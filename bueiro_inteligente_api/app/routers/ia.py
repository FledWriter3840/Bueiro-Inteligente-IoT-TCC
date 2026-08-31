from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..ai_predictor import PrevisorEntupimentoIA
from ..ml.predictor import PrevisorEntupimentoML
from ..ml.train import treinar_modelo as treinar_modelo_ml_fn
from ..weather_service import obter_dados_climaticos_dict
from ..dados_externos import historico_alagamentos, dados_geograficos, uso_do_solo
from ..config import BUEIRO_LATITUDE, BUEIRO_LONGITUDE
from datetime import datetime

router = APIRouter(
    prefix="/ia",
    tags=["Inteligência Artificial & Previsão"]
)

@router.get("/previsao", response_model=schemas.AnaliseIAResult)
def obter_previsao_atual(id_sensor: int = 1, db: Session = Depends(get_db)):
    """
    Executa o motor de IA multivariado sobre as leituras recentes do sensor
    e todas as fontes de dados disponíveis (clima, temporal, geográfico, etc.).
    Retorna o diagnóstico de risco de alagamento e recomendação de limpeza.
    (Atende ao requisito RF15 / UC09).
    """
    return PrevisorEntupimentoIA.analisar_e_prever(db=db, id_sensor=id_sensor, persistir=True)

@router.get("/historico-previsoes", response_model=list[schemas.PrevisaoEntupimentoOut])
def listar_historico_previsoes(db: Session = Depends(get_db)):
    """
    Retorna o histórico das previsões de entupimento geradas pela IA e armazenadas no MySQL.
    """
    return db.query(models.PrevisaoEntupimento)\
             .order_by(models.PrevisaoEntupimento.data_hora.desc())\
             .limit(50)\
             .all()

@router.post("/simular-cenario")
def simular_cenario_chuva(cenario: schemas.CenarioSimulacaoRequest):
    """
    Simula uma projeção matemática/IA de elevação de água em caso de chuva intensa,
    útil para demonstração visual na banca de TCC.
    """
    projecoes = []
    distancia = cenario.distancia_inicial_cm
    taxa = cenario.velocidade_subida_cm_min

    for minuto in range(0, cenario.minutos_simulacao + 1):
        distancia_min = max(0.0, distancia - (taxa * minuto))
        
        # Avalia risco instantâneo
        if distancia_min <= 15.0:
            prob = 0.95
            risco = "Crítico"
        elif distancia_min <= 50.0:
            prob = 0.75
            risco = "Alto"
        elif distancia_min <= 150.0:
            prob = 0.45
            risco = "Médio"
        else:
            prob = 0.15
            risco = "Baixo"

        projecoes.append({
            "minuto": minuto,
            "distancia_prevista_cm": round(distancia_min, 1),
            "probabilidade_alagamento": prob,
            "nivel_risco": risco
        })

    return {
        "cenario": {
            "distancia_inicial_cm": cenario.distancia_inicial_cm,
            "velocidade_subida_cm_min": cenario.velocidade_subida_cm_min,
            "tempo_total_simulado_min": cenario.minutos_simulacao
        },
        "projecoes": projecoes
    }


@router.get("/previsao-ml", response_model=schemas.AnaliseIAMLResult)
def obter_previsao_ml(id_sensor: int = 1, persistir: bool = False, db: Session = Depends(get_db)):
    """
    Previsão via Machine Learning (scikit-learn, DecisionTreeClassifier),
    treinado sobre dataset sintético — complementar ao /ia/previsao
    (motor de regressão/tendência temporal).
    """
    return PrevisorEntupimentoML.prever(db=db, id_sensor=id_sensor, persistir=persistir)

@router.post("/treinar-modelo-ml", response_model=schemas.TreinoMLResult)
def treinar_modelo_ml(n_amostras: int = 3000):
    """
    Re-treina o modelo de ML sobre um novo dataset sintético. Útil para
    demonstrar o pipeline de treino/avaliação na banca de TCC.
    """
    return treinar_modelo_ml_fn(n_amostras=n_amostras)

