from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/alertas",
    tags=["Alertas"])

@router.post("/", response_model=schemas.AlertaOut)
def registrar_alerta(alerta: schemas.AlertaCreate, db: Session = Depends(get_db)):
    novo_alerta = models.Alerta(
        descricao=alerta.descricao,
        nivel_criticidade=alerta.nivel_criticidade,
        id_leitura=alerta.id_leitura
    )
    db.add(novo_alerta)
    db.commit()
    db.refresh(novo_alerta)
    return novo_alerta

@router.get("/", response_model=list[schemas.AlertaOut])
def listar_alertas(db: Session = Depends(get_db)):
    return db.query(models.Alerta).order_by(models.Alerta.data_hora.desc()).all()