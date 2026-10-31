from uuid import uuid4
from typing import Protocol

from ..schemas import BueiroCreate


class BueiroRepository(Protocol):
    def adicionar(self, registro: dict) -> None: ...

    def listar_adicionados(self) -> list[dict]: ...

    def remover(self, identificador: str) -> bool: ...


class BueiroService:
    """Valida e coordena operações sobre os bueiros cadastrados."""

    def __init__(self, repository: BueiroRepository) -> None:
        """Inicializa o serviço com seu repositório."""
        self.repository = repository

    def cadastrar(self, novo_bueiro: BueiroCreate) -> dict[str, object]:
        """Cadastra um bueiro validado e retorna seu registro."""
        registro = {
            "id": f"NOVO-{uuid4().hex[:10].upper()}",
            **novo_bueiro.model_dump(),
        }
        self.repository.adicionar(registro)
        return registro

    def listar_adicionados(self) -> list[dict]:
        """Lista os bueiros cadastrados fora do inventário original."""
        return self.repository.listar_adicionados()

    def remover(self, identificador: str) -> bool:
        """Remove um bueiro cadastrado fora do inventário original."""
        return self.repository.remover(identificador)