from fastapi import APIRouter, Depends
from .. import models, schemas
from ..dependencies import get_alerta_service
from ..services.records import RecordService

router = APIRouter(
    prefix="/alertas",
    tags=["Alertas"])

@router.post("/", response_model=schemas.AlertaOut, status_code=201)
def registrar_alerta(
    alerta: schemas.AlertaCreate,
    service: RecordService[models.Alerta] = Depends(get_alerta_service),
):
    return service.create(alerta)

@router.get("/", response_model=list[schemas.AlertaOut])
def listar_alertas(
    service: RecordService[models.Alerta] = Depends(get_alerta_service),
):
    return service.list_recent()