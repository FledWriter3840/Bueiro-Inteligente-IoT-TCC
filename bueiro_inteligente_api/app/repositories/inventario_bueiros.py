import csv
from functools import lru_cache
from io import StringIO
import re
from pathlib import Path

from pyproj import Transformer

SAC_COORDINATE_TRANSFORMER = Transformer.from_crs(
    "EPSG:31983",
    "EPSG:4326",
    always_xy=True,
)


class InventarioBueirosRepository:
    """Carrega os inventários geográficos mantidos em arquivos."""

    def __init__(self, inventario_path: Path, sac_path: Path):
        self.inventario_path = inventario_path
        self.sac_path = sac_path

    def carregar_inventario(self) -> tuple[dict, ...]:
        return _carregar_inventario(str(self.inventario_path))

    def carregar_solicitacoes_sac(self) -> tuple[dict, ...]:
        return _carregar_solicitacoes_sac(str(self.sac_path))


def _numero(valor: str | None) -> float:
    return float((valor or "").strip().replace(",", "."))


def _numero_opcional(valor: str | None) -> float | None:
    if not (valor or "").strip():
        return None
    try:
        return _numero(valor)
    except ValueError:
        return None


def _ler_texto_csv(caminho: Path) -> str:
    try:
        return caminho.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return caminho.read_text(encoding="cp1252")


@lru_cache(maxsize=4)
def _carregar_inventario(caminho: str) -> tuple[dict, ...]:
    arquivo = Path(caminho)
    if not arquivo.exists():
        return ()

    conteudo = _ler_texto_csv(arquivo)
    registros = []
    for identificador, linha in enumerate(
        csv.DictReader(StringIO(conteudo)),
        start=1,
    ):
        try:
            latitude_montante = _numero(linha.get("Latitude-montante"))
            longitude_montante = _numero(linha.get("Longitude-montante"))
            latitude_jusante = _numero(linha.get("Latitude-jusante"))
            longitude_jusante = _numero(linha.get("Longitude-jusante"))
            km = _numero(linha.get("Km"))
        except (TypeError, ValueError):
            continue

        coordenadas = (
            (latitude_montante, longitude_montante),
            (latitude_jusante, longitude_jusante),
        )
        if any(
            not (-90 <= latitude <= 90 and -180 <= longitude <= 180)
            for latitude, longitude in coordenadas
        ):
            continue

        registros.append({
            "id": identificador,
            "regional": (linha.get("Regional") or "").strip(),
            "elemento": (linha.get("Elemento") or "").strip(),
            "rodovia": (linha.get("Rodovia") or "").strip(),
            "levantamento": (linha.get("Levantamento") or "").strip(),
            "km": km,
            "extensao_m": _numero_opcional(linha.get("Extensão (m)")),
            "dimensao_m": _numero_opcional(linha.get("Dimensão (m)")),
            "tipo": (linha.get("Tipo") or "").strip(),
            "latitude_montante": latitude_montante,
            "longitude_montante": longitude_montante,
            "latitude_jusante": latitude_jusante,
            "longitude_jusante": longitude_jusante,
        })

    return tuple(registros)


@lru_cache(maxsize=4)
def _carregar_solicitacoes_sac(
    caminho: str,
) -> tuple[dict, ...]:
    arquivo = Path(caminho)
    if not arquivo.exists():
        return ()

    conteudo = _ler_texto_csv(arquivo)
    solicitacoes = []
    for linha in csv.DictReader(StringIO(conteudo)):
        geometria = (linha.get("ge_ponto") or "").strip()
        coordenadas = re.fullmatch(
            r"POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)",
            geometria,
        )
        if not coordenadas:
            continue

        try:
            longitude, latitude = SAC_COORDINATE_TRANSFORMER.transform(
                float(coordenadas.group(1)),
                float(coordenadas.group(2)),
            )
        except (ValueError, TypeError):
            continue

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue

        solicitacoes.append({
            "id": (linha.get("cd_identificador") or linha.get("FID") or "").strip(),
            "latitude": latitude,
            "longitude": longitude,
            "logradouro": (linha.get("nm_logradouro") or "").strip(),
            "numero": (linha.get("nr_logradouro") or "").strip(),
            "data_abertura": (linha.get("dt_abertura") or "").strip(),
            "data_parecer": (linha.get("dt_parecer") or "").strip(),
            "situacao": (linha.get("tx_situacao_solicitacao") or "").strip().upper(),
            "canal": (linha.get("tx_canal_atendimento") or "").strip(),
            "servico": (linha.get("dc_servico") or "").strip(),
        })

    return tuple(solicitacoes)
