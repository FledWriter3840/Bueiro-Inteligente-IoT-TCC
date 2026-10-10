import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.routers.sensores import listar_leituras
from app.schemas import LeituraSensorOut


class TestLeiturasRisco(unittest.TestCase):
    def _db_com_resultados(self, leituras, previsoes):
        query_leituras = MagicMock()
        query_leituras.order_by.return_value.all.return_value = leituras
        query_previsoes = MagicMock()
        query_previsoes.filter.return_value.order_by.return_value.all.return_value = previsoes

        db = MagicMock()
        db.query.side_effect = [query_leituras, query_previsoes]
        return db

    def test_historico_retorna_risco_da_previsao_vinculada(self):
        leitura = SimpleNamespace(
            id_leitura=12,
            id_sensor=1,
            valor_leitura=8.0,
            unidade_medida="cm",
            data_hora=datetime(2026, 10, 7, 12, 0),
        )
        previsao = SimpleNamespace(id_leitura=12, nivel_risco="Crítico")
        db = self._db_com_resultados([leitura], [previsao])

        resposta = listar_leituras(db)
        leitura_api = LeituraSensorOut.model_validate(resposta[0])

        self.assertEqual(leitura_api.nivel_risco, "Crítico")

    def test_historico_nao_inventa_risco_baixo_sem_previsao(self):
        leitura = SimpleNamespace(
            id_leitura=13,
            id_sensor=1,
            valor_leitura=8.0,
            unidade_medida="cm",
            data_hora=datetime(2026, 10, 7, 12, 1),
        )
        db = self._db_com_resultados([leitura], [])

        resposta = listar_leituras(db)
        leitura_api = LeituraSensorOut.model_validate(resposta[0])

        self.assertIsNone(leitura_api.nivel_risco)


if __name__ == "__main__":
    unittest.main()
