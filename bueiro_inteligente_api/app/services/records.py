from typing import Generic, TypeVar

from pydantic import BaseModel

from ..repositories.records import RecordRepository

ModelT = TypeVar("ModelT")


class RecordService(Generic[ModelT]):
    """Executa operações CRUD genéricas usando um repositório."""

    def __init__(self, repository: RecordRepository[ModelT]) -> None:
        """Inicializa o serviço com seu repositório."""
        self.repository = repository

    def create(self, payload: BaseModel) -> ModelT:
        """Cria um registro a partir de um schema Pydantic."""
        return self.repository.create(payload.model_dump())

    def list_recent(self) -> list[ModelT]:
        """Lista os registros em ordem recente."""
        return self.repository.list_recent()