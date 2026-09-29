from typing import Generic, TypeVar

from pydantic import BaseModel

from ..repositories.records import RecordRepository

ModelT = TypeVar("ModelT")


class RecordService(Generic[ModelT]):
    def __init__(self, repository: RecordRepository[ModelT]):
        self.repository = repository

    def create(self, payload: BaseModel) -> ModelT:
        return self.repository.create(payload.model_dump())

    def list_recent(self) -> list[ModelT]:
        return self.repository.list_recent()