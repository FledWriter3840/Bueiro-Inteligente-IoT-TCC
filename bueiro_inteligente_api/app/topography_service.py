"""
Serviço de Topografia via API OpenTopography (Copernicus DEM GLO-30).

Consulta a elevação e a morfologia do terreno usando o modelo digital de superfície
Copernicus Global 30m (COP30) através da API REST do OpenTopography.

Recursos:
- Consulta de cota altimétrica precisa (metros acima do nível do mar)
- Detecção automática de depressões e fundo de vale (convergência de escoamento)
- Cálculo de declividade local (%) para estimar risco de enxurrada e acúmulo
- Sistema de cache persistente em arquivo JSON para respeitar a cota diária gratuita
- Fallback automático caso a chave não esteja configurada ou o serviço esteja indisponível
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

from .config import (
    OPENTOPOGRAPHY_API_KEY,
    OPENTOPOGRAPHY_DATASET,
    BUEIRO_LATITUDE,
    BUEIRO_LONGITUDE,
)

logger = logging.getLogger(__name__)

API_URL = "https://portal.opentopography.org/API/v1/elevation"
CACHE_FILE = Path(__file__).resolve().parent.parent / "topografia_cache.json"


# ─────────────────────────────────────────────────────────────────
# Dataclass do Perfil Topográfico (Consistente com dados_externos)
# ─────────────────────────────────────────────────────────────────

@dataclass
class PerfilTopograficoAPI:
    """Perfil topográfico detalhado obtido via Copernicus DEM GLO-30."""
    altitude_metros: float = 760.0
    """Altitude em metros acima do nível do mar."""

    eh_fundo_de_vale: bool = False
    """True se a localização é uma depressão/fundo de vale onde a água acumula."""

    classificacao_risco: str = "Não classificado"
    """Classificação: Baixo, Médio, Alto, Muito Alto."""

    declividade_pct: float = 0.0
    """Declividade do terreno (%): negativa se a água escorre em direção ao ponto."""

    dataset_origem: str = "Copernicus DEM GLO-30 (COP30)"
    """Nome do dataset consultado."""

    disponivel: bool = False
    """True se os dados foram obtidos da API, False se usou fallback."""

    detalhes_analise: str = ""
    """Explicação técnica da análise geomorfológica para relatórios e TCC."""


# ─────────────────────────────────────────────────────────────────
# Serviço de Topografia com Cache Persistente
# ─────────────────────────────────────────────────────────────────

class TopografiaService:
    """Gerencia consultas ao OpenTopography com cache em memória e em disco."""

    def __init__(self):
        self._cache: dict[str, float] = {}
        self._carregar_cache_disco()

    def _gerar_chave_cache(self, lat: float, lon: float, dataset: str) -> str:
        """Chave com 5 casas decimais (~1.1 metro de precisão)."""
        return f"{round(lat, 5)}_{round(lon, 5)}_{dataset}"

    def _carregar_cache_disco(self) -> None:
        """Carrega cache prévio salvo em JSON para evitar consumir cota diária."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info("Cache de topografia carregado: %d pontos em disco", len(self._cache))
            except Exception as exc:
                logger.warning("Falha ao ler cache de topografia do disco: %s", exc)

    def _salvar_cache_disco(self) -> None:
        """Persiste o cache no disco."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as exc:
            logger.warning("Falha ao salvar cache de topografia em disco: %s", exc)

    def consultar_elevacao(
        self,
        lat: float = BUEIRO_LATITUDE,
        lon: float = BUEIRO_LONGITUDE,
        dataset: str = OPENTOPOGRAPHY_DATASET,
    ) -> Optional[float]:
        """
        Consulta a elevação pontual (altitude em metros) para uma coordenada.
        Utiliza cache prioritariamente.
        """
        if not OPENTOPOGRAPHY_API_KEY:
            logger.debug("OPENTOPOGRAPHY_API_KEY não configurada.")
            return None

        chave = self._gerar_chave_cache(lat, lon, dataset)
        if chave in self._cache:
            return self._cache[chave]

        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "dataset": dataset,
                "API_Key": OPENTOPOGRAPHY_API_KEY,
            }
            resp = requests.get(API_URL, params=params, timeout=10)

            if resp.status_code == 200:
                dados = resp.json()
                elev = dados.get("Elevation") if dados.get("Elevation") is not None else dados.get("elevation")
                if elev is not None:
                    elev_float = float(elev)
                    self._cache[chave] = elev_float
                    self._salvar_cache_disco()
                    logger.info(
                        "Elevação obtida via OpenTopography: %.2fm para (%.5f, %.5f)",
                        elev_float, lat, lon
                    )
                    return elev_float
            else:
                logger.warning(
                    "OpenTopography API retornou status %d: %s",
                    resp.status_code, resp.text[:200]
                )
                return None
        except Exception as exc:
            logger.error("Erro na requisição para OpenTopography: %s", exc)
            return None

    def obter_perfil_completo(
        self,
        lat: float = BUEIRO_LATITUDE,
        lon: float = BUEIRO_LONGITUDE,
    ) -> PerfilTopograficoAPI:
        """
        Gera uma análise morfológica completa do relevo no entorno do bueiro.

        Avalia:
        1. Altitude do bueiro (centro)
        2. Elevação dos 4 pontos cardeais (+/- 60m)
        3. Identificação de bacia/fundo de vale (se o centro é mais baixo que os vizinhos)
        4. Gradiente e declividade média (%)
        """
        if not OPENTOPOGRAPHY_API_KEY:
            return PerfilTopograficoAPI(
                altitude_metros=760.0,
                eh_fundo_de_vale=False,
                classificacao_risco="Conservador (API Key não configurada)",
                declividade_pct=0.0,
                disponivel=False,
                detalhes_analise="Chave OPENTOPOGRAPHY_API_KEY não configurada no .env. Usando parâmetros padrão seguros.",
            )

        # 1. Ponto Central (bueiro)
        alt_centro = self.consultar_elevacao(lat, lon)
        if alt_centro is None:
            return PerfilTopograficoAPI(
                altitude_metros=760.0,
                eh_fundo_de_vale=False,
                classificacao_risco="Indisponível (Falha na consulta)",
                declividade_pct=0.0,
                disponivel=False,
                detalhes_analise="Não foi possível consultar a API OpenTopography. Usando fallback seguro.",
            )

        # 2. Amostragem em Cruz (+/- 0.0006 graus ~ 66 metros, resolução ideal para COP30)
        delta = 0.0006
        alt_norte = self.consultar_elevacao(lat + delta, lon)
        alt_sul = self.consultar_elevacao(lat - delta, lon)
        alt_leste = self.consultar_elevacao(lat, lon + delta)
        alt_oeste = self.consultar_elevacao(lat, lon - delta)

        vizinhos = [v for v in [alt_norte, alt_sul, alt_leste, alt_oeste] if v is not None]

        # 3. Análise Geomórfica
        if len(vizinhos) >= 2:
            media_vizinhos = sum(vizinhos) / len(vizinhos)
            diferenca_cota = alt_centro - media_vizinhos

            # Se o centro é inferior aos vizinhos, o bueiro está numa concavidade/fundo de vale
            eh_fundo_de_vale = diferenca_cota < -0.35

            # Declividade estimada: gradiente entre norte-sul e leste-oeste
            dist_metros = 132.0
            grad_ns = ((alt_norte - alt_sul) / dist_metros * 100.0) if (alt_norte and alt_sul) else 0.0
            grad_eo = ((alt_leste - alt_oeste) / dist_metros * 100.0) if (alt_leste and alt_oeste) else 0.0
            declividade = math.sqrt(grad_ns ** 2 + grad_eo ** 2)

            # Sinal negativo se a água desce convergindo para o bueiro
            if eh_fundo_de_vale:
                declividade_pct = -abs(declividade)
            else:
                declividade_pct = round(declividade, 2)
        else:
            # Fallback regional de São Paulo se vizinhos não puderem ser consultados
            # Na RMSP, cotas abaixo de 735m correspondem às várzeas do Tietê, Pinheiros e Tamanduateí
            eh_fundo_de_vale = alt_centro <= 735.0
            declividade_pct = -1.5 if eh_fundo_de_vale else 1.0

        # 4. Classificação de Risco Hidráulico/Topográfico
        if eh_fundo_de_vale and abs(declividade_pct) < 2.0:
            classificacao = "Muito Alto"
            detalhes = f"Fundo de vale com drenagem lenta (declividade suave {declividade_pct:.1f}%). Água converge e tende a acumular."
        elif eh_fundo_de_vale:
            classificacao = "Alto"
            detalhes = f"Ponto de convergência hidrológica (fundo de vale), cota {alt_centro:.1f}m."
        elif abs(declividade_pct) > 8.0:
            classificacao = "Alto"
            detalhes = f"Declividade acentuada ({declividade_pct:.1f}%). Risco elevado de enxurrada rápida com arraste de detritos para a boca de lobo."
        elif abs(declividade_pct) > 3.0:
            classificacao = "Médio"
            detalhes = f"Declividade moderada ({declividade_pct:.1f}%). Escoamento superficial ativo."
        else:
            classificacao = "Baixo"
            detalhes = f"Terreno plano em cota estável ({alt_centro:.1f}m)."

        return PerfilTopograficoAPI(
            altitude_metros=round(alt_centro, 1),
            eh_fundo_de_vale=eh_fundo_de_vale,
            classificacao_risco=classificacao,
            declividade_pct=round(declividade_pct, 2),
            dataset_origem=f"OpenTopography ({OPENTOPOGRAPHY_DATASET})",
            disponivel=True,
            detalhes_analise=detalhes,
        )


# Singleton do serviço
topografia_service = TopografiaService()


def obter_perfil_topografico_atual(
    lat: float = BUEIRO_LATITUDE,
    lon: float = BUEIRO_LONGITUDE,
) -> PerfilTopograficoAPI:
    """Função utilitária pública para obter a topografia."""
    return topografia_service.obter_perfil_completo(lat, lon)
