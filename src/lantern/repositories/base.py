import logging
from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Any

from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.repository import UpsertResults


class RepositoryBase(ABC):
    """
    Abstract base class for a repository.

    Repositories are responsible for managing records within one or more Stores as part of a Catalogue.

    This base repository class is intended to be generic, with subclasses being more opinionated.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialise."""
        self._logger = logger

    @abstractmethod
    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return all records or raise a `RecordsNotFoundError` exception."""
        ...

    @abstractmethod
    def select_one(self, file_identifier: str) -> RecordRevision:
        """Return a specific record or raise a `RecordNotFoundError` exception."""
        ...

    @abstractmethod
    def upsert(self, records: Collection[Record], *args: Any, **kwargs: Any) -> UpsertResults:
        """Persist new or existing records."""
        ...
