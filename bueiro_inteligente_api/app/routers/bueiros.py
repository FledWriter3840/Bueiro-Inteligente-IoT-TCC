from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models
from .. import schemas
from ..ai_predictor import PrevisorEntupimentoIA
from ..config import BUEIRO_LATITUDE, BUEIRO_LONGITUDE
from ..database import get_db
from ..repositories.bueiros import BueiroJsonRepository, BueiroStorageError
from ..repositories.inventario_bueiros import InventarioBueirosRepository
from ..services.bueiros import BueiroService
from ..services.catalogo_bueiros import CatalogoBueirosService
from ..services.monitoramento import (
    calcular_nivel_percentual,
    calcular_status_bueiro,
)

router = APIRouter(prefix="/bueiros", tags=["Bueiros"])
DATASETS_DIR = Path(__file__).resolve().parents[2] / "datasets"
CSV_PATH = DATASETS_DIR / "bueiros.csv"
SAC_CSV_PATH = DATASETS_DIR / "sac_limpeza_bueiro.csv"
ADICOES_PATH = DATASETS_DIR / "bueiros_adicionados.json"


def get_bueiro_service() -> BueiroService:
    """Cria o serviço de cadastro de bueiros."""
    return BueiroService(BueiroJsonRepository(ADICOES_PATH))


def get_catalogo_service() -> CatalogoBueirosService:
    """Cria o serviço de consulta ao inventário e aos dados SAC."""
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
) -> dict[str, object]:
    """Persiste um bueiro novo sem alterar o CSV de inventário original."""
    try:
        return service.cadastrar(novo_bueiro)
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.get("/cadastrados", response_model=list[schemas.BueiroOut])
def listar_bueiros_cadastrados(
    service: BueiroService = Depends(get_bueiro_service),
) -> list[dict]:
    """Lista somente os pontos cadastrados manualmente."""
    try:
        return service.listar_adicionados()
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.delete("/cadastrados/{identificador}")
def remover_bueiro_cadastrado(
    identificador: str,
    service: BueiroService = Depends(get_bueiro_service),
) -> dict[str, str]:
    """Remove somente pontos cadastrados manualmente."""
    try:
        removido = service.remover(identificador)
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc
    if not removido:
        raise HTTPException(status_code=404, detail="Ponto cadastrado não encontrado.")
    return {"mensagem": "Ponto cadastrado removido."}


@router.get("/rodovias", response_model=list[str])
def listar_rodovias(
    service: CatalogoBueirosService = Depends(get_catalogo_service),
) -> list[str]:
    """Lista as rodovias disponíveis no inventário."""
    try:
        return service.listar_rodovias()
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.get("/", response_model=list[schemas.BueiroOut])
def listar_bueiros(
    rodovia: str | None = Query(default=None),
    service: CatalogoBueirosService = Depends(get_catalogo_service),
) -> list[dict[str, object]]:
    """Lista os bueiros do inventário, opcionalmente filtrados por rodovia."""
    try:
        return service.listar_bueiros(rodovia)
    except BueiroStorageError as exc:
        raise _erro_armazenamento(exc) from exc


@router.get("/locais-sac", response_model=list[schemas.LocalSACOut])
def listar_locais_sac(
    service: CatalogoBueirosService = Depends(get_catalogo_service),
) -> list[dict[str, object]]:
    """Lista locais únicos com solicitações SAC."""
    return service.listar_locais_sac()


@router.get("/solicitacoes-limpeza", response_model=schemas.SolicitacoesProximasOut)
def listar_solicitacoes_limpeza_proximas(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    raio_m: int = Query(default=500, ge=100, le=5000),
    limite: int = Query(default=1000, ge=1, le=5000),
    service: CatalogoBueirosService = Depends(get_catalogo_service),
) -> dict[str, object]:
    """Busca solicitações SAC próximas à localização informada."""
    return service.listar_solicitacoes_proximas(lat, lon, raio_m, limite)


