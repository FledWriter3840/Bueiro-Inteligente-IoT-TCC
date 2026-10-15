import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app import schemas
from app.enums import NivelRisco
from app.repositories.leituras import LeituraRepository
from app.services.leituras import (
    LeituraService,
    combinar_riscos,
    decidir_acionamento,
)
from sqlalchemy.exc import SQLAlchemyError


class TestDecisoesLeitura(unittest.TestCase):
    def test_combina_riscos_escolhendo_o_mais_severo(self):
        self.assertEqual(
            combinar_riscos(NivelRisco.MEDIO.value, NivelRisco.ALTO.value),
            NivelRisco.ALTO.value,
        )

    def test_mapeia_todos_os_riscos_para_duracao(self):
        esperado = {
            NivelRisco.BAIXO.value: (False, 0),
            NivelRisco.MEDIO.value: (True, 5),
            NivelRisco.ALTO.value: (True, 10),
            NivelRisco.CRITICO.value: (True, 15),
        }
        for risco, resultado in esperado.items():
            with self.subTest(risco=risco):
                self.assertEqual(decidir_acionamento(risco, False), resultado)

    def test_janela_recente_impede_novo_acionamento(self):
        service = LeituraService(MagicMock())
        service.repository.criar_leitura.return_value = SimpleNamespace(
            id_sensor=1,
            id_leitura=12,
            valor_leitura=8.0,
            unidade_medida="cm",
            data_hora=datetime(2026, 10, 15, 12),
        )
        service.repository.existe_limpeza_recente.return_value = True
        etapas = []
        service.repository.existe_limpeza_recente.side_effect = (
            lambda _: etapas.append("janela") or True
        )
        resultado_ia = SimpleNamespace(
            nivel_risco=NivelRisco.ALTO.value,
            recomendacao_limpeza="Recomendação",
        )
        resultado_ml = SimpleNamespace(nivel_risco=NivelRisco.CRITICO.value)

        with (
            patch(
                "app.services.leituras.PrevisorEntupimentoIA.analisar_e_prever",
                side_effect=lambda **_: etapas.append("multivariada") or resultado_ia,
            ),
            patch(
                "app.services.leituras.PrevisorEntupimentoML.prever",
                side_effect=lambda **_: etapas.append("ml") or resultado_ml,
            ),
        ):
            resposta = service.registrar_leitura(
                schemas.LeituraSensorCreate(
                    id_sensor=1,
                    valor_leitura=8.0,
                    unidade_medida="cm",
                )
            )

        self.assertEqual(etapas, ["janela", "multivariada", "ml"])
        self.assertEqual(resposta["nivel_risco"], NivelRisco.CRITICO.value)
        self.assertFalse(resposta["acionar_limpeza"])
        self.assertEqual(resposta["tempo_limpeza_segundos"], 0)
        service.repository.registrar_limpeza_automatica.assert_not_called()

    def test_limpeza_gravada_pelo_preditor_nao_suprime_comando_ao_firmware(self):
        service = LeituraService(MagicMock())
        service.repository.criar_leitura.return_value = SimpleNamespace(
            id_sensor=1,
            id_leitura=14,
            valor_leitura=8.0,
            unidade_medida="cm",
            data_hora=datetime(2026, 10, 15, 12),
        )
        service.repository.existe_limpeza_recente.side_effect = [False, True]
        resultado_ia = SimpleNamespace(
            nivel_risco=NivelRisco.CRITICO.value,
            recomendacao_limpeza="Limpeza urgente",
        )
        resultado_ml = SimpleNamespace(nivel_risco=NivelRisco.CRITICO.value)

        with (
            patch(
                "app.services.leituras.PrevisorEntupimentoIA.analisar_e_prever",
                return_value=resultado_ia,
            ),
            patch(
                "app.services.leituras.PrevisorEntupimentoML.prever",
                return_value=resultado_ml,
            ),
        ):
            resposta = service.registrar_leitura(
                schemas.LeituraSensorCreate(
                    id_sensor=1,
                    valor_leitura=8.0,
                    unidade_medida="cm",
                )
            )

        self.assertTrue(resposta["acionar_limpeza"])
        self.assertEqual(resposta["tempo_limpeza_segundos"], 15)
        service.repository.registrar_limpeza_automatica.assert_not_called()

    def test_falha_de_preditor_faz_rollback_e_e_propagada(self):
        repository = MagicMock()
        repository.criar_leitura.return_value = SimpleNamespace(
            id_sensor=1,
            id_leitura=13,
        )
        service = LeituraService(repository)

        with patch(
            "app.services.leituras.PrevisorEntupimentoIA.analisar_e_prever",
            side_effect=RuntimeError("falha do preditor"),
        ):
            with self.assertRaisesRegex(RuntimeError, "falha do preditor"):
                service.registrar_leitura(
                    schemas.LeituraSensorCreate(
                        id_sensor=1,
                        valor_leitura=60.0,
                        unidade_medida="cm",
                    )
                )

        repository.rollback.assert_called_once_with()


class TestLeituraRepository(unittest.TestCase):
    def test_criar_leitura_faz_rollback_se_commit_falhar(self):
        session = MagicMock()
        session.commit.side_effect = SQLAlchemyError("falha no banco")
        repository = LeituraRepository(session)

        with self.assertRaises(SQLAlchemyError):
            repository.criar_leitura(
                schemas.LeituraSensorCreate(
                    id_sensor=1,
                    valor_leitura=80.0,
                    unidade_medida="cm",
                )
            )

        session.rollback.assert_called_once_with()
        session.refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
