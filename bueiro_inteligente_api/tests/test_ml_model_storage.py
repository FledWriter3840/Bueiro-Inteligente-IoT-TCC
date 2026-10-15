from unittest.mock import patch

import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

from app.ml import predictor
from app.ml.model_storage import carregar_modelo, salvar_modelo


def test_salvar_e_carregar_modelo_em_caminho_configuravel(tmp_path):
    caminho = tmp_path / "modelos" / "risco.joblib"
    modelo = DecisionTreeClassifier(random_state=42).fit(
        pd.DataFrame({"distancia_atual_cm": [10, 30]}),
        ["Crítico", "Baixo"],
    )

    salvar_modelo(modelo, caminho)
    modelo_carregado = carregar_modelo(caminho)

    assert modelo_carregado.predict(
        pd.DataFrame({"distancia_atual_cm": [10]})
    )[0] == "Crítico"


def test_carregar_modelo_inexistente_informa_caminho(tmp_path):
    caminho = tmp_path / "ausente.joblib"

    with pytest.raises(FileNotFoundError, match="ausente.joblib"):
        carregar_modelo(caminho)


def test_predictor_carrega_modelo_preguicosamente_e_treina_se_ausente(monkeypatch):
    modelo = DecisionTreeClassifier()
    monkeypatch.setattr(predictor.PrevisorEntupimentoML, "_modelo", None)
    with patch(
        "app.ml.predictor.carregar_modelo",
        side_effect=[FileNotFoundError("modelo ausente"), modelo],
    ) as carregar:
        with patch("app.ml.train.treinar_modelo") as treinar:
            primeira_carga = predictor.PrevisorEntupimentoML._carregar_modelo()
            segunda_carga = predictor.PrevisorEntupimentoML._carregar_modelo()

    assert primeira_carga is modelo
    assert segunda_carga is modelo
    treinar.assert_called_once_with()
    assert carregar.call_count == 2
