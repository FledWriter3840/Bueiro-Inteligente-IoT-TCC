from datetime import datetime

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from .. import models, schemas
from .train import MODELO_PATH, FEATURES, treinar_modelo


class PrevisorEntupimentoML:
    """
    Motor de previsão baseado em Machine Learning (scikit-learn),
    complementar ao motor de regressão/tendência temporal já existente
    em app/ai_predictor.py.

    Treinado sobre dataset SINTÉTICO (ver app/ml/dataset.py). Deve ser
    re-treinado com dados reais assim que o protótipo físico estiver
    operacional e gerando histórico suficiente de leituras.
    """

    _modelo = None

    @classmethod
    def _carregar_modelo(cls):
        if cls._modelo is None:
            if not MODELO_PATH.exists():
                treinar_modelo()
            cls._modelo = joblib.load(MODELO_PATH)
        return cls._modelo

    @staticmethod
    def _calcular_features(db: Session, id_sensor: int = 1):
        leituras = db.query(models.LeituraSensor)\
                     .filter(models.LeituraSensor.id_sensor == id_sensor)\
                     .order_by(models.LeituraSensor.data_hora.desc())\
                     .limit(10)\
                     .all()

        if not leituras:
            return None

        agora = datetime.utcnow()
        leitura_atual = leituras[0]
        distancia_atual = float(leitura_atual.valor_leitura)

        taxa_subida = 0.0
        if len(leituras) >= 2:
            leituras_cron = list(reversed(leituras))
            t0 = leituras_cron[0].data_hora or agora
            delta_t = ((leituras_cron[-1].data_hora or agora) - t0).total_seconds() / 60.0
            delta_d = leituras_cron[-1].valor_leitura - leituras_cron[0].valor_leitura
            if delta_t > 0.01:
                taxa_subida = -(delta_d / delta_t)

        ultimas_3 = leituras[:3]
        media_movel_3 = sum(float(l.valor_leitura) for l in ultimas_3) / len(ultimas_3)

        return {
            "distancia_atual_cm": distancia_atual,
            "taxa_subida_cm_min": taxa_subida,
            "media_movel_3_cm": media_movel_3,
            "id_leitura": leitura_atual.id_leitura,
        }

    @classmethod
    def prever(cls, db: Session, id_sensor: int = 1, persistir: bool = False) -> schemas.AnaliseIAMLResult:
        modelo = cls._carregar_modelo()
        features = cls._calcular_features(db, id_sensor)
        agora = datetime.utcnow()

        if features is None:
            return schemas.AnaliseIAMLResult(
                nivel_risco="Baixo",
                probabilidade_classe=0.0,
                classes_probabilidades={},
                distancia_atual_cm=400.0,
                taxa_subida_cm_min=0.0,
                media_movel_3_cm=400.0,
                modelo_utilizado="DecisionTreeClassifier (dataset sintético)",
                data_analise=agora
            )

        X = pd.DataFrame([{k: features[k] for k in FEATURES}])
        classe_prevista = modelo.predict(X)[0]
        probabilidades = modelo.predict_proba(X)[0]
        classes_prob = dict(zip(modelo.classes_, [round(float(p), 3) for p in probabilidades]))

        resultado = schemas.AnaliseIAMLResult(
            nivel_risco=classe_prevista,
            probabilidade_classe=classes_prob[classe_prevista],
            classes_probabilidades=classes_prob,
            distancia_atual_cm=round(features["distancia_atual_cm"], 2),
            taxa_subida_cm_min=round(features["taxa_subida_cm_min"], 2),
            media_movel_3_cm=round(features["media_movel_3_cm"], 2),
            modelo_utilizado="DecisionTreeClassifier (dataset sintético)",
            data_analise=agora
        )

        if persistir:
            nova_previsao = models.PrevisaoEntupimento(
                probabilidade=round(classes_prob[classe_prevista], 2),
                nivel_risco=classe_prevista,
                id_leitura=features["id_leitura"]
            )
            db.add(nova_previsao)
            db.commit()

        return resultado