from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import JANELA_LIMPEZA_MINUTOS


class LeituraRepository:
    """Encapsula consultas e persistência do fluxo de leituras."""

    def __init__(self, session: Session):
        self.session = session

    def rollback(self) -> None:
        self.session.rollback()

    def criar_leitura(self, leitura: schemas.LeituraSensorCreate) -> models.LeituraSensor:
        registro = models.LeituraSensor(
            valor_leitura=leitura.valor_leitura,
            unidade_medida=leitura.unidade_medida,
            id_sensor=leitura.id_sensor,
        )
        try:
            self.session.add(registro)
            self.session.commit()
            self.session.refresh(registro)
        except Exception:
            self.session.rollback()
            raise
        return registro

    def existe_limpeza_recente(
        self,
        agora: datetime,
        janela_minutos: int = JANELA_LIMPEZA_MINUTOS,
    ) -> bool:
        limite = agora - timedelta(minutes=janela_minutos)
        return (
            self.session.query(models.Limpeza)
            .filter(models.Limpeza.data_hora >= limite)
            .first()
            is not None
        )

    def registrar_limpeza_automatica(self, risco: str) -> models.Limpeza:
        limpeza = models.Limpeza(status_limpeza=f"Auto ({risco})"[:20])
        try:
            self.session.add(limpeza)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return limpeza

    def listar_leituras(self) -> list[models.LeituraSensor]:
        return (
            self.session.query(models.LeituraSensor)
            .order_by(models.LeituraSensor.data_hora.desc())
            .all()
        )

    def listar_previsoes_das_leituras(
        self,
        ids_leituras: list[int],
    ) -> list[models.PrevisaoEntupimento]:
        return (
            self.session.query(models.PrevisaoEntupimento)
            .filter(models.PrevisaoEntupimento.id_leitura.in_(ids_leituras))
            .order_by(
                models.PrevisaoEntupimento.data_hora.desc(),
                models.PrevisaoEntupimento.id_previsao.desc(),
            )
            .all()
        )
