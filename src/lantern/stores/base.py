from abc import ABC, abstractmethod
from typing import Protocol

from lantern.models.record.revision import RecordRevision


class StoreFrozenUnsupportedError(Exception):
    """Raised when attempting to freeze an unsupported store."""

    pass


class StoreFrozenError(Exception):
    """Raised when attempting to modify a frozen store."""

    pass


class RecordNotFoundError(Exception):
    """Raised when a record cannot be retrieved."""

    def __init__(self, file_identifier: str) -> None:
        self.file_identifier = file_identifier

    def __str__(self) -> str:
        """Exception string representation."""
        return f"Record '{self.file_identifier}' not found."


class RecordsNotFoundError(Exception):
    """Raised when one or more records cannot be retrieved."""

    def __init__(self, file_identifiers: set[str]) -> None:
        self.file_identifiers = file_identifiers

    def __str__(self) -> str:
        """Exception string representation."""
        return f"Records '{', '.join(self.file_identifiers)}' not found."


class Store(ABC):
    """
    Base representation for a container of resources.

    Stores manage Records held in a temporary or permanent storage system, such as an in-memory dict or remote database.

    This class defines the abstract interface Stores must implement to manage Records and RecordSummaries.
    """

    @property
    @abstractmethod
    def frozen(self) -> bool:
        """Whether store can be modified/updated."""
        ...

    @abstractmethod
    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return all records or raise a `RecordsNotFoundError` exception."""
        ...

    @abstractmethod
    def select_one(self, file_identifier: str) -> RecordRevision:
        """Return a specific record or raise a `RecordNotFoundError` exception."""
        ...


class SelectRecordsProtocol(Protocol):
    """Callable protocol for selecting records from Store."""

    def __call__(  # pragma: no branch  # noqa: D102
        self, file_identifiers: set[str] | None = None
    ) -> list[RecordRevision]: ...


class SelectRecordProtocol(Protocol):
    """Callable protocol for selecting a record from Store."""

    def __call__(self, file_identifier: str) -> RecordRevision: ...  # pragma: no branch  # noqa: D102
