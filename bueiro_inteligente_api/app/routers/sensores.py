from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/sensores",
    tags=["Sensores"]
)

@router.post("/leitura", response_model=schemas.LeituraSensorOut)

def registrar_leitura(leitura: schemas.LeituraSensorCreate, db: Session = Depends(get_db)):
    """
    Registra uma nova leitura de sensor no banco de dados.
    """
    nova_leitura = models.LeituraSensor(
        valor_leitura = leitura.valor_leitura,
        unidade_medida = leitura.unidade_medida,
        id_sensor = leitura.id_sensor
    )
    db.add(nova_leitura)
    db.commit()
    db.refresh(nova_leitura)
    return nova_leitura

@router.get("/leituras", response_model=list[schemas.LeituraSensorOut])
def listar_leituras(db: Session = Depends(get_db)):
    """
    Lista todas as leituras de sensores registradas no banco de dados.
    """
    return db.query(models.LeituraSensor).order_by(models.LeituraSensor.data_hora.desc()).all()