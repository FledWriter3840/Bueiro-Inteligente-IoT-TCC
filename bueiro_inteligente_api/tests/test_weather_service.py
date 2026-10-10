import unittest
from unittest.mock import patch

from app import weather_service


class TestWeatherServiceCache(unittest.TestCase):
    def setUp(self):
        weather_service.limpar_cache()

    def tearDown(self):
        weather_service.limpar_cache()

    @patch("app.weather_service._buscar_previsao", return_value=None)
    @patch("app.weather_service._buscar_clima_atual")
    def test_cache_isolado_por_localidade(self, buscar_clima, _buscar_previsao):
        buscar_clima.side_effect = [
            {"main": {"temp": 18, "humidity": 70}, "weather": [{"description": "nublado"}]},
            {"main": {"temp": 29, "humidity": 40}, "weather": [{"description": "ensolarado"}]},
        ]

        clima_a = weather_service.obter_dados_climaticos(-23.55, -46.63)
        clima_b = weather_service.obter_dados_climaticos(-22.90, -43.20)

        self.assertEqual(clima_a.temperatura_c, 18)
        self.assertEqual(clima_b.temperatura_c, 29)
        self.assertEqual(buscar_clima.call_count, 2)

    @patch("app.weather_service._buscar_previsao")
    @patch("app.weather_service._buscar_clima_atual", return_value=None)
    def test_fallback_de_uma_localidade_nao_afeta_outra(
        self,
        buscar_clima,
        buscar_previsao,
    ):
        fallback = weather_service.obter_dados_climaticos(-23.55, -46.63)
        clima = weather_service.obter_dados_climaticos(-22.90, -43.20)

        self.assertFalse(fallback.disponivel)
        self.assertFalse(clima.disponivel)
        self.assertEqual(buscar_clima.call_count, 2)
        buscar_previsao.assert_not_called()

    @patch("app.weather_service._buscar_previsao", return_value=None)
    @patch("app.weather_service._buscar_clima_atual")
    def test_cache_valido_reaproveita_clima_da_mesma_localidade(
        self,
        buscar_clima,
        _buscar_previsao,
    ):
        buscar_clima.return_value = {
            "main": {"temp": 18, "humidity": 70},
            "weather": [{"description": "nublado"}],
        }

        primeira_consulta = weather_service.obter_dados_climaticos(-23.55, -46.63)
        segunda_consulta = weather_service.obter_dados_climaticos(-23.55, -46.63)

        self.assertIs(primeira_consulta, segunda_consulta)
        buscar_clima.assert_called_once()


if __name__ == "__main__":
    unittest.main()
