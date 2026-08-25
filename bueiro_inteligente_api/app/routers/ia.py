from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..ai_predictor import PrevisorEntupimentoIA
from ..ml.predictor import PrevisorEntupimentoML
from ..ml.train import treinar_modelo as treinar_modelo_ml_fn
from datetime import datetime

router = APIRouter(
    prefix="/ia",
    tags=["Inteligência Artificial & Previsão"]
)

@router.get("/previsao", response_model=schemas.AnaliseIAResult)
def obter_previsao_atual(id_sensor: int = 1, db: Session = Depends(get_db)):
    """
    Executa o modelo de Machine Learning / Tendência Temporal sobre as leituras
    recentes do sensor no banco de dados e retorna o diagnóstico de risco de alagamento.
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