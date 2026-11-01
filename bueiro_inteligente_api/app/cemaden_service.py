"""Index and query the local CEMADEN rainfall archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import BUEIRO_LATITUDE, BUEIRO_LONGITUDE, CEMADEN_ESTACAO

logger = logging.getLogger(__name__)

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATASET_PATH = Path(
    os.getenv(
        "CEMADEN_DATASET_PATH",
        str(Path(__file__).resolve().parents[1] / "datasets" / "dados_pluviometricos"),
    )
)
INDEX_PATH = Path(
    os.getenv(
        "CEMADEN_INDEX_PATH",
        str(Path(tempfile.gettempdir()) / "bueiro-inteligente" / "cemaden.sqlite3"),
    )
)
RAIO_MAXIMO_KM = float(os.getenv("CEMADEN_RAIO_MAXIMO_KM", "25"))
IDADE_MAXIMA_MINUTOS = int(os.getenv("CEMADEN_IDADE_MAXIMA_MINUTOS", "90"))

CAMPOS_OBRIGATORIOS = {
    "codEstacao",
    "nomeEstacao",
    "latitude",
    "longitude",
    "datahora",
    "valorMedida",
}


@dataclass(frozen=True)
class DadosPluviometricosCemaden:
    disponivel: bool = False
    status: str = "Indisponível"
    codigo_estacao: str | None = None
    nome_estacao: str | None = None
    latitude_estacao: float | None = None
    longitude_estacao: float | None = None
    distancia_km: float | None = None
    chuva_ultima_hora_mm: float | None = None
    data_ultima_leitura: str | None = None
    idade_dados_minutos: float | None = None

    def para_dict(self) -> dict[str, object]:
        return asdict(self)


def _arquivos_csv(caminho: Path | None = None) -> list[Path]:
    caminho = caminho or DATASET_PATH
    if not caminho.is_dir():
        return []
    return sorted(arquivo for arquivo in caminho.rglob("*.csv") if arquivo.is_file())


def _assinatura_arquivos(arquivos: list[Path]) -> str:
    assinatura = hashlib.sha256()
    for arquivo in arquivos:
        stat = arquivo.stat()
        assinatura.update(
            f"{arquivo.resolve()}|{stat.st_size}|{stat.st_mtime_ns}\n".encode("utf-8")
        )
    return assinatura.hexdigest()


def _decimal(valor: str | None) -> float:
    texto = (valor or "").strip().replace(",", ".")
    resultado = float(texto)
    if not math.isfinite(resultado):
        raise ValueError("valor numérico não finito")
    return resultado


def _timestamp(valor: str | None) -> datetime:
    texto = (valor or "").strip()
    return datetime.fromisoformat(texto)


def _ler_linhas(arquivo: Path):
    with arquivo.open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        campos = set(reader.fieldnames or [])
        ausentes = CAMPOS_OBRIGATORIOS - campos
        if ausentes:
            raise ValueError(
                f"CSV CEMADEN inválido em {arquivo}: faltam as colunas "
                f"{', '.join(sorted(ausentes))}."
            )
        yield from reader


def _distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    raio_terra_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * raio_terra_km * math.asin(math.sqrt(a))


def _catalogo_estacoes(arquivo: Path) -> dict[str, tuple[str, float, float]]:
    estacoes: dict[str, tuple[str, float, float]] = {}
    for linha in _ler_linhas(arquivo):
        codigo = (linha.get("codEstacao") or "").strip()
        if not codigo or codigo in estacoes:
            continue
        try:
            estacoes[codigo] = (
                (linha.get("nomeEstacao") or "").strip(),
                _decimal(linha.get("latitude")),
                _decimal(linha.get("longitude")),
            )
        except ValueError:
            continue
    return estacoes


def construir_indice(
    caminho_dados: Path = DATASET_PATH,
    caminho_indice: Path = INDEX_PATH,
    latitude: float = BUEIRO_LATITUDE,
    longitude: float = BUEIRO_LONGITUDE,
    codigo_estacao: str | None = CEMADEN_ESTACAO or None,
) -> dict[str, object]:
    """Build a compact SQLite index for the station nearest to the drain."""
    arquivos = _arquivos_csv(caminho_dados)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum CSV CEMADEN encontrado em {caminho_dados}.")

    estacoes = _catalogo_estacoes(arquivos[0])
    if not estacoes:
        raise ValueError(f"Nenhuma estação válida encontrada em {arquivos[0]}.")

    if codigo_estacao:
        if codigo_estacao not in estacoes:
            raise ValueError(
                f"A estação CEMADEN '{codigo_estacao}' não existe em {arquivos[0]}."
            )
        codigo_selecionado = codigo_estacao
    else:
        codigo_selecionado = min(
            estacoes,
            key=lambda codigo: _distancia_km(
                latitude,
                longitude,
                estacoes[codigo][1],
                estacoes[codigo][2],
            ),
        )

    nome_estacao, latitude_estacao, longitude_estacao = estacoes[codigo_selecionado]
    distancia = _distancia_km(
        latitude, longitude, latitude_estacao, longitude_estacao
    )
    if distancia > RAIO_MAXIMO_KM:
        raise ValueError(
            f"A estação mais próxima está a {distancia:.1f} km, acima do limite "
            f"configurado de {RAIO_MAXIMO_KM:.1f} km."
        )

    caminho_indice.parent.mkdir(parents=True, exist_ok=True)
    caminho_temporario = caminho_indice.with_name(caminho_indice.name + ".tmp")
    if caminho_temporario.exists():
        caminho_temporario.unlink()

    registros = 0
    linhas_invalidas = 0
    conexao = sqlite3.connect(caminho_temporario)
    try:
        with conexao:
            conexao.execute(
                "CREATE TABLE observacoes ("
                "data_hora TEXT PRIMARY KEY, chuva_mm REAL NOT NULL)"
            )
            conexao.execute(
                "CREATE TABLE metadados (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)"
            )
            for arquivo in arquivos:
                lote: list[tuple[str, float]] = []
                for linha in _ler_linhas(arquivo):
                    if (linha.get("codEstacao") or "").strip() != codigo_selecionado:
                        continue
                    try:
                        instante = _timestamp(linha.get("datahora"))
                        chuva_mm = _decimal(linha.get("valorMedida"))
                        if chuva_mm < 0:
                            raise ValueError("precipitação negativa")
                    except (ValueError, TypeError):
                        linhas_invalidas += 1
                        continue
                    lote.append((instante.isoformat(sep=" "), chuva_mm))
                cursor = conexao.executemany(
                    "INSERT OR IGNORE INTO observacoes (data_hora, chuva_mm) VALUES (?, ?)",
                    lote,
                )
                registros += cursor.rowcount

            metadados = {
                "assinatura_arquivos": _assinatura_arquivos(arquivos),
                "codigo_estacao": codigo_selecionado,
                "nome_estacao": nome_estacao,
                "latitude_estacao": str(latitude_estacao),
                "longitude_estacao": str(longitude_estacao),
                "latitude_referencia": str(latitude),
                "longitude_referencia": str(longitude),
                "arquivos": str(len(arquivos)),
                "registros": str(registros),
            }
            conexao.executemany(
                "INSERT INTO metadados (chave, valor) VALUES (?, ?)",
                metadados.items(),
            )
            conexao.execute(
                "CREATE INDEX idx_observacoes_data_hora "
                "ON observacoes (data_hora)"
            )

    finally:
        conexao.close()

    try:
        os.replace(caminho_temporario, caminho_indice)
    finally:
        if caminho_temporario.exists():
            caminho_temporario.unlink()

    if linhas_invalidas:
        logger.warning(
            "CEMADEN: %d leituras inválidas ignoradas durante a indexação.",
            linhas_invalidas,
        )
    logger.info(
        "Índice CEMADEN criado: estação %s (%s), %d registros em %d arquivos.",
        codigo_selecionado,
        nome_estacao,
        registros,
        len(arquivos),
    )
    return {
        "codigo_estacao": codigo_selecionado,
        "nome_estacao": nome_estacao,
        "latitude_estacao": latitude_estacao,
        "longitude_estacao": longitude_estacao,
        "distancia_km": round(distancia, 3),
        "arquivos_processados": len(arquivos),
        "registros_indexados": registros,
        "leituras_invalidas": linhas_invalidas,
        "caminho_indice": str(caminho_indice),
    }


def _agora_local(agora: datetime | None) -> datetime:
    if agora is None:
        return datetime.now(FUSO_BRASILIA).replace(tzinfo=None)
    if agora.tzinfo is None:
        return agora.replace(tzinfo=timezone.utc).astimezone(FUSO_BRASILIA).replace(
            tzinfo=None
        )
    return agora.astimezone(FUSO_BRASILIA).replace(tzinfo=None)


def obter_dados_pluviometricos(
    latitude: float = BUEIRO_LATITUDE,
    longitude: float = BUEIRO_LONGITUDE,
    agora: datetime | None = None,
) -> DadosPluviometricosCemaden:
    """Return one-hour observed rainfall when the indexed station is fresh."""
    if not INDEX_PATH.is_file():
        return DadosPluviometricosCemaden(
            status="Índice CEMADEN não encontrado; execute a indexação documentada."
        )

    arquivos = _arquivos_csv()
    if not arquivos:
        return DadosPluviometricosCemaden(
            status=f"Arquivos CSV CEMADEN não encontrados em {DATASET_PATH}."
        )

    try:
        with closing(sqlite3.connect(INDEX_PATH)) as conexao:
            metadados = dict(
                conexao.execute("SELECT chave, valor FROM metadados").fetchall()
            )
            if metadados.get("assinatura_arquivos") != _assinatura_arquivos(arquivos):
                return DadosPluviometricosCemaden(
                    status="Índice CEMADEN desatualizado; execute novamente a indexação."
                )

            latitude_estacao = float(metadados["latitude_estacao"])
            longitude_estacao = float(metadados["longitude_estacao"])
            distancia = _distancia_km(
                latitude, longitude, latitude_estacao, longitude_estacao
            )
            if distancia > RAIO_MAXIMO_KM:
                return DadosPluviometricosCemaden(
                    status=(
                        f"Estação indexada a {distancia:.1f} km; fora do limite de "
                        f"{RAIO_MAXIMO_KM:.1f} km para esta localização."
                    )
                )

            instante_local = _agora_local(agora)
            ultima = conexao.execute(
                "SELECT data_hora FROM observacoes "
                "WHERE data_hora <= ? ORDER BY data_hora DESC LIMIT 1",
                (instante_local.isoformat(sep=" "),),
            ).fetchone()
            if ultima is None:
                return DadosPluviometricosCemaden(
                    status="A estação indexada não possui leituras até o horário consultado."
                )

            data_ultima = datetime.fromisoformat(ultima[0])
            idade_minutos = (instante_local - data_ultima).total_seconds() / 60
            if idade_minutos < 0 or idade_minutos > IDADE_MAXIMA_MINUTOS:
                return DadosPluviometricosCemaden(
                    status=(
                        f"Última leitura da estação tem {idade_minutos:.0f} min; "
                        f"limite de atualidade: {IDADE_MAXIMA_MINUTOS} min."
                    ),
                    codigo_estacao=metadados["codigo_estacao"],
                    nome_estacao=metadados["nome_estacao"],
                    latitude_estacao=latitude_estacao,
                    longitude_estacao=longitude_estacao,
                    distancia_km=round(distancia, 3),
                    data_ultima_leitura=data_ultima.isoformat(sep=" "),
                    idade_dados_minutos=round(idade_minutos, 1),
                )

            inicio_janela = instante_local - timedelta(hours=1)
            chuva_ultima_hora = conexao.execute(
                "SELECT COALESCE(SUM(chuva_mm), 0) FROM observacoes "
                "WHERE data_hora > ? AND data_hora <= ?",
                (
                    inicio_janela.isoformat(sep=" "),
                    instante_local.isoformat(sep=" "),
                ),
            ).fetchone()[0]
    except (sqlite3.Error, KeyError, ValueError) as exc:
        logger.error("Falha ao consultar o índice pluviométrico CEMADEN: %s", exc)
        return DadosPluviometricosCemaden(
            status=f"Falha ao consultar índice CEMADEN: {type(exc).__name__}."
        )

    return DadosPluviometricosCemaden(
        disponivel=True,
        status="Ativo",
        codigo_estacao=metadados["codigo_estacao"],
        nome_estacao=metadados["nome_estacao"],
        latitude_estacao=latitude_estacao,
        longitude_estacao=longitude_estacao,
        distancia_km=round(distancia, 3),
        chuva_ultima_hora_mm=round(float(chuva_ultima_hora), 2),
        data_ultima_leitura=data_ultima.isoformat(sep=" "),
        idade_dados_minutos=round(idade_minutos, 1),
    )


def obter_historico_diario(
    data_inicio: date,
    data_fim: date,
    latitude: float = BUEIRO_LATITUDE,
    longitude: float = BUEIRO_LONGITUDE,
) -> dict[str, object]:
    """Return daily precipitation totals from the indexed station."""
    if data_fim < data_inicio:
        raise ValueError("A data final deve ser igual ou posterior à data inicial.")
    if not INDEX_PATH.is_file():
        return {
            "disponivel": False,
            "status": "Índice CEMADEN não encontrado; execute a indexação documentada.",
            "dias": [],
        }

    arquivos = _arquivos_csv()
    if not arquivos:
        return {
            "disponivel": False,
            "status": f"Arquivos CSV CEMADEN não encontrados em {DATASET_PATH}.",
            "dias": [],
        }

    try:
        with closing(sqlite3.connect(INDEX_PATH)) as conexao:
            metadados = dict(
                conexao.execute("SELECT chave, valor FROM metadados").fetchall()
            )
            if metadados.get("assinatura_arquivos") != _assinatura_arquivos(arquivos):
                return {
                    "disponivel": False,
                    "status": "Índice CEMADEN desatualizado; execute novamente a indexação.",
                    "dias": [],
                }

            latitude_estacao = float(metadados["latitude_estacao"])
            longitude_estacao = float(metadados["longitude_estacao"])
            distancia = _distancia_km(
                latitude, longitude, latitude_estacao, longitude_estacao
            )
            if distancia > RAIO_MAXIMO_KM:
                return {
                    "disponivel": False,
                    "status": (
                        f"Estação indexada a {distancia:.1f} km; fora do limite de "
                        f"{RAIO_MAXIMO_KM:.1f} km para esta localização."
                    ),
                    "dias": [],
                }

            inicio = data_inicio.isoformat()
            fim_exclusivo = (data_fim + timedelta(days=1)).isoformat()
            linhas = conexao.execute(
                "SELECT date(data_hora), SUM(chuva_mm), COUNT(*) "
                "FROM observacoes WHERE data_hora >= ? AND data_hora < ? "
                "GROUP BY date(data_hora) ORDER BY date(data_hora)",
                (inicio, fim_exclusivo),
            ).fetchall()
    except (sqlite3.Error, KeyError, ValueError) as exc:
        logger.error("Falha ao consultar histórico CEMADEN: %s", exc)
        return {
            "disponivel": False,
            "status": f"Falha ao consultar índice CEMADEN: {type(exc).__name__}.",
            "dias": [],
        }

    dias = [
        {
            "data": dia,
            "chuva_mm": round(float(chuva_mm), 2),
            "quantidade_leituras": int(quantidade),
        }
        for dia, chuva_mm, quantidade in linhas
    ]
    return {
        "disponivel": True,
        "status": "Histórico indexado",
        "codigo_estacao": metadados["codigo_estacao"],
        "nome_estacao": metadados["nome_estacao"],
        "latitude_estacao": latitude_estacao,
        "longitude_estacao": longitude_estacao,
        "distancia_km": round(distancia, 3),
        "data_inicio": inicio,
        "data_fim": data_fim.isoformat(),
        "total_dias_com_dados": len(dias),
        "chuva_total_mm": round(sum(dia["chuva_mm"] for dia in dias), 2),
        "dias": dias,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Cria o índice local da estação CEMADEN mais próxima do bueiro."
    )
    parser.add_argument(
        "--build-index",
        action="store_true",
        help="Processa os CSVs e cria o índice compacto usado pela API.",
    )
    parser.add_argument("--latitude", type=float, default=BUEIRO_LATITUDE)
    parser.add_argument("--longitude", type=float, default=BUEIRO_LONGITUDE)
    parser.add_argument("--station", help="Código opcional para fixar uma estação.")
    argumentos = parser.parse_args()
    if not argumentos.build_index:
        parser.error("informe --build-index para criar o índice.")
    resultado = construir_indice(
        latitude=argumentos.latitude,
        longitude=argumentos.longitude,
        codigo_estacao=argumentos.station,
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
