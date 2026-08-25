from pathlib import Path

import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from .dataset import gerar_dataset_sintetico

MODELO_PATH = Path(__file__).parent / "modelo_risco.joblib"
FEATURES = ["distancia_atual_cm", "taxa_subida_cm_min", "media_movel_3_cm"]
LABEL = "nivel_risco"


def treinar_modelo(n_amostras: int = 3000, salvar: bool = True) -> dict:
    """
    Treina um classificador de Árvore de Decisão sobre o dataset sintético
    de leituras do sensor, prevendo o nível de risco de entupimento.

    Retorna métricas de avaliação (acurácia, relatório de classificação,
    matriz de confusão) — úteis para demonstrar o pipeline funcionando na banca.
    """
    df = gerar_dataset_sintetico(n_amostras=n_amostras)

    X = df[FEATURES]
    y = df[LABEL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    modelo = DecisionTreeClassifier(max_depth=5, random_state=42)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)

    if salvar:
        joblib.dump(modelo, MODELO_PATH)

    return {
        "acuracia": round(accuracy_score(y_test, y_pred), 4),
        "relatorio_classificacao": classification_report(y_test, y_pred, zero_division=0),
        "matriz_confusao": confusion_matrix(y_test, y_pred, labels=modelo.classes_).tolist(),
        "classes": modelo.classes_.tolist(),
        "n_amostras_treino": len(X_train),
        "n_amostras_teste": len(X_test),
    }


if __name__ == "__main__":
    metricas = treinar_modelo()
    print(f"Acurácia: {metricas['acuracia']}")
    print(metricas["relatorio_classificacao"])