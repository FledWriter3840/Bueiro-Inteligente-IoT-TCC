from fastapi import APIRouter, Depends
from .. import models, schemas
from ..dependencies import get_historico_service
from ..services.records import RecordService

router = APIRouter(
    prefix="/historico",
    tags=["Historico"])

@router.post("/", response_model=schemas.HistoricoOut, status_code=201)
def registrar_historico(
    historico: schemas.HistoricoCreate,
    service: RecordService[models.HistoricoSistema] = Depends(get_historico_service),
):
    return service.create(historico)

@router.get("/", response_model=list[schemas.HistoricoOut])
def listar_historicos(
    service: RecordService[models.HistoricoSistema] = Depends(get_historico_service),
):
    return service.list_recent()