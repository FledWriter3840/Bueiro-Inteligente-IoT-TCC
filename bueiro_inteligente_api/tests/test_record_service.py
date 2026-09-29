import unittest
from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError

from app.repositories.records import SQLAlchemyRecordRepository
from app.schemas import LimpezaCreate
from app.services.records import RecordService


class SortField:
    def desc(self):
        return "data_hora DESC"


class FakeRecord:
    data_hora = SortField()

    def __init__(self, **values):
        self.__dict__.update(values)


class TestRecordService(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.repository = SQLAlchemyRecordRepository(self.session, FakeRecord)
        self.service = RecordService(self.repository)

    def test_create_commits_and_refreshes_record(self):
        record = self.service.create(LimpezaCreate(status_limpeza="Manual"))

        self.assertEqual(record.status_limpeza, "Manual")
        self.session.add.assert_called_once_with(record)
        self.session.commit.assert_called_once_with()
        self.session.refresh.assert_called_once_with(record)

    def test_create_rolls_back_when_commit_fails(self):
        self.session.commit.side_effect = SQLAlchemyError("database failure")

        with self.assertRaises(SQLAlchemyError):
            self.service.create(LimpezaCreate(status_limpeza="Manual"))

        self.session.rollback.assert_called_once_with()

    def test_list_orders_records_by_timestamp_descending(self):
        expected = [FakeRecord(status_limpeza="Manual")]
        self.session.query.return_value.order_by.return_value.all.return_value = expected

        records = self.service.list_recent()

        self.assertEqual(records, expected)
        self.session.query.assert_called_once_with(FakeRecord)
        self.session.query.return_value.order_by.assert_called_once_with("data_hora DESC")


if __name__ == "__main__":
    unittest.main()