import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import get_db
from app.routers import camera as camera_router


class TestCameraRouter(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.image_directory = Path(self.temporary_directory.name) / "images"
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(
            self.engine,
            tables=[
                models.Sensor.__table__,
                models.LeituraSensor.__table__,
                models.Camera.__table__,
                models.RegistroImagem.__table__,
            ],
        )
        self.session_factory = sessionmaker(bind=self.engine)
        app = FastAPI()
        app.include_router(camera_router.router)

        def override_get_db():
            session = self.session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        self.storage_patch = patch.object(
            camera_router,
            "IMAGE_STORAGE_DIR",
            self.image_directory,
        )
        self.storage_patch.start()

    def tearDown(self):
        self.storage_patch.stop()
        self.engine.dispose()
        self.temporary_directory.cleanup()

    def test_recebe_guarda_e_retorna_imagem(self):
        jpeg = b"\xff\xd8\xff\xe0test-image\xff\xd9"

        resposta = self.client.post(
            "/camera/imagens",
            params={"camera_id": 1},
            content=jpeg,
            headers={"Content-Type": "image/jpeg"},
        )

        self.assertEqual(resposta.status_code, 201)
        dados = resposta.json()
        self.assertEqual(dados["status_analise"], "Sem modelo")
        self.assertEqual(dados["caminho_imagem"].split("/")[0], "images")
        image_file = self.image_directory / Path(dados["caminho_imagem"]).name
        self.assertTrue(image_file.is_file())

        imagem = self.client.get(dados["url_imagem"])
        self.assertEqual(imagem.status_code, 200)
        self.assertEqual(imagem.content, jpeg)
        self.assertEqual(imagem.headers["content-type"], "image/jpeg")

    def test_lista_imagens_salvas(self):
        jpeg = b"\xff\xd8\xff\xe0test-image\xff\xd9"
        criada = self.client.post(
            "/camera/imagens",
            content=jpeg,
            headers={"Content-Type": "image/jpeg"},
        ).json()

        resposta = self.client.get("/camera/imagens")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()[0]["id_imagem"], criada["id_imagem"])
        self.assertIsNotNone(resposta.json()[0]["data_hora"])

    def test_associa_imagem_a_leitura_do_sensor(self):
        with self.session_factory() as session:
            session.add(
                models.Sensor(
                    id_sensor=1,
                    tipo_sensor="Ultrassonico",
                    status_sensor="Ativo",
                )
            )
            leitura = models.LeituraSensor(
                id_sensor=1,
                valor_leitura=42.5,
                unidade_medida="cm",
            )
            session.add(leitura)
            session.commit()
            id_leitura = leitura.id_leitura

        resposta = self.client.post(
            "/camera/imagens",
            params={"id_leitura": id_leitura},
            content=b"\xff\xd8\xff\xe0test-image\xff\xd9",
            headers={"Content-Type": "image/jpeg"},
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["id_leitura"], id_leitura)

    def test_rejeita_conteudo_que_nao_e_jpeg(self):
        resposta = self.client.post(
            "/camera/imagens",
            content=b"nao e jpeg",
            headers={"Content-Type": "image/jpeg"},
        )

        self.assertEqual(resposta.status_code, 400)

    @patch.object(
        camera_router,
        "analisar_residuo",
        return_value=camera_router.ResultadoAnaliseResiduo(
            "Plástico",
            0.92,
            "Analisada",
        ),
    )
    def test_classifica_residuo_e_indica_possivel_interferencia(
        self,
        analisar_residuo,
    ):
        resposta = self.client.post(
            "/camera/imagens",
            content=b"\xff\xd8\xff\xe0test-image\xff\xd9",
            headers={"Content-Type": "image/jpeg"},
        )

        self.assertEqual(resposta.status_code, 201)
        dados = resposta.json()
        self.assertEqual(dados["tipo_residuo"], "Plástico")
        self.assertEqual(dados["confianca_ia"], 0.92)
        self.assertEqual(dados["status_analise"], "Analisada")
        self.assertTrue(dados["possivel_interferencia_sensor"])
        analisar_residuo.assert_called_once()

    @patch.object(
        camera_router,
        "analisar_residuo",
        return_value=camera_router.ResultadoAnaliseResiduo(
            "Sem resíduo",
            0.95,
            "Analisada",
        ),
    )
    def test_sem_residuo_nao_sinaliza_interferencia(self, analisar_residuo):
        resposta = self.client.post(
            "/camera/imagens",
            content=b"\xff\xd8\xff\xe0test-image\xff\xd9",
            headers={"Content-Type": "image/jpeg"},
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertFalse(resposta.json()["possivel_interferencia_sensor"])
        analisar_residuo.assert_called_once()


if __name__ == "__main__":
    unittest.main()
