from uuid import uuid4
from typing import Protocol

from ..schemas import BueiroCreate


class BueiroRepository(Protocol):
    def adicionar(self, registro: dict) -> None: ...

    def listar_adicionados(self) -> list[dict]: ...


class BueiroService:
    def __init__(self, repository: BueiroRepository):
        self.repository = repository

    def cadastrar(self, novo_bueiro: BueiroCreate) -> dict:
        registro = {
            "id": f"NOVO-{uuid4().hex[:10].upper()}",
            **novo_bueiro.model_dump(),
        }
        self.repository.adicionar(registro)
        return registro

    def listar_adicionados(self) -> list[dict]:
        return self.repository.listar_adicionados()