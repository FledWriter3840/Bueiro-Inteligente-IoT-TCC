from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..database import get_db
from ..repositories.leituras import LeituraRepository
from ..services.leituras import LeituraService

router = APIRouter(
    prefix="/sensores",
    tags=["Sensores"]
)

@router.post("/leitura", response_model=schemas.LeituraSensorOut)
def registrar_leitura(
    leitura: schemas.LeituraSensorCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """
    Registra uma nova leitura de sensor no banco de dados e executa a IA preditiva.
    """
    service = LeituraService(LeituraRepository(db))
    return service.registrar_leitura(leitura)

@router.get("/leituras", response_model=list[schemas.LeituraSensorOut])
def listar_leituras(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    """
    Lista todas as leituras de sensores registradas no banco de dados.
    """
    service = LeituraService(LeituraRepository(db))
    return service.listar_leituras()