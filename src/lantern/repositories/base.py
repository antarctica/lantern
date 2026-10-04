from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    import logging
    from collections.abc import Collection, Iterator

    from lantern.models.record.record import Record
    from lantern.models.record.revision import RecordRevision
    from lantern.models.repository import UpsertResults


class RecordsProtocol(Protocol):
    """
    Interface to abstract accessing Records from Stores.

    Intended for use with Sites and returned by Repositories, to prevent direct knowledge of any backing Stores and
    avoid abstraction leaks.

    Termed a snapshot to encourage returning a consistent set of records for use in parallel Site workers.
    """

    @property
    def head_commit(self) -> str | None:
        """Optional commit-like reference if available."""
        ...

    @property
    def record_count(self) -> int:
        """Number of available records."""
        ...

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return all or specified records, raises `RecordsNotFoundError` if any specified records aren't found."""
        ...

    def select_one(self, file_identifier: str) -> RecordRevision:
        """Return a specific record or raise a `RecordNotFoundError`."""
        ...

    def prep_parallel(self) -> RecordsProtocol:
        """
        Adapt snapshot to efficiently pass to parallel workers.

        As per StoreBase.prep_parallel().
        """
        ...

    def restore_parallel(self) -> None:
        """
        Adapt snapshot for performance once passed to a parallel worker.

        As per StoreBase.restore_parallel().
        """
        ...


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
    def select_records(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return all records or raise a `RecordsNotFoundError` exception."""
        ...

    @abstractmethod
    def select_record(self, file_identifier: str) -> RecordRevision:
        """Return a specific record or raise a `RecordNotFoundError` exception."""
        ...

    @abstractmethod
    def upsert_records(self, records: Collection[Record], *args: Any, **kwargs: Any) -> UpsertResults:
        """Persist new or existing records."""
        ...

    @abstractmethod
    @contextmanager
    def snapshot(self) -> Iterator[RecordsProtocol]:
        """
        Yield available records for Site generation.

        Intended to prevent Site instances needing direct access to Store by defining the subset of methods and
        properties a Site needs.

        Where a repository wraps around a single Store, this method MAY yield the Store itself, providing it implements
        the RecordsProtocol.
        """
        ...
