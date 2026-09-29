from fastapi import Depends
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .repositories.records import SQLAlchemyRecordRepository
from .services.records import RecordService


def get_alerta_service(
    db: Session = Depends(get_db),
) -> RecordService[models.Alerta]:
    return RecordService(SQLAlchemyRecordRepository(db, models.Alerta))


def get_limpeza_service(
    db: Session = Depends(get_db),
) -> RecordService[models.Limpeza]:
    return RecordService(SQLAlchemyRecordRepository(db, models.Limpeza))


def get_compactacao_service(
    db: Session = Depends(get_db),
) -> RecordService[models.Compactacao]:
    return RecordService(SQLAlchemyRecordRepository(db, models.Compactacao))


def get_historico_service(
    db: Session = Depends(get_db),
) -> RecordService[models.HistoricoSistema]:
    return RecordService(SQLAlchemyRecordRepository(db, models.HistoricoSistema))