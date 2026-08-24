from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..ai_predictor import PrevisorEntupimentoIA
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
