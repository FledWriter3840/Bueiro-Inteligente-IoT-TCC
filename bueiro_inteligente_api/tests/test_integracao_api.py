"""Testes de integracao contra uma API FastAPI em execucao.

Uso:
    python -m unittest tests.test_integracao_api -v

A API deve estar em http://localhost:8000 ou em API_URL.
"""

import os
import unittest

import requests


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


class TestIntegracaoAPI(unittest.TestCase):
    def request(self, method: str, endpoint: str, **kwargs):
        response = requests.request(
            method,
            f"{API_URL}{endpoint}",
            timeout=30,
            **kwargs,
        )
        self.assertLess(response.status_code, 400, response.text)
        return response.json()

    def test_api_esta_disponivel(self):
        resultado = self.request("GET", "/")
        self.assertIn("message", resultado)

    def test_seis_fontes_de_dados(self):
        resultado = self.request("GET", "/ia/fontes-dados")
        self.assertEqual(resultado["total_fontes"], 6)
        self.assertGreaterEqual(resultado["total_ativas"], 5)
        self.assertEqual(len(resultado["fontes"]), 6)

    def test_leitura_executa_os_dois_modelos(self):
        leitura = {
            "id_sensor": 1,
            "valor_leitura": 60.0,
            "unidade_medida": "cm",
        }
        resultado = self.request("POST", "/sensores/leitura", json=leitura)

        self.assertIn(resultado["nivel_risco"], {"Baixo", "Médio", "Alto", "Crítico"})
        self.assertIn(resultado["nivel_risco_multivariado"], {"Baixo", "Médio", "Alto", "Crítico"})
        self.assertIn(resultado["nivel_risco_ml"], {"Baixo", "Médio", "Alto", "Crítico"})
        self.assertEqual(resultado["modelo_decisao"], "Multivariada + Machine Learning")
        self.assertIsInstance(resultado["acionar_limpeza"], bool)
        self.assertGreaterEqual(resultado["tempo_limpeza_segundos"], 0)

    def test_leitura_critica_retorna_decisao_critica(self):
        leitura = {
            "id_sensor": 1,
            "valor_leitura": 8.0,
            "unidade_medida": "cm",
        }
        resultado = self.request("POST", "/sensores/leitura", json=leitura)

        self.assertEqual(resultado["nivel_risco"], "Crítico")
        self.assertEqual(resultado["nivel_risco_multivariado"], "Crítico")
        self.assertEqual(resultado["nivel_risco_ml"], "Crítico")
        self.assertEqual(resultado["tempo_limpeza_segundos"], 15 if resultado["acionar_limpeza"] else 0)

    def test_resposta_e_compativel_com_firmware(self):
        leitura = {
            "id_sensor": 1,
            "valor_leitura": 200.0,
            "unidade_medida": "cm",
        }
        resultado = self.request("POST", "/sensores/leitura", json=leitura)

        # Estes campos sao os que o ESP32 interpreta para comandar o servo.
        self.assertIn("acionar_limpeza", resultado)
        self.assertIn("tempo_limpeza_segundos", resultado)
        self.assertIsInstance(resultado["tempo_limpeza_segundos"], int)


if __name__ == "__main__":
    unittest.main()
