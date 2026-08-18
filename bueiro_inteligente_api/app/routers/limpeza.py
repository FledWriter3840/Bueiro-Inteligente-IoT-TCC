from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/limpeza",
    tags=["Limpeza"])

@router.post("/", response_model=schemas.LimpezaOut)
def registrar_limpeza(limpeza: schemas.LimpezaCreate, db: Session = Depends(get_db)):
    nova_limpeza = models.Limpeza(
        status_limpeza = limpeza.status_limpeza
    )
    db.add(nova_limpeza)
    db.commit()
    db.refresh(nova_limpeza)
    return nova_limpeza

@router.get("/", response_model=list[schemas.LimpezaOut])
def listar_limpezas(db: Session = Depends(get_db)):
    return db.query(models.Limpeza).order_by(models.Limpeza.data_hora.desc()).all()