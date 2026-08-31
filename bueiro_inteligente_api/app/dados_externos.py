"""
Providers de dados externos — esqueletos prontos para receber datasets reais.

Três providers preparados para integração futura:
1. HistoricoAlagamentosProvider  — CGE SP / Defesa Civil
2. DadosGeograficosProvider      — GeoSampa (topografia)
3. UsoDeSoloProvider             — Classificação do entorno

Cada provider:
- Tem um método `carregar_de_csv()` / `carregar_de_json()` para importar dados
- Retorna valores DEFAULT CONSERVADORES quando os datasets não estão disponíveis
- Expõe `disponivel` para indicar se dados reais foram carregados
"""

from __future__ import annotations

import csv
import json
import math
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import (
    DADOS_ALAGAMENTOS_PATH,
    DADOS_GEOGRAFICOS_PATH,
    DADOS_USO_SOLO_PATH,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 1. HISTÓRICO DE ALAGAMENTOS (CGE SP / Defesa Civil)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PontoAlagamento:
    """Um ponto histórico de alagamento/enchente."""
    latitude: float
    longitude: float
    frequencia_anual: int = 1
    """Quantas vezes alagou por ano nesse ponto."""
    severidade_media: float = 0.5
    """Severidade média (0.0 a 1.0): 0=leve, 1=grave."""
    descricao: str = ""


@dataclass
class ScoreAlagamentoHistorico:
    """Score de risco baseado no histórico de alagamentos próximos."""
    score: float = 0.3
    """Score de 0.0 a 1.0 (0=sem histórico, 1=ponto muito recorrente)."""
    pontos_proximos: int = 0
    """Quantidade de pontos de alagamento num raio de 500m."""
    frequencia_total: int = 0
    """Soma das frequências anuais dos pontos próximos."""
    disponivel: bool = False
    """True se o dataset de alagamentos foi carregado."""


class HistoricoAlagamentosProvider:
    """
    Provider de dados históricos de alagamento.

    Quando o dataset estiver disponível (CSV da CGE SP ou Defesa Civil),
    carregue com `carregar_de_csv()`. O formato esperado do CSV é:

    latitude,longitude,frequencia_anual,severidade_media,descricao
    -23.5505,-46.6333,12,0.8,"Praça da Sé"
    -23.5489,-46.6388,8,0.6,"Vale do Anhangabaú"
    """

    def __init__(self):
        self._pontos: list[PontoAlagamento] = []
        self._carregado: bool = False

    @property
    def disponivel(self) -> bool:
        return self._carregado

    def carregar_de_csv(self, caminho: str | Path) -> int:
        """
        Carrega pontos de alagamento de um arquivo CSV.

        Retorna o número de registros carregados.
        Formato esperado: latitude,longitude,frequencia_anual,severidade_media,descricao
        """
        caminho = Path(caminho)
        if not caminho.exists():
            logger.warning("Arquivo de alagamentos não encontrado: %s", caminho)
            return 0

        self._pontos.clear()
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._pontos.append(PontoAlagamento(
                        latitude=float(row.get("latitude", 0)),
                        longitude=float(row.get("longitude", 0)),
                        frequencia_anual=int(row.get("frequencia_anual", 1)),
                        severidade_media=float(row.get("severidade_media", 0.5)),
                        descricao=row.get("descricao", ""),
                    ))
            self._carregado = True
            logger.info("Carregados %d pontos de alagamento de %s", len(self._pontos), caminho)
            return len(self._pontos)
        except Exception as exc:
            logger.error("Erro ao carregar CSV de alagamentos: %s", exc)
            return 0

    def carregar_de_json(self, caminho: str | Path) -> int:
        """
        Carrega pontos de alagamento de um arquivo JSON.

        Formato esperado:
        [
            {"latitude": -23.55, "longitude": -46.63, "frequencia_anual": 12, ...},
            ...
        ]
        """
        caminho = Path(caminho)
        if not caminho.exists():
            logger.warning("Arquivo JSON de alagamentos não encontrado: %s", caminho)
            return 0

        self._pontos.clear()
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)

            for item in dados:
                self._pontos.append(PontoAlagamento(
                    latitude=float(item.get("latitude", 0)),
                    longitude=float(item.get("longitude", 0)),
                    frequencia_anual=int(item.get("frequencia_anual", 1)),
                    severidade_media=float(item.get("severidade_media", 0.5)),
                    descricao=item.get("descricao", ""),
                ))
            self._carregado = True
            logger.info("Carregados %d pontos de alagamento de %s", len(self._pontos), caminho)
            return len(self._pontos)
        except Exception as exc:
            logger.error("Erro ao carregar JSON de alagamentos: %s", exc)
            return 0

    def obter_score_risco_local(
        self,
        lat: float,
        lon: float,
        raio_metros: float = 500.0,
    ) -> ScoreAlagamentoHistorico:
        """
        Calcula o score de risco baseado na proximidade com pontos de alagamento.

        Se o dataset não foi carregado, retorna score DEFAULT de 0.3
        (conservador — assume risco moderado por precaução).
        """
        if not self._carregado:
            return ScoreAlagamentoHistorico(
                score=0.3,
                disponivel=False,
            )

        pontos_proximos = []
        for ponto in self._pontos:
            dist = _haversine_metros(lat, lon, ponto.latitude, ponto.longitude)
            if dist <= raio_metros:
                pontos_proximos.append(ponto)

        if not pontos_proximos:
            return ScoreAlagamentoHistorico(
                score=0.05,
                pontos_proximos=0,
                frequencia_total=0,
                disponivel=True,
            )

        freq_total = sum(p.frequencia_anual for p in pontos_proximos)
        sev_media = sum(p.severidade_media for p in pontos_proximos) / len(pontos_proximos)

        # Score: combinação de frequência e severidade, normalizado
        score_freq = min(1.0, freq_total / 20.0)  # 20+ ocorrências/ano = score máximo
        score = 0.6 * score_freq + 0.4 * sev_media
        score = max(0.0, min(1.0, score))

        return ScoreAlagamentoHistorico(
            score=round(score, 3),
            pontos_proximos=len(pontos_proximos),
            frequencia_total=freq_total,
            disponivel=True,
        )


