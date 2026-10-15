from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from .. import models


class PrevisaoRepository:
    """Centraliza consultas e gravações usadas pelos motores preditivos."""

    def __init__(self, session: Session) -> None:
        """Associa a sessão usada pelos motores preditivos."""
        self.session = session

    def leituras_recentes(
        self,
        id_sensor: int,
        limite: int = 10,
    ) -> list[models.LeituraSensor]:
        """Lista as leituras recentes de um sensor."""
        return (
            self.session.query(models.LeituraSensor)
            .filter(models.LeituraSensor.id_sensor == id_sensor)
            .order_by(models.LeituraSensor.data_hora.desc())
            .limit(limite)
            .all()
        )

    def ultima_compactacao(self) -> models.Compactacao | None:
        """Retorna a medição de compactação mais recente."""
        return (
            self.session.query(models.Compactacao)
            .order_by(models.Compactacao.data_hora.desc())
            .first()
        )

    def existe_alerta_desde(self, instante: datetime) -> bool:
        """Verifica se há alertas desde o instante informado."""
        return (
            self.session.query(models.Alerta)
            .filter(models.Alerta.data_hora >= instante)
            .first()
            is not None
        )

    def existe_limpeza_desde(self, instante: datetime) -> bool:
        """Verifica se há limpezas desde o instante informado."""
        return (
            self.session.query(models.Limpeza)
            .filter(models.Limpeza.data_hora >= instante)
            .first()
            is not None
        )

    def salvar_registros(self, registros: Iterable[object]) -> None:
        """Grava vários registros em uma única transação."""
        try:
            self.session.add_all(list(registros))
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def salvar_previsao(self, previsao: models.PrevisaoEntupimento) -> None:
        """Persiste uma previsão em uma transação própria."""
        try:
            self.session.add(previsao)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def listar_historico(self, limite: int = 50) -> list[models.PrevisaoEntupimento]:
        """Lista previsões recentes limitadas pela quantidade solicitada."""
        return (
            self.session.query(models.PrevisaoEntupimento)
            .order_by(models.PrevisaoEntupimento.data_hora.desc())
            .limit(limite)
            .all()
        )
