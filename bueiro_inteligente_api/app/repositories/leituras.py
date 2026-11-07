from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import JANELA_LIMPEZA_MINUTOS


class LeituraRepository:
    """Encapsula consultas e persistência do fluxo de leituras."""

    def __init__(self, session: Session) -> None:
        """Associa a sessão usada nas consultas e gravações."""
        self.session = session

    def rollback(self) -> None:
        """Reverte a transação atual."""
        self.session.rollback()

    def criar_leitura(
        self,
        leitura: schemas.LeituraSensorCreate,
    ) -> tuple[models.LeituraSensor, bool]:
        """Persiste uma leitura e ignora reenvios com timestamp já registrado."""
        timestamp = leitura.data_hora
        if timestamp is not None and timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

        if timestamp is not None:
            existente = (
                self.session.query(models.LeituraSensor)
                .filter(
                    models.LeituraSensor.id_sensor == leitura.id_sensor,
                    models.LeituraSensor.timestamp_dispositivo == timestamp,
                )
                .first()
            )
            if existente is not None:
                return existente, False

        valores_leitura = {
            "valor_leitura": leitura.valor_leitura,
            "unidade_medida": leitura.unidade_medida,
            "id_sensor": leitura.id_sensor,
        }
        if timestamp is not None:
            valores_leitura["data_hora"] = timestamp
            valores_leitura["timestamp_dispositivo"] = timestamp

        registro = models.LeituraSensor(
            **valores_leitura,
        )
        try:
            self.session.add(registro)
            self.session.commit()
            self.session.refresh(registro)
        except IntegrityError:
            self.session.rollback()
            if timestamp is not None:
                existente = (
                    self.session.query(models.LeituraSensor)
                    .filter(
                        models.LeituraSensor.id_sensor == leitura.id_sensor,
                        models.LeituraSensor.timestamp_dispositivo == timestamp,
                    )
                    .first()
                )
                if existente is not None:
                    return existente, False
            raise
        except Exception:
            self.session.rollback()
            raise
        return registro, True

    def existe_limpeza_recente(
        self,
        agora: datetime,
        janela_minutos: int = JANELA_LIMPEZA_MINUTOS,
    ) -> bool:
        """Verifica se houve limpeza dentro da janela configurada."""
        limite = agora - timedelta(minutes=janela_minutos)
        return (
            self.session.query(models.Limpeza)
            .filter(models.Limpeza.data_hora >= limite)
            .first()
            is not None
        )

    def registrar_limpeza_automatica(self, risco: str) -> models.Limpeza:
        """Registra a limpeza automática associada ao risco."""
        limpeza = models.Limpeza(status_limpeza=f"Auto ({risco})"[:20])
        try:
            self.session.add(limpeza)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return limpeza

    def listar_leituras(self) -> list[models.LeituraSensor]:
        """Lista leituras da mais recente para a mais antiga."""
        return (
            self.session.query(models.LeituraSensor)
            .order_by(models.LeituraSensor.data_hora.desc())
            .all()
        )

    def listar_previsoes_das_leituras(
        self,
        ids_leituras: list[int],
    ) -> list[models.PrevisaoEntupimento]:
        """Busca previsões relacionadas às leituras indicadas."""
        return (
            self.session.query(models.PrevisaoEntupimento)
            .filter(models.PrevisaoEntupimento.id_leitura.in_(ids_leituras))
            .order_by(
                models.PrevisaoEntupimento.data_hora.desc(),
                models.PrevisaoEntupimento.id_previsao.desc(),
            )
            .all()
        )
