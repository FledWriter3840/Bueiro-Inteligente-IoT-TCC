import numpy as np
import pandas as pd

def _score_probabilistico(distancia_atual: float, taxa_subida: float) -> float:
    """Reaproveita a mesma lógica de regras do motor de regressão
    (app/ai_predictor.py) para gerar rótulos consistentes no dataset sintético."""
    if distancia_atual <= 15.0:
        score_base = 0.85
    elif distancia_atual <= 30.0:
        score_base = 0.65
    elif distancia_atual <= 80.0:
        score_base = 0.40
    elif distancia_atual <= 150.0:
        score_base = 0.20
    else:
        score_base = 0.05

    if taxa_subida >= 30.0:
        modificador = 0.30
    elif taxa_subida >= 15.0:
        modificador = 0.20
    elif taxa_subida >= 5.0:
        modificador = 0.10
    elif taxa_subida <= -5.0:
        modificador = -0.20
    else:
        modificador = 0.0

    return max(0.01, min(0.99, score_base + modificador))


def _classificar_risco(probabilidade: float, distancia_atual: float) -> str:
    if probabilidade >= 0.80 or distancia_atual <= 15.0:
        return "Crítico"
    elif probabilidade >= 0.60:
        return "Alto"
    elif probabilidade >= 0.35:
        return "Médio"
    return "Baixo"


def gerar_dataset_sintetico(n_amostras: int = 3000, seed: int = 42) -> pd.DataFrame:
    """
    Gera um dataset SINTÉTICO de cenários de leitura do sensor ultrassônico,
    baseado nas mesmas regras de domínio usadas no motor de regressão
    (app/ai_predictor.py), para treinar um classificador de Machine Learning.

    IMPORTANTE: dataset sintético, documentado no TCC. Deve ser substituído
    por dados reais assim que o protótipo físico estiver operacional e
    gerando histórico suficiente de leituras.
    """
    rng = np.random.default_rng(seed)
    registros = []

    for _ in range(n_amostras):
        distancia_atual = float(rng.uniform(0, 400))          # alcance do HC-SR04
        taxa_subida = float(rng.normal(loc=0, scale=15))       # cm/min, + = enchendo
        media_movel_3 = max(0.0, distancia_atual + rng.normal(loc=0, scale=8))

        probabilidade = _score_probabilistico(distancia_atual, taxa_subida)
        probabilidade_ruidosa = max(0.01, min(0.99, probabilidade + rng.normal(0, 0.03)))
        nivel_risco = _classificar_risco(probabilidade_ruidosa, distancia_atual)

        registros.append({
            "distancia_atual_cm": distancia_atual,
            "taxa_subida_cm_min": taxa_subida,
            "media_movel_3_cm": media_movel_3,
            "probabilidade": round(probabilidade_ruidosa, 3),
            "nivel_risco": nivel_risco,
        })

    return pd.DataFrame(registros)