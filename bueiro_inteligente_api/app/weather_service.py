"""
Serviço de dados climáticos via API OpenWeatherMap.

Consome os endpoints 'weather' (dados atuais) e 'forecast' (previsão 5 dias/3h)
do plano gratuito da OpenWeatherMap. Inclui cache em memória para respeitar o
rate-limit de 60 chamadas/minuto do free tier.

Quando a API Key não está configurada ou a API está indisponível, retorna
valores de fallback (céu limpo, sem chuva) para que o restante do sistema
continue funcionando normalmente.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

from .config import (
    OPENWEATHER_API_KEY,
    OPENWEATHER_CACHE_TTL_SEGUNDOS,
    BUEIRO_LATITUDE,
    BUEIRO_LONGITUDE,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openweathermap.org/data/2.5"


# ─────────────────────────────────────────────────────────────────
# Dataclass de resultado
# ─────────────────────────────────────────────────────────────────

@dataclass
class DadosClimaticos:
    """Dados climáticos consolidados para uso pelo ai_predictor."""

    chuva_mm_h: float = 0.0
    """Precipitação acumulada na última 1h (mm)."""

    umidade_pct: float = 50.0
    """Umidade relativa do ar (%)."""

    vento_ms: float = 0.0
    """Velocidade do vento (m/s)."""

    previsao_chuva_proximas_3h_mm: float = 0.0
    """Precipitação prevista para as próximas 3 horas (mm)."""

    temperatura_c: float = 25.0
    """Temperatura atual (°C)."""

    descricao_clima: str = "Dados climáticos não disponíveis"
    """Descrição textual do clima atual."""

    disponivel: bool = False
    """Indica se os dados foram obtidos da API (True) ou são fallback (False)."""

    timestamp_consulta: float = field(default_factory=time.time)
    """Timestamp UNIX da última consulta."""


# ─────────────────────────────────────────────────────────────────
# Cache em memória (singleton)
# ─────────────────────────────────────────────────────────────────

_cache: Optional[DadosClimaticos] = None
_cache_timestamp: float = 0.0


def _cache_valido() -> bool:
    global _cache, _cache_timestamp
    if _cache is None:
        return False
    return (time.time() - _cache_timestamp) < OPENWEATHER_CACHE_TTL_SEGUNDOS


def limpar_cache() -> None:
    """Força a próxima consulta a buscar dados frescos da API."""
    global _cache, _cache_timestamp
    _cache = None
    _cache_timestamp = 0.0


# ─────────────────────────────────────────────────────────────────
# Funções internas de consumo da API
# ─────────────────────────────────────────────────────────────────

def _buscar_clima_atual(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
) -> dict | None:
    """Consulta o endpoint /weather da OpenWeatherMap."""
    if not OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY não configurada — usando fallback climático.")
        return None

    try:
        resp = requests.get(
            f"{BASE_URL}/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "pt_br",
            },
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("Erro ao consultar OpenWeatherMap /weather: %s", exc)
        return None


def _buscar_previsao(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
) -> dict | None:
    """Consulta o endpoint /forecast (previsão 5 dias / 3h) da OpenWeatherMap."""
    if not OPENWEATHER_API_KEY:
        return None

    try:
        resp = requests.get(
            f"{BASE_URL}/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "pt_br",
                "cnt": 2,  # Apenas os próximos 2 intervalos de 3h
            },
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("Erro ao consultar OpenWeatherMap /forecast: %s", exc)
        return None


def _extrair_chuva_previsao(forecast_data: dict | None) -> float:
    """Soma a precipitação prevista nos próximos intervalos de 3h."""
    if not forecast_data or "list" not in forecast_data:
        return 0.0

    total_mm = 0.0
    for item in forecast_data.get("list", []):
        rain = item.get("rain", {})
        total_mm += rain.get("3h", 0.0)
    return total_mm


# ─────────────────────────────────────────────────────────────────
# Interface pública
# ─────────────────────────────────────────────────────────────────

def obter_dados_climaticos(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
    forcar_atualizacao: bool = False,
) -> DadosClimaticos:
    """
    Retorna os dados climáticos atuais e previsão de precipitação.

    - Usa cache em memória (TTL configurável via OPENWEATHER_CACHE_TTL).
    - Se a API Key não estiver configurada ou a API estiver offline,
      retorna um DadosClimaticos com valores de fallback e disponivel=False.
    """
    global _cache, _cache_timestamp

    if not forcar_atualizacao and _cache_valido():
        return _cache  # type: ignore[return-value]

    # Tenta buscar dados da API
    clima_atual = _buscar_clima_atual(lat, lon)
    forecast = _buscar_previsao(lat, lon)

    if clima_atual is None:
        # Fallback — sistema continua funcionando sem dados climáticos
        fallback = DadosClimaticos(disponivel=False)
        _cache = fallback
        _cache_timestamp = time.time()
        return fallback

    # Extrai dados do JSON retornado pela API
    main = clima_atual.get("main", {})
    wind = clima_atual.get("wind", {})
    rain = clima_atual.get("rain", {})
    weather_list = clima_atual.get("weather", [{}])
    descricao = weather_list[0].get("description", "N/A") if weather_list else "N/A"

    resultado = DadosClimaticos(
        chuva_mm_h=rain.get("1h", 0.0),
        umidade_pct=main.get("humidity", 50.0),
        vento_ms=wind.get("speed", 0.0),
        previsao_chuva_proximas_3h_mm=_extrair_chuva_previsao(forecast),
        temperatura_c=main.get("temp", 25.0),
        descricao_clima=descricao.capitalize(),
        disponivel=True,
    )

    _cache = resultado
    _cache_timestamp = time.time()

    logger.info(
        "Dados climáticos atualizados: %s, chuva=%.1fmm/h, umidade=%d%%, previsão_3h=%.1fmm",
        resultado.descricao_clima,
        resultado.chuva_mm_h,
        resultado.umidade_pct,
        resultado.previsao_chuva_proximas_3h_mm,
    )

    return resultado


def obter_dados_climaticos_dict(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
) -> dict:
    """Versão dict dos dados climáticos — útil para endpoints REST."""
    dados = obter_dados_climaticos(lat, lon)
    return {
        "chuva_mm_h": dados.chuva_mm_h,
        "umidade_pct": dados.umidade_pct,
        "vento_ms": dados.vento_ms,
        "previsao_chuva_proximas_3h_mm": dados.previsao_chuva_proximas_3h_mm,
        "temperatura_c": dados.temperatura_c,
        "descricao_clima": dados.descricao_clima,
        "disponivel": dados.disponivel,
    }
