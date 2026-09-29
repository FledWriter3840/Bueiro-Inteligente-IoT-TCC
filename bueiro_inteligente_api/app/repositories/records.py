from typing import Any, Generic, Protocol, TypeVar

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class RecordRepository(Protocol[ModelT]):
    def create(self, values: dict[str, Any]) -> ModelT: ...

    def list_recent(self) -> list[ModelT]: ...


class SQLAlchemyRecordRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]):
        self.session = session
        self.model = model

    def create(self, values: dict[str, Any]) -> ModelT:
        record = self.model(**values)
        try:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        except Exception:
            self.session.rollback()
            raise
        return record

    def list_recent(self) -> list[ModelT]:
        timestamp = getattr(self.model, "data_hora")
        return (
            self.session.query(self.model)
            .order_by(timestamp.desc())
            .all()
        )