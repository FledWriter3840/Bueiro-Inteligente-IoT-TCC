from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/historico",
    tags=["Historico"])

@router.post("/", response_model=schemas.HistoricoOut)
def registrar_historico(historico: schemas.HistoricoCreate, db: Session = Depends(get_db)):
    novo_evento = models.HistoricoSistema(
        descricao_evento = historico.descricao_evento,
        id_usuario = historico.id_usuario
    )
    db.add(novo_evento)
    db.commit()
    db.refresh(novo_evento)
    return novo_evento

@router.get("/", response_model=list[schemas.HistoricoOut])
def listar_historicos(db: Session = Depends(get_db)):
    return db.query(models.HistoricoSistema).order_by(models.HistoricoSistema.data_hora.desc()).all()