def _serializar_bueiro_monitorado(
    sensor: models.Sensor,
    leitura: models.LeituraSensor | None,
) -> dict[str, object]:
    if sensor.latitude is None or sensor.longitude is None:
        raise HTTPException(
            status_code=503,
            detail="Coordenadas ausentes. Execute a migração de localização.",
        )

    nivel = (
        calcular_nivel_percentual(leitura.valor_leitura, leitura.unidade_medida)
        if leitura is not None
        else 0.0
    )
    return {
        "id": sensor.id_sensor,
        "nome": f"Bueiro {sensor.id_sensor}",
        "latitude": float(sensor.latitude),
        "longitude": float(sensor.longitude),
        "nivel": nivel,
        "status": calcular_status_bueiro(nivel),
        "ultima_leitura": leitura.data_hora if leitura is not None else None,
    }


@router.get(
    "",
    response_model=list[schemas.BueiroMonitoramentoOut],
    summary="Lista bueiros monitorados",
    description=(
        "Retorna sensores cadastrados no MySQL com coordenadas, nível percentual "
        "indicativo, status atual e horário da leitura mais recente."
    ),
)
def listar_bueiros_monitorados(
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    sensores = db.query(models.Sensor).order_by(models.Sensor.id_sensor).all()
    resposta = []
    for sensor in sensores:
        leitura = (
            db.query(models.LeituraSensor)
            .filter(models.LeituraSensor.id_sensor == sensor.id_sensor)
            .order_by(
                models.LeituraSensor.data_hora.desc(),
                models.LeituraSensor.id_leitura.desc(),
            )
            .first()
        )
        resposta.append(_serializar_bueiro_monitorado(sensor, leitura))
    return resposta


@router.get(
    "/{id_sensor}",
    response_model=schemas.BueiroDetalheOut,
    summary="Detalha um bueiro monitorado",
    description="Inclui as 20 leituras mais recentes e a URL da foto mais nova.",
)
def obter_bueiro_monitorado(
    id_sensor: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    sensor = db.get(models.Sensor, id_sensor)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Bueiro não encontrado.")

    leituras = (
        db.query(models.LeituraSensor)
        .filter(models.LeituraSensor.id_sensor == id_sensor)
        .order_by(
            models.LeituraSensor.data_hora.desc(),
            models.LeituraSensor.id_leitura.desc(),
        )
        .limit(20)
        .all()
    )
    leitura_atual = leituras[0] if leituras else None
    bueiro = _serializar_bueiro_monitorado(sensor, leitura_atual)

    imagem = (
        db.query(models.RegistroImagem)
        .join(
            models.LeituraSensor,
            models.RegistroImagem.id_leitura == models.LeituraSensor.id_leitura,
        )
        .filter(models.LeituraSensor.id_sensor == id_sensor)
        .order_by(
            models.RegistroImagem.data_hora.desc(),
            models.RegistroImagem.id_imagem.desc(),
        )
        .first()
    )
    bueiro["historico"] = leituras
    bueiro["foto_url"] = f"/camera/imagens/{imagem.id_imagem}" if imagem else None
    return bueiro


@router.get(
    "/{id_sensor}/previsao",
    response_model=schemas.PrevisaoBueiroOut,
    summary="Prevê o risco do bueiro",
    description="Consulta o motor multivariado de IA já utilizado pela API.",
)
def prever_risco_bueiro(
    id_sensor: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    sensor = db.get(models.Sensor, id_sensor)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Bueiro não encontrado.")

    resultado = PrevisorEntupimentoIA.analisar_e_prever(
        db=db,
        id_sensor=id_sensor,
        persistir=False,
        lat=float(sensor.latitude or BUEIRO_LATITUDE),
        lon=float(sensor.longitude or BUEIRO_LONGITUDE),
    )
    nivel = resultado.nivel_risco.casefold()
    risco = (
        "alto"
        if "alto" in nivel or "crítico" in nivel or "critico" in nivel
        else "moderado"
        if "médio" in nivel or "medio" in nivel
        else "baixo"
    )
    minutos = resultado.tempo_estimado_transbordo_min
    return {
        "risco": risco,
        "horas_estimadas": round(minutos / 60) if minutos is not None else None,
        "recomendacao": resultado.recomendacao,
    }
