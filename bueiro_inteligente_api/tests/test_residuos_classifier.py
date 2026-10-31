import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from app.ml.residuos import (
    CLASSES_RESIDUOS,
    ResultadoAnaliseResiduo,
    analisar_residuo,
    extrair_caracteristicas,
)
from app.ml.train_residuos import treinar_modelo_residuos


class TestClassificadorResiduos(unittest.TestCase):
    def test_retorna_sem_modelo_quando_artefato_nao_existe(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            resultado = analisar_residuo(
                b"jpeg ainda nao precisa ser decodificado",
                Path(temporary_directory) / "modelo.joblib",
            )

        self.assertEqual(
            resultado,
            ResultadoAnaliseResiduo(None, None, "Sem modelo"),
        )
        self.assertIsNone(resultado.possivel_interferencia_sensor)

    def test_extrai_caracteristicas_de_jpeg(self):
        imagem = np.zeros((64, 64, 3), dtype=np.uint8)
        sucesso, jpeg = cv2.imencode(".jpg", imagem)
        self.assertTrue(sucesso)

        caracteristicas = extrair_caracteristicas(jpeg.tobytes())

        self.assertEqual(caracteristicas.dtype, np.float32)
        self.assertGreater(caracteristicas.size, 0)

    def test_rejeita_imagem_que_nao_pode_ser_decodificada(self):
        with self.assertRaises(ValueError):
            extrair_caracteristicas(b"nao e uma imagem")

    def test_treina_e_carrega_modelo_completo(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            raiz = Path(temporary_directory)
            dataset = raiz / "dataset"
            caminho_modelo = raiz / "modelo.joblib"
            cores = (
                (255, 0, 0),
                (255, 255, 0),
                (0, 255, 0),
                (0, 0, 255),
                (255, 0, 255),
                (0, 255, 255),
            )
            for indice, classe in enumerate(CLASSES_RESIDUOS):
                pasta = dataset / classe
                pasta.mkdir(parents=True)
                for amostra in range(10):
                    imagem = np.zeros((96, 96, 3), dtype=np.uint8)
                    imagem[:] = cores[indice]
                    cv2.rectangle(
                        imagem,
                        (10 + amostra, 10),
                        (70, 70),
                        tuple(reversed(cores[indice])),
                        thickness=2 + amostra % 3,
                    )
                    sucesso, jpeg = cv2.imencode(".jpg", imagem)
                    self.assertTrue(sucesso)
                    (pasta / f"{amostra}.jpg").write_bytes(jpeg.tobytes())

            metricas = treinar_modelo_residuos(dataset, caminho_modelo)
            self.assertTrue(caminho_modelo.is_file())
            resultado = analisar_residuo(
                (dataset / "plastico" / "0.jpg").read_bytes(),
                caminho_modelo,
            )

        self.assertEqual(metricas["total_imagens"], 60)
        self.assertIn(resultado.status, {"Analisada", "Baixa confiança"})
        self.assertIsNotNone(resultado.confianca)
        if resultado.status == "Analisada":
            self.assertIn(resultado.tipo_residuo, CLASSES_RESIDUOS.values())
            self.assertIsInstance(resultado.possivel_interferencia_sensor, bool)


if __name__ == "__main__":
    unittest.main()
