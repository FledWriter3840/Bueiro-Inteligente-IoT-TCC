import csv
import json
from functools import lru_cache
from io import StringIO
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pyproj import Transformer

router = APIRouter(prefix="/bueiros", tags=["Bueiros"])
CSV_PATH = Path(__file__).resolve().parents[2] / "datasets_exemplo" / "bueiros.csv"
SAC_CSV_PATH = Path(__file__).resolve().parents[2] / "datasets_exemplo" / "sac_limpeza_bueiro.csv"
ADICOES_PATH = Path(__file__).resolve().parents[2] / "datasets_exemplo" / "bueiros_adicionados.json"
SAC_COORDINATE_TRANSFORMER = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)


class NovoBueiro(BaseModel):
    regional: str = Field(min_length=1, max_length=80)
    elemento: str = Field(default="Bueiro", min_length=1, max_length=80)
    rodovia: str = Field(min_length=1, max_length=80)
    levantamento: str = Field(min_length=1, max_length=20)
    km: float = Field(ge=0)
    extensao_m: float | None = Field(default=None, ge=0)
    dimensao_m: float | None = Field(default=None, ge=0)
    tipo: str = Field(min_length=1, max_length=160)
    latitude_montante: float = Field(ge=-90, le=90)
    longitude_montante: float = Field(ge=-180, le=180)
    latitude_jusante: float = Field(ge=-90, le=90)
    longitude_jusante: float = Field(ge=-180, le=180)


def _carregar_bueiros_adicionados() -> list[dict]:
    if not ADICOES_PATH.exists():
        return []
    try:
        registros = json.loads(ADICOES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Não foi possível ler os bueiros cadastrados.") from exc
    return registros if isinstance(registros, list) else []


@router.post("/", status_code=201)
def cadastrar_bueiro(novo_bueiro: NovoBueiro):
    """Persiste um bueiro novo sem alterar o CSV de inventário original."""
    ADICOES_PATH.parent.mkdir(parents=True, exist_ok=True)
    registro = {"id": f"NOVO-{uuid4().hex[:10].upper()}", **novo_bueiro.model_dump()}
    registros = _carregar_bueiros_adicionados()
    registros.append(registro)
    try:
        ADICOES_PATH.write_text(
            json.dumps(registros, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Não foi possível salvar o novo bueiro.") from exc
    return registro


def _numero(valor: str | None) -> float:
    return float((valor or "").strip().replace(",", "."))


def _numero_opcional(valor: str | None) -> float | None:
    if not (valor or "").strip():
        return None
    try:
        return _numero(valor)
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _carregar_inventario() -> tuple[dict, ...]:
    if not CSV_PATH.exists():
        return ()

    try:
        conteudo = CSV_PATH.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        conteudo = CSV_PATH.read_text(encoding="cp1252")

    registros = []
    for identificador, linha in enumerate(csv.DictReader(StringIO(conteudo)), start=1):
        try:
            latitude_montante = _numero(linha.get("Latitude-montante"))
            longitude_montante = _numero(linha.get("Longitude-montante"))
            latitude_jusante = _numero(linha.get("Latitude-jusante"))
            longitude_jusante = _numero(linha.get("Longitude-jusante"))
            km = _numero(linha.get("Km"))
        except (TypeError, ValueError):
            continue
        extensao = _numero_opcional(linha.get("Extensão (m)"))
        dimensao = _numero_opcional(linha.get("Dimensão (m)"))

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
            "extensao_m": extensao,
            "dimensao_m": dimensao,
            "tipo": (linha.get("Tipo") or "").strip(),
            "latitude_montante": latitude_montante,
            "longitude_montante": longitude_montante,
            "latitude_jusante": latitude_jusante,
            "longitude_jusante": longitude_jusante,
        })

    return tuple(registros)


@router.get("/rodovias", response_model=list[str])
def listar_rodovias():
    """Lista as rodovias disponíveis no inventário com coordenadas válidas."""
    inventario = (*_carregar_inventario(), *_carregar_bueiros_adicionados())
    return sorted({bueiro["rodovia"] for bueiro in inventario if bueiro["rodovia"]})


@router.get("/")
def listar_bueiros(rodovia: str | None = Query(default=None)):
    """Lista bueiros do CSV e cadastros manuais, opcionalmente filtrados por rodovia."""
    inventario = (*_carregar_inventario(), *_carregar_bueiros_adicionados())
    if rodovia:
        inventario = tuple(bueiro for bueiro in inventario if bueiro["rodovia"] == rodovia)
    return sorted(inventario, key=lambda bueiro: (bueiro["rodovia"], bueiro["km"], str(bueiro["id"])))


def _distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    raio_terra_m = 6_371_000
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon / 2) ** 2
    return 2 * raio_terra_m * asin(sqrt(a))


