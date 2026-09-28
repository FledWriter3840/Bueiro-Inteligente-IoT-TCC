import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import bueiros as bueiros_router
from app.routers.bueiros import router


class TestBueirosRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def test_lista_rodovias_do_inventario(self):
        resposta = self.client.get("/bueiros/rodovias")

        self.assertEqual(resposta.status_code, 200)
        rodovias = resposta.json()
        self.assertTrue(rodovias)
        self.assertEqual(rodovias, sorted(set(rodovias)))

    def test_filtra_bueiros_por_rodovia_com_coordenadas_validas(self):
        resposta = self.client.get("/bueiros/", params={"rodovia": "SP 081"})

        self.assertEqual(resposta.status_code, 200)
        bueiros = resposta.json()
        self.assertTrue(bueiros)
        self.assertTrue(all(bueiro["rodovia"] == "SP 081" for bueiro in bueiros))
        for bueiro in bueiros:
            self.assertGreaterEqual(bueiro["latitude_montante"], -90)
            self.assertLessEqual(bueiro["latitude_montante"], 90)
            self.assertGreaterEqual(bueiro["longitude_jusante"], -180)
            self.assertLessEqual(bueiro["longitude_jusante"], 180)

    def test_busca_chamados_sac_proximos_da_localizacao(self):
        resposta = self.client.get(
            "/bueiros/solicitacoes-limpeza",
            params={"lat": -23.55, "lon": -46.63, "raio_m": 1000},
        )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        self.assertGreater(dados["total_encontradas"], 0)
        self.assertGreaterEqual(dados["total_finalizadas"], 0)
        self.assertTrue(all(item["distancia_m"] <= 1000 for item in dados["solicitacoes"]))
        self.assertIn("indice_constancia_chamados", dados)

    def test_lista_locais_sac_com_coordenadas_validas_e_deduplicados(self):
        resposta = self.client.get("/bueiros/locais-sac")

        self.assertEqual(resposta.status_code, 200)
        locais = resposta.json()
        self.assertTrue(locais)
        self.assertEqual(
            len(locais),
            len({(round(local["latitude"], 6), round(local["longitude"], 6)) for local in locais}),
        )
        for local in locais:
            self.assertGreaterEqual(local["latitude"], -90)
            self.assertLessEqual(local["latitude"], 90)
            self.assertGreaterEqual(local["longitude"], -180)
            self.assertLessEqual(local["longitude"], 180)
            self.assertGreater(local["total_solicitacoes"], 0)

    def test_rejeita_raio_fora_dos_limites(self):
        resposta = self.client.get(
            "/bueiros/solicitacoes-limpeza",
            params={"lat": -23.55, "lon": -46.63, "raio_m": 50},
        )

        self.assertEqual(resposta.status_code, 422)

    def test_cadastra_e_lista_novo_bueiro(self):
        cadastro = {
            "regional": "Teste local",
            "elemento": "Boca de lobo",
            "rodovia": "Rua de Teste",
            "levantamento": "2026-09-26",
            "km": 12.5,
            "extensao_m": None,
            "dimensao_m": None,
            "tipo": "Boca de lobo de concreto",
            "latitude_montante": -23.55,
            "longitude_montante": -46.63,
            "latitude_jusante": -23.5501,
            "longitude_jusante": -46.6301,
        }
        with tempfile.TemporaryDirectory() as diretorio:
            arquivo_adicoes = Path(diretorio) / "bueiros_adicionados.json"
            with patch.object(bueiros_router, "ADICOES_PATH", arquivo_adicoes):
                resposta = self.client.post("/bueiros/", json=cadastro)
                self.assertEqual(resposta.status_code, 201)
                criado = resposta.json()

                rodovias = self.client.get("/bueiros/rodovias").json()
                listagem = self.client.get(
                    "/bueiros/", params={"rodovia": cadastro["rodovia"]}
                ).json()

        self.assertTrue(criado["id"].startswith("NOVO-"))
        self.assertIn(cadastro["rodovia"], rodovias)
        self.assertIn(criado, listagem)

    def test_rejeita_coordenada_fora_dos_limites_no_cadastro(self):
        resposta = self.client.post("/bueiros/", json={
            "regional": "Teste",
            "elemento": "Bueiro",
            "rodovia": "SP 999",
            "levantamento": "2026-09-26",
            "km": 1,
            "tipo": "Concreto",
            "latitude_montante": 120,
            "longitude_montante": 0,
            "latitude_jusante": 0,
            "longitude_jusante": 0,
        })

        self.assertEqual(resposta.status_code, 422)


if __name__ == "__main__":
    unittest.main()