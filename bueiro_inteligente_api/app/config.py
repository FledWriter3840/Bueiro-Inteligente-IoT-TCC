"""
Configuração centralizada do sistema Bueiro Inteligente.
Carrega variáveis de ambiente do .env e expõe constantes globais.
"""

import os
from dotenv import load_dotenv

from .enums import NivelRisco

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# Operação e classificação de risco
# ─────────────────────────────────────────────────────────────────
LIMIAR_CRITICO_CM: float = 15.0
JANELA_LIMPEZA_MINUTOS: int = 5
PRIORIDADE_NIVEL_RISCO: dict[str, int] = {
    NivelRisco.BAIXO.value: 0,
    NivelRisco.MEDIO.value: 1,
    NivelRisco.ALTO.value: 2,
    NivelRisco.CRITICO.value: 3,
}
TEMPOS_LIMPEZA_POR_RISCO: dict[str, int] = {
    NivelRisco.BAIXO.value: 0,
    NivelRisco.MEDIO.value: 5,
    NivelRisco.ALTO.value: 10,
    "Emergência": 15,
    NivelRisco.CRITICO.value: 15,
}

# Parâmetros do modelo de árvore de decisão e do dataset sintético.
ML_N_AMOSTRAS: int = 3000
ML_RANDOM_STATE: int = 42
ML_TEST_SIZE: float = 0.2
ML_MAX_DEPTH: int = 5

# ─────────────────────────────────────────────────────────────────
# OpenWeatherMap
# ─────────────────────────────────────────────────────────────────
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_CACHE_TTL_SEGUNDOS: int = int(os.getenv("OPENWEATHER_CACHE_TTL", "60"))

# ─────────────────────────────────────────────────────────────────
# OpenTopography (Copernicus DEM GLO-30)
# ─────────────────────────────────────────────────────────────────
OPENTOPOGRAPHY_API_KEY: str = os.getenv("OPENTOPOGRAPHY_API_KEY", "")
OPENTOPOGRAPHY_DATASET: str = os.getenv("OPENTOPOGRAPHY_DATASET", "COP30")

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

# OpenStreetMap / Overpass para dados do entorno
OVERPASS_API_URL: str = os.getenv(
	"OVERPASS_API_URL",
	"https://overpass-api.de/api/interpreter",
)
OVERPASS_RAIO_METROS: int = int(os.getenv("OVERPASS_RAIO_METROS", "500"))

# ─────────────────────────────────────────────────────────────────
# Pesos do scoring ponderado (somam 1.0)
# ─────────────────────────────────────────────────────────────────
PESO_SENSOR: float = 0.30
PESO_CLIMA: float = 0.25
PESO_TEMPORAL: float = 0.10
PESO_HISTORICO_ALAGAMENTO: float = 0.15
PESO_GEOGRAFICO: float = 0.10
PESO_USO_SOLO: float = 0.10
