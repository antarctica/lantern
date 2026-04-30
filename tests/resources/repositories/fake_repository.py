import logging
from collections.abc import Collection

from lantern.config import Config
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.repositories.base import RepositoryBase
from tests.resources.stores.fake_records_store import FakeRecordsStore


class FakeRepository(RepositoryBase):
    """
    Fake repository for testing.

    Used to test RepositoryBase.

    Simplistic example wrapping a single Store. Would not be used in practice (over using a Store directly).
    """

    def __init__(self, logger: logging.Logger, config: Config, store: FakeRecordsStore) -> None:
        super().__init__(logger)
        self._config = config
        self._store = store

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return all records or raise a `RecordsNotFoundError` exception."""
        return self._store.select(file_identifiers=file_identifiers)

    def select_one(self, file_identifier: str) -> RecordRevision:
        """Return a specific record or raise a `RecordNotFoundError` exception."""
        return self._store.select_one(file_identifier=file_identifier)

    def upsert(self, content: Collection[Record]) -> None:
        """Persist new or existing records."""
        return