# ═══════════════════════════════════════════════════════════════════
# 2. DADOS GEOGRÁFICOS / TOPOGRÁFICOS (GeoSampa)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PerfilTopografico:
    """Perfil topográfico de uma localização."""
    altitude_metros: float = 760.0
    """Altitude relativa em metros (default: altitude média de SP)."""
    eh_fundo_de_vale: bool = False
    """True se a localização está em um fundo de vale."""
    classificacao_risco: str = "Não classificado"
    """Classificação de risco geológico/hidrológico: Baixo/Médio/Alto/Muito Alto."""
    declividade_pct: float = 0.0
    """Declividade do terreno (%). Negativa = descida em direção ao ponto."""
    disponivel: bool = False


class DadosGeograficosProvider:
    """
    Provider de dados geográficos/topográficos do GeoSampa.

    Quando o dataset estiver disponível, carregue com `carregar_de_csv()`
    ou `carregar_de_geojson()`. Formato CSV esperado:

    latitude,longitude,altitude_m,fundo_de_vale,classificacao_risco,declividade_pct
    -23.5505,-46.6333,740,1,Alto,-2.5
    """

    def __init__(self):
        self._pontos: list[dict] = []
        self._carregado: bool = False

    @property
    def disponivel(self) -> bool:
        return self._carregado

    def carregar_de_csv(self, caminho: str | Path) -> int:
        """Carrega dados topográficos de CSV."""
        caminho = Path(caminho)
        if not caminho.exists():
            logger.warning("Arquivo geográfico não encontrado: %s", caminho)
            return 0

        self._pontos.clear()
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._pontos.append({
                        "latitude": float(row.get("latitude", 0)),
                        "longitude": float(row.get("longitude", 0)),
                        "altitude_m": float(row.get("altitude_m", 760)),
                        "fundo_de_vale": row.get("fundo_de_vale", "0") in ("1", "true", "True", "sim"),
                        "classificacao_risco": row.get("classificacao_risco", "Não classificado"),
                        "declividade_pct": float(row.get("declividade_pct", 0)),
                    })
            self._carregado = True
            logger.info("Carregados %d pontos geográficos de %s", len(self._pontos), caminho)
            return len(self._pontos)
        except Exception as exc:
            logger.error("Erro ao carregar CSV geográfico: %s", exc)
            return 0

    def carregar_de_geojson(self, caminho: str | Path) -> int:
        """
        Carrega dados de um GeoJSON (formato FeatureCollection).

        Espera propriedades: altitude_m, fundo_de_vale, classificacao_risco, declividade_pct
        """
        caminho = Path(caminho)
        if not caminho.exists():
            logger.warning("Arquivo GeoJSON não encontrado: %s", caminho)
            return 0

        self._pontos.clear()
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                geojson = json.load(f)

            for feature in geojson.get("features", []):
                coords = feature.get("geometry", {}).get("coordinates", [0, 0])
                props = feature.get("properties", {})
                self._pontos.append({
                    "latitude": coords[1] if len(coords) >= 2 else 0,
                    "longitude": coords[0] if len(coords) >= 1 else 0,
                    "altitude_m": float(props.get("altitude_m", 760)),
                    "fundo_de_vale": props.get("fundo_de_vale", False),
                    "classificacao_risco": props.get("classificacao_risco", "Não classificado"),
                    "declividade_pct": float(props.get("declividade_pct", 0)),
                })
            self._carregado = True
            logger.info("Carregados %d pontos de GeoJSON: %s", len(self._pontos), caminho)
            return len(self._pontos)
        except Exception as exc:
            logger.error("Erro ao carregar GeoJSON: %s", exc)
            return 0

    def obter_perfil_topografico(self, lat: float, lon: float) -> PerfilTopografico:
        """
        Busca o perfil topográfico do ponto mais próximo.

        Se o dataset não foi carregado, retorna perfil DEFAULT conservador
        (assume fundo de vale = False, risco não classificado).
        """
        if not self._carregado or not self._pontos:
            return PerfilTopografico(disponivel=False)

        # Encontra o ponto mais próximo
        melhor = None
        melhor_dist = float("inf")
        for ponto in self._pontos:
            dist = _haversine_metros(lat, lon, ponto["latitude"], ponto["longitude"])
            if dist < melhor_dist:
                melhor_dist = dist
                melhor = ponto

        if melhor is None or melhor_dist > 1000:
            # Nenhum ponto próximo o suficiente (> 1km)
            return PerfilTopografico(disponivel=True)

        return PerfilTopografico(
            altitude_metros=melhor["altitude_m"],
            eh_fundo_de_vale=melhor["fundo_de_vale"],
            classificacao_risco=melhor["classificacao_risco"],
            declividade_pct=melhor["declividade_pct"],
            disponivel=True,
        )