@lru_cache(maxsize=1)
def _carregar_solicitacoes_sac() -> tuple[dict, ...]:
    if not SAC_CSV_PATH.exists():
        return ()

    try:
        conteudo = SAC_CSV_PATH.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        conteudo = SAC_CSV_PATH.read_text(encoding="cp1252")

    solicitacoes = []
    for linha in csv.DictReader(StringIO(conteudo)):
        geometria = (linha.get("ge_ponto") or "").strip()
        coordenadas = re.fullmatch(r"POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)", geometria)
        if not coordenadas:
            continue

        try:
            longitude, latitude = SAC_COORDINATE_TRANSFORMER.transform(
                float(coordenadas.group(1)), float(coordenadas.group(2))
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


@router.get("/locais-sac")
def listar_locais_sac():
    """Lista locais únicos com chamados SAC que podem ser cadastrados no inventário."""
    locais = {}
    for solicitacao in _carregar_solicitacoes_sac():
        chave = (round(solicitacao["latitude"], 6), round(solicitacao["longitude"], 6))
        if chave not in locais:
            locais[chave] = {
                "id": f"SAC-{solicitacao['id']}",
                "latitude": solicitacao["latitude"],
                "longitude": solicitacao["longitude"],
                "logradouro": solicitacao["logradouro"],
                "numero": solicitacao["numero"],
                "total_solicitacoes": 0,
            }
        locais[chave]["total_solicitacoes"] += 1

    return sorted(
        locais.values(),
        key=lambda local: (local["logradouro"], local["numero"], local["id"]),
    )


@router.get("/solicitacoes-limpeza")
def listar_solicitacoes_limpeza_proximas(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    raio_m: int = Query(default=500, ge=100, le=5000),
    limite: int = Query(default=1000, ge=1, le=5000),
):
    """Busca chamados SAC próximos; seus pontos UTM são convertidos para WGS84."""
    proximas = []
    for solicitacao in _carregar_solicitacoes_sac():
        distancia = _distancia_metros(
            lat, lon, solicitacao["latitude"], solicitacao["longitude"]
        )
        if distancia <= raio_m:
            proximas.append({**solicitacao, "distancia_m": round(distancia, 1)})

    proximas.sort(key=lambda solicitacao: (solicitacao["distancia_m"], solicitacao["data_abertura"]))
    finalizadas = [
        solicitacao for solicitacao in proximas
        if solicitacao["situacao"] == "FINALIZADA" and solicitacao["data_parecer"]
    ]
    datas_parecer = sorted({solicitacao["data_parecer"] for solicitacao in finalizadas})
    indice_constancia = None
    intervalo_medio_dias = None
    if len(datas_parecer) >= 3:
        from datetime import datetime

        datas = [datetime.fromisoformat(data.replace("Z", "+00:00")) for data in datas_parecer]
        intervalos = [
            (data_atual - data_anterior).total_seconds() / 86400
            for data_anterior, data_atual in zip(datas, datas[1:])
        ]
        intervalo_medio_dias = sum(intervalos) / len(intervalos)
        variancia_amostral = sum(
            (intervalo - intervalo_medio_dias) ** 2 for intervalo in intervalos
        ) / (len(intervalos) - 1)
        coeficiente_variacao = sqrt(variancia_amostral) / intervalo_medio_dias
        indice_constancia = round(100 / (1 + coeficiente_variacao), 1)

    return {
        "latitude_referencia": lat,
        "longitude_referencia": lon,
        "raio_m": raio_m,
        "total_encontradas": len(proximas),
        "total_finalizadas": len(finalizadas),
        "total_canceladas": sum(s["situacao"] == "CANCELADA" for s in proximas),
        "indice_constancia_chamados": indice_constancia,
        "intervalo_medio_dias": round(intervalo_medio_dias, 1) if intervalo_medio_dias is not None else None,
        "periodo_inicio": datas_parecer[0] if datas_parecer else None,
        "periodo_fim": datas_parecer[-1] if datas_parecer else None,
        "solicitacoes": proximas[:limite],
    }