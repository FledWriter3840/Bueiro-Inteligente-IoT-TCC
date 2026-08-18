from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/compactacao",
    tags=["Compactacao"])

@router.post("/", response_model=schemas.CompactacaoOut)
def registrar_compactacao(compactacao: schemas.CompactacaoCreate, db: Session = Depends(get_db)):
    nova_compactacao = models.Compactacao(
        nivel_residuo = compactacao.nivel_residuo
    )
    db.add(nova_compactacao)
    db.commit()
    db.refresh(nova_compactacao)
    return nova_compactacao

@router.get("/", response_model=list[schemas.CompactacaoOut])
def listar_compacacoes(db: Session = Depends(get_db)):
    return db.query(models.Compactacao).order_by(models.Compactacao.data_hora.desc()).all()