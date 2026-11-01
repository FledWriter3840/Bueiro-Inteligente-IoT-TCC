import csv
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app import cemaden_service
from app.ai_predictor import _calcular_score_clima
from app.weather_service import DadosClimaticos


class TestCemadenService(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)
        self.raiz = Path(self.diretorio.name)
        self.dataset = self.raiz / "dados"
        self.dataset.mkdir()
        self.indice = self.raiz / "cemaden.sqlite3"
        self.csv_path = self.dataset / "janeiro_2026.csv"
        self._gravar_csv([
            ["CENTRO", "ESTACAO_PROXIMA", "SP", "Centro", "-23,550", "-46,630",
             "2026-01-15 10:10:00.0", "1,20"],
            ["CENTRO", "ESTACAO_DISTANTE", "SP", "Distante", "-23,900", "-46,900",
             "2026-01-15 10:20:00.0", "9,00"],
            ["CENTRO", "ESTACAO_PROXIMA", "SP", "Centro", "-23,550", "-46,630",
             "2026-01-15 10:30:00.0", "0,80"],
            ["CENTRO", "ESTACAO_PROXIMA", "SP", "Centro", "-23,550", "-46,630",
             "2026-01-15 10:50:00.0", "0,50"],
        ])
        self.patch_dataset = patch.object(cemaden_service, "DATASET_PATH", self.dataset)
        self.patch_index = patch.object(cemaden_service, "INDEX_PATH", self.indice)
        self.patch_dataset.start()
        self.patch_index.start()
        self.addCleanup(self.patch_dataset.stop)
        self.addCleanup(self.patch_index.stop)

    def _gravar_csv(self, linhas):
        with self.csv_path.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow([
                "municipio",
                "codEstacao",
                "uf",
                "nomeEstacao",
                "latitude",
                "longitude",
                "datahora",
                "valorMedida",
            ])
            escritor.writerows(linhas)

    def test_indexa_estacao_mais_proxima_e_soma_ultima_hora(self):
        resumo = cemaden_service.construir_indice(
            self.dataset,
            self.indice,
            latitude=-23.5505,
            longitude=-46.6333,
        )
        agora = datetime(2026, 1, 15, 14, 0, tzinfo=timezone.utc)

        dados = cemaden_service.obter_dados_pluviometricos(
            latitude=-23.5505,
            longitude=-46.6333,
            agora=agora,
        )

        self.assertEqual(resumo["codigo_estacao"], "ESTACAO_PROXIMA")
        self.assertEqual(resumo["registros_indexados"], 3)
        self.assertTrue(dados.disponivel)
        self.assertEqual(dados.chuva_ultima_hora_mm, 2.5)
        self.assertEqual(dados.idade_dados_minutos, 10.0)

    def test_nao_usa_leitura_antiga_como_chuva_atual(self):
        cemaden_service.construir_indice(self.dataset, self.indice)
        agora = datetime(2026, 1, 15, 16, 0, tzinfo=timezone.utc)

        dados = cemaden_service.obter_dados_pluviometricos(agora=agora)

        self.assertFalse(dados.disponivel)
        self.assertIn("limite de atualidade", dados.status)

    def test_indice_invalida_se_os_csvs_mudarem(self):
        cemaden_service.construir_indice(self.dataset, self.indice)
        with self.csv_path.open("a", encoding="utf-8") as arquivo:
            arquivo.write(
                "CENTRO;ESTACAO_PROXIMA;SP;Centro;-23,550;-46,630;"
                "2026-01-15 10:55:00.0;0,10\n"
            )

        dados = cemaden_service.obter_dados_pluviometricos(
            agora=datetime(2026, 1, 15, 14, 0, tzinfo=timezone.utc)
        )

        self.assertFalse(dados.disponivel)
        self.assertIn("desatualizado", dados.status)

    def test_historico_retorna_totais_diarios_do_intervalo(self):
        cemaden_service.construir_indice(self.dataset, self.indice)

        historico = cemaden_service.obter_historico_diario(
            date(2026, 1, 15),
            date(2026, 1, 15),
            latitude=-23.5505,
            longitude=-46.6333,
        )

        self.assertTrue(historico["disponivel"])
        self.assertEqual(historico["total_dias_com_dados"], 1)
        self.assertEqual(historico["chuva_total_mm"], 2.5)
        self.assertEqual(historico["dias"][0]["quantidade_leituras"], 3)

    def test_chuva_cemaden_recente_prevalece_sobre_openweathermap(self):
        clima = DadosClimaticos(
            chuva_mm_h=0.0,
            umidade_pct=50,
            disponivel=True,
        )
        cemaden = cemaden_service.DadosPluviometricosCemaden(
            disponivel=True,
            chuva_ultima_hora_mm=12.0,
        )

        score_sem_cemaden = _calcular_score_clima(clima)
        score_com_cemaden = _calcular_score_clima(clima, cemaden)

        self.assertGreater(score_com_cemaden, score_sem_cemaden)


if __name__ == "__main__":
    unittest.main()
