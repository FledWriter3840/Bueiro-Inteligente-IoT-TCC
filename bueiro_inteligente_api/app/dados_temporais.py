"""
Extração de features temporais e sazonais para o ai_predictor.

Todas as features são derivadas de datetime do Python — sem dependência
externa de APIs ou datasets. Inclui feriados nacionais e municipais de
São Paulo (hardcoded + configurável).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date


# ─────────────────────────────────────────────────────────────────
# Feriados nacionais fixos + feriados municipais de São Paulo
# Formato: (mês, dia)
# Feriados móveis (Carnaval, Corpus Christi, Sexta-feira Santa)
# são aproximados — para precisão total, usar biblioteca holidays.
# ─────────────────────────────────────────────────────────────────

FERIADOS_FIXOS: set[tuple[int, int]] = {
    (1, 1),    # Confraternização Universal
    (1, 25),   # Aniversário de São Paulo (municipal)
    (4, 21),   # Tiradentes
    (5, 1),    # Dia do Trabalho
    (7, 9),    # Revolução Constitucionalista (estadual SP)
    (9, 7),    # Independência do Brasil
    (10, 12),  # N. Sra. Aparecida
    (11, 2),   # Finados
    (11, 15),  # Proclamação da República
    (11, 20),  # Consciência Negra (municipal SP)
    (12, 25),  # Natal
}

# Datas aproximadas de feriados móveis para anos recentes/próximos
# (Carnaval terça, Sexta-feira Santa, Corpus Christi)
# Adicionar mais anos conforme necessário
FERIADOS_MOVEIS: set[tuple[int, int, int]] = {
    # 2025
    (2025, 3, 4),   # Carnaval
    (2025, 4, 18),  # Sexta-feira Santa
    (2025, 6, 19),  # Corpus Christi
    # 2026
    (2026, 2, 17),  # Carnaval
    (2026, 4, 3),   # Sexta-feira Santa
    (2026, 6, 4),   # Corpus Christi
    # 2027
    (2027, 2, 9),   # Carnaval
    (2027, 3, 26),  # Sexta-feira Santa
    (2027, 5, 27),  # Corpus Christi
}


# ─────────────────────────────────────────────────────────────────
# Dataclass de resultado
# ─────────────────────────────────────────────────────────────────

@dataclass
class DadosTemporais:
    """Features temporais/sazonais extraídas do momento atual."""

    hora_do_dia: int
    """Hora do dia (0-23)."""

    dia_da_semana: int
    """Dia da semana (0=segunda, 6=domingo)."""

    estacao_do_ano: str
    """Estação do ano no hemisfério sul (Verão/Outono/Inverno/Primavera)."""

    eh_horario_pico: bool
    """Verdadeiro se estiver em horário de pico (7-9h ou 17-19h)."""

    eh_feriado: bool
    """Verdadeiro se for feriado nacional ou municipal de SP."""

    eh_fim_de_semana: bool
    """Verdadeiro se for sábado ou domingo."""

    periodo_chuvoso: bool
    """Verdadeiro se estiver no período chuvoso de SP (outubro a março)."""

    mes: int
    """Mês atual (1-12)."""

    periodo_do_dia: str
    """Madrugada / Manhã / Tarde / Noite."""


# ─────────────────────────────────────────────────────────────────
# Funções auxiliares
# ─────────────────────────────────────────────────────────────────

def _estacao_hemisferio_sul(mes: int, dia: int) -> str:
    """Retorna a estação do ano para o hemisfério sul com base no mês/dia."""
    if (mes == 12 and dia >= 21) or (1 <= mes <= 2) or (mes == 3 and dia < 20):
        return "Verão"
    elif (mes == 3 and dia >= 20) or (4 <= mes <= 5) or (mes == 6 and dia < 21):
        return "Outono"
    elif (mes == 6 and dia >= 21) or (7 <= mes <= 8) or (mes == 9 and dia < 22):
        return "Inverno"
    else:
        return "Primavera"


def _eh_feriado(dt: datetime) -> bool:
    """Verifica se a data é um feriado fixo ou móvel cadastrado."""
    # Feriados fixos (mês, dia)
    if (dt.month, dt.day) in FERIADOS_FIXOS:
        return True
    # Feriados móveis (ano, mês, dia)
    if (dt.year, dt.month, dt.day) in FERIADOS_MOVEIS:
        return True
    return False


def _periodo_do_dia(hora: int) -> str:
    """Classifica o período do dia pela hora."""
    if 0 <= hora < 6:
        return "Madrugada"
    elif 6 <= hora < 12:
        return "Manhã"
    elif 12 <= hora < 18:
        return "Tarde"
    else:
        return "Noite"


def _eh_periodo_chuvoso(mes: int) -> bool:
    """Outubro a Março é o período chuvoso na região de São Paulo."""
    return mes >= 10 or mes <= 3


# ─────────────────────────────────────────────────────────────────
# Interface pública
# ─────────────────────────────────────────────────────────────────

def extrair_dados_temporais(dt: datetime | None = None) -> DadosTemporais:
    """
    Extrai todas as features temporais/sazonais de um datetime.

    Args:
        dt: Datetime de referência. Se None, usa datetime.now().

    Returns:
        DadosTemporais preenchido com todas as features.
    """
    if dt is None:
        dt = datetime.now()

    hora = dt.hour
    dia_semana = dt.weekday()  # 0=segunda, 6=domingo

    return DadosTemporais(
        hora_do_dia=hora,
        dia_da_semana=dia_semana,
        estacao_do_ano=_estacao_hemisferio_sul(dt.month, dt.day),
        eh_horario_pico=(7 <= hora <= 9) or (17 <= hora <= 19),
        eh_feriado=_eh_feriado(dt),
        eh_fim_de_semana=dia_semana >= 5,
        periodo_chuvoso=_eh_periodo_chuvoso(dt.month),
        mes=dt.month,
        periodo_do_dia=_periodo_do_dia(hora),
    )
