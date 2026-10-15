from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas
from ..database import get_db
from ..repositories.previsoes import PrevisaoRepository
from ..ai_predictor import PrevisorEntupimentoIA
from ..ml.predictor import PrevisorEntupimentoML
from ..ml.train import treinar_modelo as treinar_modelo_ml_fn
from ..weather_service import obter_dados_climaticos_dict
from ..config import (
    BUEIRO_LATITUDE,
    BUEIRO_LONGITUDE,
    ML_N_AMOSTRAS,
)
from ..services.ia import (
    comparar_motores_ia as comparar_motores_ia_service,
    listar_fontes_dados as listar_fontes_dados_service,
    obter_topografia_atual as obter_topografia_atual_service,
    simular_cenario_chuva as simular_cenario_chuva_service,
)

router = APIRouter(
    prefix="/ia",
    tags=["Inteligência Artificial & Previsão"]
)

@router.get("/previsao", response_model=schemas.AnaliseIAResult)
def obter_previsao_atual(
    id_sensor: int = 1,
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
    db: Session = Depends(get_db),
):
    """
    Executa o motor de IA multivariado sobre as leituras recentes do sensor
    e todas as fontes de dados disponíveis (clima, temporal, geográfico, etc.).
    Retorna o diagnóstico de risco de alagamento e recomendação de limpeza.
    (Atende ao requisito RF15 / UC09).
    """
    return PrevisorEntupimentoIA.analisar_e_prever(
        db=db, id_sensor=id_sensor, persistir=True, lat=lat, lon=lon,
    )

@router.get("/historico-previsoes", response_model=list[schemas.PrevisaoEntupimentoOut])
def listar_historico_previsoes(db: Session = Depends(get_db)):
    """
    Retorna o histórico das previsões de entupimento geradas pela IA e armazenadas no MySQL.
    """
    return PrevisaoRepository(db).listar_historico()

@router.post("/simular-cenario")
def simular_cenario_chuva(cenario: schemas.CenarioSimulacaoRequest):
    """
    Simula uma projeção matemática/IA de elevação de água em caso de chuva intensa,
    útil para demonstração visual na banca de TCC.
    """
    return simular_cenario_chuva_service(cenario)


@router.get("/previsao-ml", response_model=schemas.AnaliseIAMLResult)
def obter_previsao_ml(
    id_sensor: int = 1,
    persistir: bool = False,
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
    db: Session = Depends(get_db),
):
    """
    Previsão via Machine Learning (scikit-learn, DecisionTreeClassifier),
    treinado sobre dataset sintético — complementar ao /ia/previsao
    (motor de regressão/tendência temporal).
    """
    return PrevisorEntupimentoML.prever(db=db, id_sensor=id_sensor, persistir=persistir)

@router.post("/treinar-modelo-ml", response_model=schemas.TreinoMLResult)
def treinar_modelo_ml(n_amostras: int = ML_N_AMOSTRAS):
    """
    Re-treina o modelo de ML sobre um novo dataset sintético. Útil para
    demonstrar o pipeline de treino/avaliação na banca de TCC.
    """
    return treinar_modelo_ml_fn(n_amostras=n_amostras)

@router.get("/comparativo", response_model=schemas.ComparativoIAResult)
def comparar_motores_ia(
    id_sensor: int = 1,
    persistir: bool = False,
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
    db: Session = Depends(get_db),
):
    """
    Executa os dois motores de previsão (regressão/tendência temporal e
    Machine Learning via scikit-learn) sobre as mesmas leituras recentes
    e retorna os dois resultados lado a lado, com um veredito de
    convergência entre eles. Pensado para demonstração na banca de TCC.
    """
    return comparar_motores_ia_service(
        db=db,
        id_sensor=id_sensor,
        persistir=persistir,
        lat=lat,
        lon=lon,
    )


# ═══════════════════════════════════════════════════════════════════
# NOVOS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/clima-atual")
def obter_clima_atual(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
):
    """
    Consulta os dados climáticos atuais via OpenWeatherMap.
    Retorna precipitação, umidade, vento, previsão de chuva e descrição.
    Requer OPENWEATHER_API_KEY configurada no .env.
    """
    return obter_dados_climaticos_dict(
        lat=lat,
        lon=lon,
    )


@router.get("/topografia-atual")
def obter_topografia_atual(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
):
    """
    Consulta os dados topográficos atuais via OpenTopography (Copernicus DEM GLO-30)
    ou provider local configurado. Retorna altitude, declividade, classificação de risco
    e detecção de fundo de vale.
    """
    return obter_topografia_atual_service(lat, lon)


@router.get("/fontes-dados")
def listar_fontes_dados():
    """
    Lista quais fontes de dados estão ativas/carregadas no sistema.
    Útil para diagnóstico e verificação da configuração.
    """
    return listar_fontes_dados_service()