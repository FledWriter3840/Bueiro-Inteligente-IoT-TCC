from unittest.mock import patch

import requests

from app.dados_externos import UsoDeSoloProvider


@patch("app.dados_externos.OVERPASS_API_URL_FALLBACK", "https://fallback.example/api")
@patch("app.dados_externos.OVERPASS_API_URL", "https://primary.example/api")
@patch("app.dados_externos.external_http_client.post_json")
def test_overpass_tenta_endpoint_de_fallback_quando_o_principal_falha(post_json):
    post_json.side_effect = [
        requests.Timeout("endpoint indisponivel"),
        {
            "elements": [
                {
                    "tags": {"landuse": "residential"},
                    "center": {"lat": -23.55, "lon": -46.63},
                }
            ]
        },
    ]

    perfil = UsoDeSoloProvider().obter_perfil(lat=-23.55, lon=-46.63)

    assert perfil.disponivel
    assert perfil.tipo_via == "Residencial"
    assert [chamada.args[0] for chamada in post_json.call_args_list] == [
        "https://primary.example/api",
        "https://fallback.example/api",
    ]


@patch("app.dados_externos.OVERPASS_API_URL_FALLBACK", "https://primary.example/api")
@patch("app.dados_externos.OVERPASS_API_URL", "https://primary.example/api")
@patch("app.dados_externos.external_http_client.post_json")
def test_overpass_nao_duplica_tentativa_quando_endpoints_sao_iguais(post_json):
    post_json.return_value = {"elements": []}

    perfil = UsoDeSoloProvider().obter_perfil(lat=-23.55, lon=-46.63)

    assert not perfil.disponivel
    post_json.assert_called_once()