# ═══════════════════════════════════════════════════════════════════
# 3. DADOS DE USO DO SOLO / ENTORNO
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PerfilUsoSolo:
    """Perfil de uso do solo e entorno do bueiro."""
    tipo_via: str = "Não classificado"
    """Tipo da via: Comercial / Residencial / Industrial / Mista."""
    proximidade_feira_m: float | None = None
    """Distância em metros até a feira mais próxima (None = desconhecido)."""
    proximidade_parque_m: float | None = None
    """Distância em metros até o parque mais próximo (None = desconhecido)."""
    indice_impermeabilizacao: float = 0.7
    """0.0 (permeável, muito verde) a 1.0 (totalmente impermeável, asfalto)."""
    zona_comercial_intensa: bool = False
    """True se estiver em região de alto movimento comercial (mais resíduos)."""
    disponivel: bool = False


class UsoDeSoloProvider:
    """
    Provider de dados de uso do solo / entorno.

    Carregue a configuração do bueiro com `carregar_configuracao()`.
    Formato JSON esperado:

    {
        "tipo_via": "Comercial",
        "proximidade_feira_m": 150,
        "proximidade_parque_m": 800,
        "indice_impermeabilizacao": 0.85,
        "zona_comercial_intensa": true
    }
    """

    def __init__(self):
        self._perfil: PerfilUsoSolo = PerfilUsoSolo()
        self._carregado: bool = False

    @property
    def disponivel(self) -> bool:
        return self._carregado

    def carregar_configuracao(self, caminho: str | Path) -> bool:
        """Carrega configuração de uso do solo de um arquivo JSON."""
        caminho = Path(caminho)
        if not caminho.exists():
            logger.warning("Arquivo de uso do solo não encontrado: %s", caminho)
            return False

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)

            self._perfil = PerfilUsoSolo(
                tipo_via=dados.get("tipo_via", "Não classificado"),
                proximidade_feira_m=dados.get("proximidade_feira_m"),
                proximidade_parque_m=dados.get("proximidade_parque_m"),
                indice_impermeabilizacao=float(dados.get("indice_impermeabilizacao", 0.7)),
                zona_comercial_intensa=dados.get("zona_comercial_intensa", False),
                disponivel=True,
            )
            self._carregado = True
            logger.info("Perfil de uso do solo carregado: tipo_via=%s", self._perfil.tipo_via)
            return True
        except Exception as exc:
            logger.error("Erro ao carregar configuração de uso do solo: %s", exc)
            return False

    def configurar_manualmente(
        self,
        tipo_via: str = "Não classificado",
        proximidade_feira_m: float | None = None,
        proximidade_parque_m: float | None = None,
        indice_impermeabilizacao: float = 0.7,
        zona_comercial_intensa: bool = False,
    ) -> None:
        """Configura o perfil de uso do solo programaticamente (sem arquivo)."""
        self._perfil = PerfilUsoSolo(
            tipo_via=tipo_via,
            proximidade_feira_m=proximidade_feira_m,
            proximidade_parque_m=proximidade_parque_m,
            indice_impermeabilizacao=indice_impermeabilizacao,
            zona_comercial_intensa=zona_comercial_intensa,
            disponivel=True,
        )
        self._carregado = True

    def obter_perfil(self) -> PerfilUsoSolo:
        """Retorna o perfil de uso do solo. Default conservador se não carregado."""
        return self._perfil


