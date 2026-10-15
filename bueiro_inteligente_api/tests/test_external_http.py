from unittest.mock import Mock, patch

from app.external_http import ExternalHttpClient


@patch("app.external_http.requests.get")
def test_get_json_aplica_timeout_e_verifica_status(mock_get):
    resposta = Mock()
    resposta.json.return_value = {"ok": True}
    mock_get.return_value = resposta

    resultado = ExternalHttpClient.get_json(
        "https://provider.example/data",
        timeout=8,
        params={"id": 1},
    )

    assert resultado == {"ok": True}
    mock_get.assert_called_once_with(
        "https://provider.example/data",
        params={"id": 1},
        headers=None,
        timeout=8,
    )
    resposta.raise_for_status.assert_called_once_with()
