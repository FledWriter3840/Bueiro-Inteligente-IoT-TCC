import unittest

from app.enums import NivelRisco
from app.schemas import CenarioSimulacaoRequest
from app.services.ia import simular_cenario_chuva


class TestIAService(unittest.TestCase):
    def test_simulacao_preserva_formato_e_classificacao_por_risco(self):
        resultado = simular_cenario_chuva(
            CenarioSimulacaoRequest(
                distancia_inicial_cm=16,
                velocidade_subida_cm_min=1,
                minutos_simulacao=2,
            )
        )

        self.assertEqual(
            resultado["cenario"],
            {
                "distancia_inicial_cm": 16.0,
                "velocidade_subida_cm_min": 1.0,
                "tempo_total_simulado_min": 2,
            },
        )
        self.assertEqual(
            [item["nivel_risco"] for item in resultado["projecoes"]],
            [
                NivelRisco.ALTO.value,
                NivelRisco.CRITICO.value,
                NivelRisco.CRITICO.value,
            ],
        )
        self.assertEqual(
            [item["probabilidade_alagamento"] for item in resultado["projecoes"]],
            [0.75, 0.95, 0.95],
        )


if __name__ == "__main__":
    unittest.main()
