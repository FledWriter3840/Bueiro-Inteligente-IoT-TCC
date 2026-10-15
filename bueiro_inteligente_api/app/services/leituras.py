import logging
from datetime import datetime, timezone

from .. import models, schemas
from ..config import PRIORIDADE_NIVEL_RISCO, TEMPOS_LIMPEZA_POR_RISCO
from ..enums import NivelRisco
from ..ml.predictor import PrevisorEntupimentoML
from ..ai_predictor import PrevisorEntupimentoIA
from ..repositories.leituras import LeituraRepository

logger = logging.getLogger(__name__)


def combinar_riscos(risco_multivariado: str, risco_ml: str) -> str:
    """Retorna o risco de maior prioridade entre os dois motores."""
    return max(
        (risco_multivariado, risco_ml),
        key=lambda risco: PRIORIDADE_NIVEL_RISCO.get(risco, 0),
    )


def decidir_acionamento(
    nivel_risco: str,
    limpeza_recente: bool,
) -> tuple[bool, int]:
    """Calcula o acionamento e a duração respeitando a janela de limpeza."""
    duracao = TEMPOS_LIMPEZA_POR_RISCO.get(nivel_risco, 0)
    deve_acionar = bool(duracao and not limpeza_recente)
    return deve_acionar, duracao if deve_acionar else 0


def montar_resposta_leitura(
    leitura: models.LeituraSensor,
    risco_multivariado: str,
    risco_ml: str,
    nivel_risco: str,
    acionar_limpeza: bool,
    tempo_limpeza_segundos: int,
    recomendacao_limpeza: str,
) -> dict:
    """Monta o payload existente retornado ao firmware."""
    return {
        "id_sensor": leitura.id_sensor,
        "valor_leitura": leitura.valor_leitura,
        "unidade_medida": leitura.unidade_medida,
        "id_leitura": leitura.id_leitura,
        "data_hora": leitura.data_hora,
        "acionar_limpeza": acionar_limpeza,
        "tempo_limpeza_segundos": tempo_limpeza_segundos,
        "motivo_limpeza": (
            f"Decisão conjunta: multivariada={risco_multivariado}; ML={risco_ml}. "
            f"{recomendacao_limpeza}"
        ),
        "nivel_risco": nivel_risco,
        "nivel_risco_multivariado": risco_multivariado,
        "nivel_risco_ml": risco_ml,
    }


class LeituraService:
    """Orquestra registro, predição e resposta de uma leitura do sensor."""

    def __init__(self, repository: LeituraRepository):
        self.repository = repository

    def registrar_leitura(
        self,
        leitura: schemas.LeituraSensorCreate,
    ) -> dict:
        """Persiste uma leitura e produz a decisão de limpeza."""
        registro = self.repository.criar_leitura(leitura)
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        limpeza_recente = self.repository.existe_limpeza_recente(agora)
        try:
            resultado_ia = PrevisorEntupimentoIA.analisar_e_prever(
                db=self.repository.session,
                id_sensor=registro.id_sensor,
                persistir=True,
            )
            resultado_ml = PrevisorEntupimentoML.prever(
                db=self.repository.session,
                id_sensor=registro.id_sensor,
                persistir=False,
            )
        except Exception:
            self.repository.rollback()
            logger.exception(
                "Falha ao executar os preditores para a leitura %s",
                registro.id_leitura,
            )
            raise

        risco_multivariado = (
            resultado_ia.nivel_risco if resultado_ia else NivelRisco.BAIXO.value
        )
        risco_ml = resultado_ml.nivel_risco if resultado_ml else NivelRisco.BAIXO.value
        nivel_risco = combinar_riscos(risco_multivariado, risco_ml)

        acionar, duracao = decidir_acionamento(nivel_risco, limpeza_recente)
        if acionar:
            # O preditor multivariado pode gravar a mesma limpeza antes da
            # resposta ao ESP32; reutiliza esse registro sem suprimir o comando.
            limpeza_recente = self.repository.existe_limpeza_recente(
                datetime.now(timezone.utc).replace(tzinfo=None)
            )
            if not limpeza_recente:
                self.repository.registrar_limpeza_automatica(nivel_risco)

        return montar_resposta_leitura(
            leitura=registro,
            risco_multivariado=risco_multivariado,
            risco_ml=risco_ml,
            nivel_risco=nivel_risco,
            acionar_limpeza=acionar,
            tempo_limpeza_segundos=duracao,
            recomendacao_limpeza=(
                resultado_ia.recomendacao_limpeza if resultado_ia else ""
            ),
        )

    def listar_leituras(self) -> list[dict]:
        """Lista leituras com a previsão mais recente associada."""
        leituras = self.repository.listar_leituras()
        if not leituras:
            return []

        previsoes = self.repository.listar_previsoes_das_leituras(
            [leitura.id_leitura for leitura in leituras]
        )
        risco_por_leitura: dict[int, str] = {}
        for previsao in previsoes:
            risco_por_leitura.setdefault(previsao.id_leitura, previsao.nivel_risco)

        return [
            {
                "id_sensor": leitura.id_sensor,
                "valor_leitura": leitura.valor_leitura,
                "unidade_medida": leitura.unidade_medida,
                "id_leitura": leitura.id_leitura,
                "data_hora": leitura.data_hora,
                "nivel_risco": risco_por_leitura.get(leitura.id_leitura),
            }
            for leitura in leituras
        ]
