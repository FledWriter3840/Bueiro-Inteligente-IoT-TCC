from fastapi import APIRouter, Depends
from .. import models, schemas
from ..dependencies import get_compactacao_service
from ..services.records import RecordService

router = APIRouter(
    prefix="/compactacao",
    tags=["Compactacao"])

@router.post("/", response_model=schemas.CompactacaoOut, status_code=201)
def registrar_compactacao(
    compactacao: schemas.CompactacaoCreate,
    service: RecordService[models.Compactacao] = Depends(get_compactacao_service),
):
    return service.create(compactacao)

@router.get("/", response_model=list[schemas.CompactacaoOut])
def listar_compacacoes(
    service: RecordService[models.Compactacao] = Depends(get_compactacao_service),
):
    return service.list_recent()