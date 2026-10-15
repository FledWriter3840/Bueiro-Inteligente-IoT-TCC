from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from ..schemas import BueiroCreate
from ..repositories.inventario_bueiros import InventarioBueirosRepository
from .bueiros import BueiroService


class CatalogoBueirosService:
    """Aplica filtros e agrega os inventários de bueiros e chamados SAC."""

    def __init__(
        self,
        repository: InventarioBueirosRepository,
        bueiro_service: BueiroService,
    ):
        self.repository = repository
        self.bueiro_service = bueiro_service

    def cadastrar(self, bueiro: BueiroCreate) -> dict:
        return self.bueiro_service.cadastrar(bueiro)

    def listar_rodovias(self) -> list[str]:
        inventario = self._inventario_com_cadastros()
        return sorted({
            bueiro["rodovia"]
            for bueiro in inventario
            if bueiro["rodovia"]
        })

    def listar_bueiros(self, rodovia: str | None = None) -> list[dict]:
        inventario = self._inventario_com_cadastros()
        if rodovia:
            inventario = tuple(
                bueiro for bueiro in inventario
                if bueiro["rodovia"] == rodovia
            )
        return sorted(
            inventario,
            key=lambda bueiro: (
                bueiro["rodovia"],
                bueiro["km"],
                str(bueiro["id"]),
            ),
        )

    def listar_locais_sac(self) -> list[dict]:
        locais = {}
        for solicitacao in self.repository.carregar_solicitacoes_sac():
            chave = (
                round(solicitacao["latitude"], 6),
                round(solicitacao["longitude"], 6),
            )
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
            key=lambda local: (
                local["logradouro"],
                local["numero"],
                local["id"],
            ),
        )

    def listar_solicitacoes_proximas(
        self,
        lat: float,
        lon: float,
        raio_m: int,
        limite: int,
    ) -> dict:
        proximas = []
        for solicitacao in self.repository.carregar_solicitacoes_sac():
            distancia = _distancia_metros(
                lat,
                lon,
                solicitacao["latitude"],
                solicitacao["longitude"],
            )
            if distancia <= raio_m:
                proximas.append({
                    **solicitacao,
                    "distancia_m": round(distancia, 1),
                })

        proximas.sort(
            key=lambda solicitacao: (
                solicitacao["distancia_m"],
                solicitacao["data_abertura"],
            )
        )
        finalizadas = [
            solicitacao for solicitacao in proximas
            if solicitacao["situacao"] == "FINALIZADA"
            and solicitacao["data_parecer"]
        ]
        datas_parecer = sorted({
            solicitacao["data_parecer"]
            for solicitacao in finalizadas
        })
        indice_constancia, intervalo_medio_dias = _calcular_constancia(
            datas_parecer
        )

        return {
            "latitude_referencia": lat,
            "longitude_referencia": lon,
            "raio_m": raio_m,
            "total_encontradas": len(proximas),
            "total_finalizadas": len(finalizadas),
            "total_canceladas": sum(
                solicitacao["situacao"] == "CANCELADA"
                for solicitacao in proximas
            ),
            "indice_constancia_chamados": indice_constancia,
            "intervalo_medio_dias": (
                round(intervalo_medio_dias, 1)
                if intervalo_medio_dias is not None
                else None
            ),
            "periodo_inicio": datas_parecer[0] if datas_parecer else None,
            "periodo_fim": datas_parecer[-1] if datas_parecer else None,
            "solicitacoes": proximas[:limite],
        }

    def _inventario_com_cadastros(self) -> tuple[dict, ...]:
        return (
            *self.repository.carregar_inventario(),
            *self.bueiro_service.listar_adicionados(),
        )


def _distancia_metros(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    raio_terra_m = 6_371_000
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = (
        sin(delta_lat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(delta_lon / 2) ** 2
    )
    return 2 * raio_terra_m * asin(sqrt(a))


def _calcular_constancia(
    datas_parecer: list[str],
) -> tuple[float | None, float | None]:
    if len(datas_parecer) < 3:
        return None, None

    datas = [
        datetime.fromisoformat(data.replace("Z", "+00:00"))
        for data in datas_parecer
    ]
    intervalos = [
        (atual - anterior).total_seconds() / 86400
        for anterior, atual in zip(datas, datas[1:])
    ]
    intervalo_medio = sum(intervalos) / len(intervalos)
    variancia = sum(
        (intervalo - intervalo_medio) ** 2
        for intervalo in intervalos
    ) / (len(intervalos) - 1)
    coeficiente_variacao = sqrt(variancia) / intervalo_medio
    return round(100 / (1 + coeficiente_variacao), 1), intervalo_medio
