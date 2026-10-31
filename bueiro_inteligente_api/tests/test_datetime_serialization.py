import unittest
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import schemas


class TestDatetimeSerialization(unittest.TestCase):
    def setUp(self):
        app = FastAPI()

        @app.get("/leitura", response_model=schemas.LeituraSensorOut)
        def obter_leitura():
            return {
                "id_sensor": 1,
                "valor_leitura": 120.0,
                "unidade_medida": "cm",
                "id_leitura": 1,
                "data_hora": self.timestamp,
            }

        self.client = TestClient(app)

    def test_serializa_datetime_ingenuo_assumindo_utc(self):
        self.timestamp = datetime(2026, 10, 26, 1, 15, 30)

        response = self.client.get("/leitura")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data_hora"], "25/10/2026 22:15:30")

    def test_serializa_datetime_com_fuso_em_horario_de_brasilia(self):
        self.timestamp = datetime(2026, 10, 26, 1, 15, 30, tzinfo=timezone.utc)

        response = self.client.get("/leitura")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data_hora"], "25/10/2026 22:15:30")


if __name__ == "__main__":
    unittest.main()