@router.get("/comparativo", response_model=schemas.ComparativoIAResult)
def comparar_motores_ia(id_sensor: int = 1, persistir: bool = False, db: Session = Depends(get_db)):
    """
    Executa os dois motores de previsão (regressão/tendência temporal e
    Machine Learning via scikit-learn) sobre as mesmas leituras recentes
    e retorna os dois resultados lado a lado, com um veredito de
    convergência entre eles. Pensado para demonstração na banca de TCC.
    """
    resultado_regressao = PrevisorEntupimentoIA.analisar_e_prever(
        db=db, id_sensor=id_sensor, persistir=persistir
    )
    resultado_ml = PrevisorEntupimentoML.prever(
        db=db, id_sensor=id_sensor, persistir=False
    )

    convergencia = resultado_regressao.nivel_risco == resultado_ml.nivel_risco

    if convergencia:
        observacao = (
            f"Os dois motores concordam: risco '{resultado_regressao.nivel_risco}'. "
            "Isso reforça a confiabilidade do diagnóstico."
        )
    else:
        observacao = (
            f"Divergência entre os motores: regressão indica '{resultado_regressao.nivel_risco}', "
            f"Machine Learning indica '{resultado_ml.nivel_risco}'. "
            "Recomenda-se monitoramento contínuo até a próxima leitura confirmar a tendência."
        )

    return schemas.ComparativoIAResult(
        motor_regressao=resultado_regressao,
        motor_machine_learning=resultado_ml,
        convergencia=convergencia,
        observacao=observacao
    )


# ═══════════════════════════════════════════════════════════════════
# NOVOS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/clima-atual")
def obter_clima_atual():
    """
    Consulta os dados climáticos atuais via OpenWeatherMap.
    Retorna precipitação, umidade, vento, previsão de chuva e descrição.
    Requer OPENWEATHER_API_KEY configurada no .env.
    """
    return obter_dados_climaticos_dict(
        lat=BUEIRO_LATITUDE,
        lon=BUEIRO_LONGITUDE,
    )


@router.get("/fontes-dados")
def listar_fontes_dados():
    """
    Lista quais fontes de dados estão ativas/carregadas no sistema.
    Útil para diagnóstico e verificação da configuração.
    """
    return {
        "fontes": [
            {
                "nome": "Sensor IoT (Telemetria)",
                "status": "Ativo",
                "descricao": "Dados do sensor ultrassônico e compactação via banco de dados MySQL.",
            },
            {
                "nome": "OpenWeatherMap (Clima)",
                "status": "Ativo" if obter_dados_climaticos_dict().get("disponivel") else "Indisponível (configurar OPENWEATHER_API_KEY)",
                "descricao": "Dados climáticos em tempo real: chuva, umidade, vento, previsão.",
            },
            {
                "nome": "Dados Temporais (datetime)",
                "status": "Ativo",
                "descricao": "Features derivadas do horário: estação do ano, horário de pico, feriados SP.",
            },
            {
                "nome": "Histórico de Alagamentos (CGE SP)",
                "status": "Ativo" if historico_alagamentos.disponivel else "Esqueleto (aguardando dataset)",
                "descricao": "Pontos recorrentes de alagamento e manchas de inundação.",
            },
            {
                "nome": "Dados Geográficos (GeoSampa)",
                "status": "Ativo" if dados_geograficos.disponivel else "Esqueleto (aguardando dataset)",
                "descricao": "Altitude relativa, fundo de vale, classificação de áreas de risco.",
            },
            {
                "nome": "Uso do Solo (Entorno)",
                "status": "Ativo" if uso_do_solo.disponivel else "Esqueleto (aguardando dataset)",
                "descricao": "Tipo de via, proximidade com feiras/parques, impermeabilização.",
            },
        ],
        "total_ativas": sum([
            True,  # Sensor sempre ativo
            obter_dados_climaticos_dict().get("disponivel", False),
            True,  # Temporal sempre ativo
            historico_alagamentos.disponivel,
            dados_geograficos.disponivel,
            uso_do_solo.disponivel,
        ]),
        "total_fontes": 6,
    }