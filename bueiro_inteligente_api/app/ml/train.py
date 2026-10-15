from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from ..config import ML_MAX_DEPTH, ML_N_AMOSTRAS, ML_RANDOM_STATE, ML_TEST_SIZE
from .dataset import gerar_dataset_sintetico
from .features import FEATURES, LABEL
from .model_storage import salvar_modelo


def treinar_modelo(n_amostras: int = ML_N_AMOSTRAS, salvar: bool = True) -> dict:
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
        X,
        y,
        test_size=ML_TEST_SIZE,
        random_state=ML_RANDOM_STATE,
        stratify=y,
    )

    modelo = DecisionTreeClassifier(
        max_depth=ML_MAX_DEPTH,
        random_state=ML_RANDOM_STATE,
    )
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)

    if salvar:
        salvar_modelo(modelo)

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