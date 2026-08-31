"""
Configuração centralizada do sistema Bueiro Inteligente.
Carrega variáveis de ambiente do .env e expõe constantes globais.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# OpenWeatherMap
# ─────────────────────────────────────────────────────────────────
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_CACHE_TTL_SEGUNDOS: int = int(os.getenv("OPENWEATHER_CACHE_TTL", "600"))

# ─────────────────────────────────────────────────────────────────
# Localização padrão do bueiro (São Paulo, SP)
# ─────────────────────────────────────────────────────────────────
BUEIRO_LATITUDE: float = float(os.getenv("BUEIRO_LATITUDE", "-23.5505"))
BUEIRO_LONGITUDE: float = float(os.getenv("BUEIRO_LONGITUDE", "-46.6333"))

# ─────────────────────────────────────────────────────────────────
# Caminhos para datasets externos (esqueleto — preencher quando disponíveis)
# ─────────────────────────────────────────────────────────────────
DADOS_ALAGAMENTOS_PATH: str = os.getenv("DADOS_ALAGAMENTOS_PATH", "")
DADOS_GEOGRAFICOS_PATH: str = os.getenv("DADOS_GEOGRAFICOS_PATH", "")
DADOS_USO_SOLO_PATH: str = os.getenv("DADOS_USO_SOLO_PATH", "")

# ─────────────────────────────────────────────────────────────────
# Pesos do scoring ponderado (somam 1.0)
# ─────────────────────────────────────────────────────────────────
PESO_SENSOR: float = 0.30
PESO_CLIMA: float = 0.25
PESO_TEMPORAL: float = 0.10
PESO_HISTORICO_ALAGAMENTO: float = 0.15
PESO_GEOGRAFICO: float = 0.10
PESO_USO_SOLO: float = 0.10
