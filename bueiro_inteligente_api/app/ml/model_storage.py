from pathlib import Path

import joblib
from sklearn.base import BaseEstimator

from ..config import ML_MODEL_PATH


def salvar_modelo(
    modelo: BaseEstimator,
    caminho: Path = ML_MODEL_PATH,
) -> None:
    """Persiste o classificador no caminho configurado."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, caminho)


def carregar_modelo(caminho: Path = ML_MODEL_PATH) -> BaseEstimator:
    """Carrega o classificador persistido ou informa que ele não existe."""
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de modelo não encontrado: {caminho}")
    return joblib.load(caminho)
