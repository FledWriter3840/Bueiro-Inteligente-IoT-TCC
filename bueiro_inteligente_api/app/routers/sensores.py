from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config import (
    JANELA_LIMPEZA_MINUTOS,
    PRIORIDADE_NIVEL_RISCO,
    TEMPOS_LIMPEZA_POR_RISCO,
)
from ..database import get_db
from ..enums import NivelRisco

from ..ai_predictor import PrevisorEntupimentoIA
from ..ml.predictor import PrevisorEntupimentoML

router = APIRouter(
    prefix="/sensores",
    tags=["Sensores"]
)

@router.post("/leitura", response_model=schemas.LeituraSensorOut)
def registrar_leitura(leitura: schemas.LeituraSensorCreate, db: Session = Depends(get_db)):
    """
    Registra uma nova leitura de sensor no banco de dados e executa a IA preditiva.
    """
    nova_leitura = models.LeituraSensor(
        valor_leitura = leitura.valor_leitura,
        unidade_medida = leitura.unidade_medida,
        id_sensor = leitura.id_sensor
    )
    db.add(nova_leitura)
    db.commit()
    db.refresh(nova_leitura)

    # Executa a IA preditiva para avaliar risco de transbordo e gravar na tabela previsaoentupimento
    resultado_ia = None
    resultado_ml = None
    limpeza_recente = db.query(models.Limpeza).filter(
        models.Limpeza.data_hora
        >= datetime.utcnow() - timedelta(minutes=JANELA_LIMPEZA_MINUTOS)
    ).first()
    try:
        resultado_ia = PrevisorEntupimentoIA.analisar_e_prever(
            db=db,
            id_sensor=nova_leitura.id_sensor,
            persistir=True,
        )
        resultado_ml = PrevisorEntupimentoML.prever(
            db=db,
            id_sensor=nova_leitura.id_sensor,
            persistir=False,
        )
    except Exception as e:
        print(f"Aviso: Falha ao executar preditor de IA: {e}")

    risco_multivariado = (
        resultado_ia.nivel_risco if resultado_ia else NivelRisco.BAIXO.value
    )
    risco_ml = resultado_ml.nivel_risco if resultado_ml else NivelRisco.BAIXO.value
    nivel_risco_decisao = max(
        (risco_multivariado, risco_ml),
        key=lambda risco: PRIORIDADE_NIVEL_RISCO.get(risco, 0),
    )

    tempo_limpeza = TEMPOS_LIMPEZA_POR_RISCO.get(nivel_risco_decisao, 0)
    deve_acionar = bool(tempo_limpeza and not limpeza_recente)

    if deve_acionar:
        status = f"Auto ({nivel_risco_decisao})"
        db.add(models.Limpeza(status_limpeza=status[:20]))
        db.commit()

    return {
        "id_sensor": nova_leitura.id_sensor,
        "valor_leitura": nova_leitura.valor_leitura,
        "unidade_medida": nova_leitura.unidade_medida,
        "id_leitura": nova_leitura.id_leitura,
        "data_hora": nova_leitura.data_hora,
        "acionar_limpeza": deve_acionar,
        "tempo_limpeza_segundos": tempo_limpeza if deve_acionar else 0,
        "motivo_limpeza": (
            f"Decisão conjunta: multivariada={risco_multivariado}; ML={risco_ml}. "
            f"{resultado_ia.recomendacao_limpeza if resultado_ia else ''}"
        ),
        "nivel_risco": nivel_risco_decisao,
        "nivel_risco_multivariado": risco_multivariado,
        "nivel_risco_ml": risco_ml,
    }

@router.get("/leituras", response_model=list[schemas.LeituraSensorOut])
def listar_leituras(db: Session = Depends(get_db)):
    """
    Lista todas as leituras de sensores registradas no banco de dados.
    """
    leituras = db.query(models.LeituraSensor)\
                  .order_by(models.LeituraSensor.data_hora.desc())\
                  .all()
    if not leituras:
        return []

    ids_leituras = [leitura.id_leitura for leitura in leituras]
    previsoes = db.query(models.PrevisaoEntupimento)\
                  .filter(models.PrevisaoEntupimento.id_leitura.in_(ids_leituras))\
                  .order_by(
                      models.PrevisaoEntupimento.data_hora.desc(),
                      models.PrevisaoEntupimento.id_previsao.desc(),
                  )\
                  .all()
    risco_por_leitura: dict[int, str] = {}
    for previsao in previsoes:
        risco_por_leitura.setdefault(previsao.id_leitura, previsao.nivel_risco)

    return [
        {
            "id_sensor": leitura.id_sensor,
            "valor_leitura": leitura.valor_leitura,
            "unidade_medida": leitura.unidade_medida,
            "id_leitura": leitura.id_leitura,
            "data_hora": leitura.data_hora,
            "nivel_risco": risco_por_leitura.get(leitura.id_leitura),
        }
        for leitura in leituras
    ]