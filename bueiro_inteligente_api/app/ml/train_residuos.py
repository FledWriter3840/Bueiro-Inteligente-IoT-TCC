import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .residuos import (
    CAMINHO_MODELO,
    CLASSES_RESIDUOS,
    EXTENSOES_IMAGEM,
    extrair_caracteristicas,
)

MINIMO_IMAGENS_POR_CLASSE = 10


def treinar_modelo_residuos(
    diretorio_dataset: Path,
    caminho_modelo: Path = CAMINHO_MODELO,
) -> dict[str, object]:
    """Treina um classificador local com imagens organizadas por classe."""
    features: list[np.ndarray] = []
    labels: list[str] = []
    quantidades: dict[str, int] = {}

    for classe in CLASSES_RESIDUOS:
        pasta_classe = diretorio_dataset / classe
        imagens = sorted(
            caminho
            for caminho in pasta_classe.rglob("*")
            if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_IMAGEM
        ) if pasta_classe.is_dir() else []
        quantidades[classe] = len(imagens)
        if len(imagens) < MINIMO_IMAGENS_POR_CLASSE:
            raise ValueError(
                f"A classe '{classe}' precisa de pelo menos "
                f"{MINIMO_IMAGENS_POR_CLASSE} imagens; encontradas {len(imagens)}."
            )
        for caminho_imagem in imagens:
            features.append(extrair_caracteristicas(caminho_imagem.read_bytes()))
            labels.append(classe)

    X = np.stack(features)
    y = np.asarray(labels)
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    modelo = make_pipeline(
        StandardScaler(),
        CalibratedClassifierCV(
            estimator=SVC(
                kernel="rbf",
                C=10.0,
                class_weight="balanced",
                random_state=42,
            ),
            method="sigmoid",
            cv=3,
        ),
    )
    modelo.fit(X_treino, y_treino)
    previsoes = modelo.predict(X_teste)
    acuracia = float(accuracy_score(y_teste, previsoes))

    caminho_modelo.parent.mkdir(parents=True, exist_ok=True)
    caminho_temporario = caminho_modelo.with_suffix(
        f"{caminho_modelo.suffix}.tmp"
    )
    try:
        joblib.dump(
            {
                "versao": 1,
                "classes": list(CLASSES_RESIDUOS),
                "modelo": modelo,
            },
            caminho_temporario,
        )
        caminho_temporario.replace(caminho_modelo)
    finally:
        caminho_temporario.unlink(missing_ok=True)

    return {
        "acuracia_teste": round(acuracia, 4),
        "relatorio_classificacao": classification_report(
            y_teste,
            previsoes,
            labels=list(CLASSES_RESIDUOS),
            target_names=list(CLASSES_RESIDUOS.values()),
            zero_division=0,
        ),
        "matriz_confusao": confusion_matrix(
            y_teste,
            previsoes,
            labels=list(CLASSES_RESIDUOS),
        ).tolist(),
        "classes": list(CLASSES_RESIDUOS.values()),
        "imagens_por_classe": quantidades,
        "total_imagens": len(labels),
        "caminho_modelo": str(caminho_modelo),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Treina o classificador local de resíduos a partir de imagens."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Pasta contendo uma subpasta por classe.",
    )
    parser.add_argument(
        "--modelo",
        type=Path,
        default=CAMINHO_MODELO,
        help="Caminho do arquivo de modelo a salvar.",
    )
    argumentos = parser.parse_args()
    metricas = treinar_modelo_residuos(argumentos.dataset, argumentos.modelo)
    print(json.dumps(metricas, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
