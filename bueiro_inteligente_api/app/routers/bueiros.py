from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import schemas
from ..repositories.bueiros import BueiroJsonRepository, BueiroStorageError
from ..repositories.inventario_bueiros import InventarioBueirosRepository
from ..services.bueiros import BueiroService
from ..services.catalogo_bueiros import CatalogoBueirosService

router = APIRouter(prefix="/bueiros", tags=["Bueiros"])
CSV_PATH = Path(__file__).resolve().parents[2] / "datasets_exemplo" / "bueiros.csv"
SAC_CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "datasets_exemplo"
    / "sac_limpeza_bueiro.csv"
)
ADICOES_PATH = (
    Path(__file__).resolve().parents[2]
    / "datasets_exemplo"
    / "bueiros_adicionados.json"
)


def get_bueiro_service() -> BueiroService:
    return BueiroService(BueiroJsonRepository(ADICOES_PATH))


def get_catalogo_service() -> CatalogoBueirosService:
    return CatalogoBueirosService(
        repository=InventarioBueirosRepository(CSV_PATH, SAC_CSV_PATH),
        bueiro_service=get_bueiro_service(),
    )


def _erro_armazenamento(exc: BueiroStorageError) -> HTTPException:
    return HTTPException(status_code=500, detail=str(exc))


@router.post("/", status_code=201, response_model=schemas.BueiroOut)
def cadastrar_bueiro(
    novo_bueiro: schemas.BueiroCreate,
    service: BueiroService = Depends(get_bueiro_service),
):
    """Persiste um bueiro novo sem alterar o CSV de inventário original."""
    try:
        return service.cadastrar(novo_bueiro)
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.get("/rodovias", response_model=list[str])
def listar_rodovias(
    service: CatalogoBueirosService = Depends(get_catalogo_service),
):
    """Lista as rodovias disponíveis no inventário."""
    try:
        return service.listar_rodovias()
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.get("/", response_model=list[schemas.BueiroOut])
def listar_bueiros(
    rodovia: str | None = Query(default=None),
    service: CatalogoBueirosService = Depends(get_catalogo_service),
):
    """Lista os bueiros do inventário, opcionalmente filtrados por rodovia."""
    try:
        return service.listar_bueiros(rodovia)
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.get("/locais-sac", response_model=list[schemas.LocalSACOut])
def listar_locais_sac(
    service: CatalogoBueirosService = Depends(get_catalogo_service),
):
    """Lista locais únicos com solicitações SAC."""
    return service.listar_locais_sac()


@router.get("/solicitacoes-limpeza", response_model=schemas.SolicitacoesProximasOut)
def listar_solicitacoes_limpeza_proximas(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    raio_m: int = Query(default=500, ge=100, le=5000),
    limite: int = Query(default=1000, ge=1, le=5000),
    service: CatalogoBueirosService = Depends(get_catalogo_service),
):
    """Busca solicitações SAC próximas à localização informada."""
    return service.listar_solicitacoes_proximas(lat, lon, raio_m, limite)
