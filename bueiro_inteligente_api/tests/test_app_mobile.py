import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models, schemas
from app.database import get_db
from app.repositories.leituras import LeituraRepository
from app.main import app as api_app
from app.routers import app_mobile, bueiros, sensores
from app.services.monitoramento import (
    calcular_nivel_percentual,
    calcular_status_bueiro,
)


class TestStatusBueiro(unittest.TestCase):
    def test_limites_de_status(self):
        casos = (
            (0, "livre"),
            (49.9, "livre"),
            (50, "atencao"),
            (79.9, "atencao"),
            (80, "critico"),
            (100, "critico"),
        )
        for nivel, status in casos:
            with self.subTest(nivel=nivel):
                self.assertEqual(calcular_status_bueiro(nivel), status)

    def test_converte_distancia_em_percentual_indicativo(self):
        self.assertEqual(calcular_nivel_percentual(90, "cm"), 80.0)
        self.assertEqual(calcular_nivel_percentual(75, "%"), 75.0)


class TestAppMobileAPI(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.uploads_directory = Path(self.temporary_directory.name) / "uploads"
        self.uploads_directory.mkdir()
        self.uploads_patch = patch.object(
            app_mobile,
            "UPLOADS_DIR",
            self.uploads_directory,
        )
        self.uploads_patch.start()
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        app = FastAPI()
        app.include_router(bueiros.router)
        app.include_router(sensores.router)
        app.include_router(app_mobile.router)
        app.mount(
            "/uploads",
            StaticFiles(directory=str(self.uploads_directory)),
            name="uploads",
        )

        def override_get_db():
            session = self.session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        with self.session_factory() as session:
            session.add(
                models.Sensor(
                    id_sensor=1,
                    tipo_sensor="Ultrassonico",
                    status_sensor="Ativo",
                    latitude=-23.5505,
                    longitude=-46.6333,
                )
            )
            session.add(
                models.LeituraSensor(
                    id_sensor=1,
                    valor_leitura=90,
                    unidade_medida="cm",
                    data_hora=datetime(2026, 11, 2, 18),
                )
            )
            session.commit()

    def tearDown(self):
        self.uploads_patch.stop()
        self.engine.dispose()
        self.temporary_directory.cleanup()

    def test_lista_detalhe_e_resumo_de_bueiros(self):
        resposta = self.client.get("/bueiros")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()[0]["nivel"], 80.0)
        self.assertEqual(resposta.json()[0]["status"], "critico")

        detalhe = self.client.get("/bueiros/1")
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(len(detalhe.json()["historico"]), 1)

        resumo = self.client.get("/resumo")
        self.assertEqual(resumo.status_code, 200)
        self.assertEqual(resumo.json()["bueiros_por_status"]["critico"], 1)

    @patch(
        "app.routers.bueiros.PrevisorEntupimentoIA.analisar_e_prever",
        return_value=SimpleNamespace(
            nivel_risco="Crítico",
            tempo_estimado_transbordo_min=720,
            recomendacao="Acompanhar o nível e acionar a equipe.",
        ),
    )
    def test_previsao_usa_o_motor_de_ia_existente(self, analisar):
        resposta = self.client.get("/bueiros/1/previsao")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["risco"], "alto")
        self.assertEqual(resposta.json()["horas_estimadas"], 12)
        analisar.assert_called_once()

    def test_cria_filtra_e_atualiza_ocorrencia(self):
        criada = self.client.post(
            "/ocorrencias",
            json={
                "descricao": "Alagamento na via",
                "latitude": -23.55,
                "longitude": -46.63,
                "gravidade": "grave",
            },
        )
        self.assertEqual(criada.status_code, 201)
        id_ocorrencia = criada.json()["id"]

        lista = self.client.get(
            "/ocorrencias",
            params={"status": "aberta", "gravidade": "grave"},
        )
        self.assertEqual(lista.status_code, 200)
        self.assertEqual(len(lista.json()), 1)

        atualizada = self.client.patch(
            f"/ocorrencias/{id_ocorrencia}",
            json={"status": "em_analise"},
        )
        self.assertEqual(atualizada.status_code, 200)
        self.assertEqual(atualizada.json()["status"], "em_analise")

        resumo = self.client.get("/resumo").json()
        self.assertEqual(resumo["ocorrencias_por_status"]["em_analise"], 1)
        self.assertEqual(resumo["ocorrencias_por_gravidade"]["grave"], 1)

    def test_upload_de_foto_e_servico_estatico(self):
        ocorrencia = self.client.post(
            "/ocorrencias",
            json={"latitude": -23.55, "longitude": -46.63},
        ).json()
        jpeg = b"\xff\xd8\xff\xe0imagem-de-teste\xff\xd9"

        resposta = self.client.post(
            f"/ocorrencias/{ocorrencia['id']}/foto",
            files={"foto": ("alagamento.jpg", jpeg, "image/jpeg")},
        )

        self.assertEqual(resposta.status_code, 201)
        foto_url = resposta.json()["foto_url"]
        imagem = self.client.get(foto_url)
        self.assertEqual(imagem.status_code, 200)
        self.assertEqual(imagem.content, jpeg)

    def test_saude_e_validacao_de_entradas_invalidas(self):
        self.assertEqual(self.client.get("/saude").json(), {"status": "ok"})
        gravidade_invalida = self.client.post(
            "/ocorrencias",
            json={
                "latitude": -23.55,
                "longitude": -46.63,
                "gravidade": "extrema",
            },
        )
        coordenada_ausente = self.client.post(
            "/ocorrencias",
            json={"longitude": -46.63},
        )
        coordenada_invalida = self.client.post(
            "/ocorrencias",
            json={"latitude": 91, "longitude": -46.63},
        )

        self.assertEqual(gravidade_invalida.status_code, 422)
        self.assertEqual(coordenada_ausente.status_code, 422)
        self.assertEqual(coordenada_invalida.status_code, 422)

    def test_api_principal_habilita_cors(self):
        cliente = TestClient(api_app)
        resposta = cliente.options(
            "/saude",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.headers["access-control-allow-origin"],
            "*",
        )


class TestIdempotenciaLeitura(unittest.TestCase):
    def test_timestamp_do_dispositivo_ignora_reenvio(self):
        engine = create_engine("sqlite://")
        models.Base.metadata.create_all(
            engine,
            tables=[models.Sensor.__table__, models.LeituraSensor.__table__],
        )
        with Session(engine) as session:
            session.add(
                models.Sensor(
                    id_sensor=1,
                    tipo_sensor="Ultrassonico",
                    status_sensor="Ativo",
                )
            )
            session.commit()
            repository = LeituraRepository(session)
            primeira, nova = repository.criar_leitura(
                schemas.LeituraSensorCreate(
                    id_sensor=1,
                    valor_leitura=90,
                    unidade_medida="cm",
                    data_hora=datetime(2026, 11, 2, 18, tzinfo=timezone.utc),
                )
            )
            segunda, nova_segunda = repository.criar_leitura(
                schemas.LeituraSensorCreate(
                    id_sensor=1,
                    valor_leitura=80,
                    unidade_medida="cm",
                    data_hora=datetime(
                        2026,
                        11,
                        2,
                        15,
                        tzinfo=timezone(timedelta(hours=-3)),
                    ),
                )
            )

        self.assertTrue(nova)
        self.assertFalse(nova_segunda)
        self.assertEqual(primeira.id_leitura, segunda.id_leitura)
        self.assertEqual(segunda.valor_leitura, 90)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
