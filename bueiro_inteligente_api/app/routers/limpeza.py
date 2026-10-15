from fastapi import APIRouter, Depends
from .. import models, schemas
from ..dependencies import get_limpeza_service
from ..services.records import RecordService

router = APIRouter(
    prefix="/limpeza",
    tags=["Limpeza"])

@router.post("/", response_model=schemas.LimpezaOut, status_code=201)
def registrar_limpeza(
    limpeza: schemas.LimpezaCreate,
    service: RecordService[models.Limpeza] = Depends(get_limpeza_service),
) -> models.Limpeza:
    """Registra uma operação de limpeza."""
    return service.create(limpeza)

@router.get("/", response_model=list[schemas.LimpezaOut])
def listar_limpezas(
    service: RecordService[models.Limpeza] = Depends(get_limpeza_service),
) -> list[models.Limpeza]:
    """Lista as operações de limpeza registradas."""
    return service.list_recent()