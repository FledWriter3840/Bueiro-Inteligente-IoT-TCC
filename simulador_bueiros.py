"""Gera leituras de demonstração e envia telemetria à API FastAPI."""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone

import requests


PERFIS_NIVEL = (
    (22, 32, 45, 58, 68, 82, 91, 72, 48),
    (15, 27, 42, 57, 79, 86, 63, 38),
    (10, 20, 35, 50, 62, 81, 95, 67, 30),
)
logger = logging.getLogger("simulador_bueiros")


def nivel_simulado(id_sensor: int, ciclo: int) -> int:
    """Retorna um nível determinístico que sobe até a faixa crítica."""
    perfil = PERFIS_NIVEL[(id_sensor - 1) % len(PERFIS_NIVEL)]
    return perfil[ciclo % len(perfil)]


def montar_leitura(
    id_sensor: int,
    ciclo: int,
    instante: datetime | None = None,
) -> dict[str, int | float | str]:
    nivel = nivel_simulado(id_sensor, ciclo)
    distancia_cm = round(450 * (1 - nivel / 100), 2)
    data_hora = instante or datetime.now(timezone.utc)
    return {
        "id_sensor": id_sensor,
        "valor_leitura": distancia_cm,
        "unidade_medida": "cm",
        "data_hora": data_hora.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }


def obter_ids_sensores(api_url: str, ids_configurados: str | None) -> list[int]:
    if ids_configurados:
        try:
            ids = [int(item.strip()) for item in ids_configurados.split(",")]
        except ValueError as exc:
            raise ValueError("--ids deve conter números separados por vírgula.") from exc
    else:
        resposta = requests.get(f"{api_url}/bueiros", timeout=10)
        resposta.raise_for_status()
        ids = [int(item["id"]) for item in resposta.json()]

    ids_unicos = sorted(set(ids))
    if len(ids_unicos) < 3:
        raise ValueError(
            "A demonstração requer ao menos 3 sensores. Execute, uma vez, "
            "bueiro_inteligente_api/migrations/002_sensores_demo.sql."
        )
    if any(id_sensor <= 0 for id_sensor in ids_unicos):
        raise ValueError("Os identificadores dos sensores devem ser positivos.")
    return ids_unicos


def executar(
    api_url: str,
    ids_sensores: list[int],
    intervalo: float,
    ciclos: int,
) -> int:
    ciclo = 0
    falhas = 0
    while ciclos == 0 or ciclo < ciclos:
        for id_sensor in ids_sensores:
            leitura = montar_leitura(id_sensor, ciclo)
            try:
                resposta = requests.post(
                    f"{api_url}/sensores/leitura",
                    json=leitura,
                    timeout=20,
                )
                resposta.raise_for_status()
                dados = resposta.json()
                logger.info(
                    "Sensor %s: %.2f cm, risco=%s, duplicada=%s",
                    id_sensor,
                    leitura["valor_leitura"],
                    dados.get("nivel_risco", "indisponível"),
                    dados.get("duplicada", False),
                )
            except requests.RequestException as exc:
                falhas += 1
                logger.error(
                    "Falha ao enviar leitura do sensor %s: %s",
                    id_sensor,
                    exc,
                )
        ciclo += 1
        if ciclos == 0 or ciclo < ciclos:
            time.sleep(intervalo)
    return falhas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simula níveis de bueiros e envia leituras à API."
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("BUEIRO_API_URL", "http://localhost:8000"),
        help="URL base da API (padrão: BUEIRO_API_URL ou localhost:8000).",
    )
    parser.add_argument(
        "--ids",
        default=None,
        help="IDs existentes separados por vírgula; padrão: consulta GET /bueiros.",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=5,
        help="Segundos entre ciclos (padrão: 5).",
    )
    parser.add_argument(
        "--ciclos",
        type=int,
        default=0,
        help="Quantidade de ciclos; zero mantém a simulação ativa.",
    )
    argumentos = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if argumentos.intervalo <= 0 or argumentos.ciclos < 0:
        parser.error("--intervalo deve ser positivo e --ciclos não pode ser negativo.")

    api_url = argumentos.api_url.rstrip("/")
    try:
        ids_sensores = obter_ids_sensores(api_url, argumentos.ids)
    except (requests.RequestException, ValueError) as exc:
        logger.error("Não foi possível iniciar o simulador: %s", exc)
        return 1

    logger.info("Simulando sensores: %s", ", ".join(map(str, ids_sensores)))
    try:
        falhas = executar(
            api_url,
            ids_sensores,
            argumentos.intervalo,
            argumentos.ciclos,
        )
    except KeyboardInterrupt:
        logger.info("Simulação interrompida pelo operador.")
        return 0
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