# ═══════════════════════════════════════════════════════════════════
# UTILITÁRIO: Fórmula de Haversine
# ═══════════════════════════════════════════════════════════════════

def _haversine_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância em metros entre dois pontos geográficos."""
    R = 6_371_000  # Raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ═══════════════════════════════════════════════════════════════════
# Instâncias Singleton (carregadas uma vez na inicialização)
# ═══════════════════════════════════════════════════════════════════

historico_alagamentos = HistoricoAlagamentosProvider()
dados_geograficos = DadosGeograficosProvider()
uso_do_solo = UsoDeSoloProvider()


def inicializar_dados_externos() -> dict[str, bool]:
    """
    Tenta carregar todos os datasets externos configurados via variáveis de ambiente.
    Deve ser chamado na inicialização da aplicação (main.py).

    Retorna um dict indicando quais fontes foram carregadas com sucesso.
    """
    status: dict[str, bool] = {}

    if DADOS_ALAGAMENTOS_PATH:
        path = Path(DADOS_ALAGAMENTOS_PATH)
        if path.suffix == ".json":
            n = historico_alagamentos.carregar_de_json(path)
        else:
            n = historico_alagamentos.carregar_de_csv(path)
        status["historico_alagamentos"] = n > 0
    else:
        status["historico_alagamentos"] = False

    if DADOS_GEOGRAFICOS_PATH:
        path = Path(DADOS_GEOGRAFICOS_PATH)
        if path.suffix == ".geojson":
            n = dados_geograficos.carregar_de_geojson(path)
        else:
            n = dados_geograficos.carregar_de_csv(path)
        status["dados_geograficos"] = n > 0
    else:
        status["dados_geograficos"] = False

    if DADOS_USO_SOLO_PATH:
        status["uso_do_solo"] = uso_do_solo.carregar_configuracao(DADOS_USO_SOLO_PATH)
    else:
        status["uso_do_solo"] = False

    logger.info("Dados externos inicializados: %s", status)
    return status
