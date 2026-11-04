import math

from ..config import BUEIRO_PROFUNDIDADE_CM


def calcular_nivel_percentual(valor_leitura: float, unidade_medida: str) -> float:
    """Converte a distância do ultrassônico em nível indicativo de 0 a 100%."""
    if not math.isfinite(valor_leitura):
        raise ValueError("A leitura do sensor precisa ser um número finito.")

    if unidade_medida.strip().lower() in {"%", "percentual", "percent"}:
        if not 0 <= valor_leitura <= 100:
            raise ValueError("Leituras percentuais devem estar entre 0 e 100.")
        return round(valor_leitura, 1)

    if BUEIRO_PROFUNDIDADE_CM <= 0:
        raise ValueError("BUEIRO_PROFUNDIDADE_CM precisa ser maior que zero.")

    nivel = 100 * (1 - valor_leitura / BUEIRO_PROFUNDIDADE_CM)
    return round(min(100.0, max(0.0, nivel)), 1)


def calcular_status_bueiro(nivel: float) -> str:
    """Classifica o nível conforme os limites definidos para o app móvel."""
    if not math.isfinite(nivel) or not 0 <= nivel <= 100:
        raise ValueError("O nível do bueiro deve estar entre 0 e 100.")
    if nivel >= 80:
        return "critico"
    if nivel >= 50:
        return "atencao"
    return "livre"
