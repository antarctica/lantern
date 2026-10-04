from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from lantern.models.record.revision import RecordRevision


class StoreFrozenUnsupportedError(Exception):
    """Raised when attempting to freeze an unsupported store."""


class StoreCountUnsupportedError(Exception):
    """Raised when attempting to count records in a store that cannot do so efficiently."""


class StoreFrozenError(Exception):
    """Raised when attempting to modify a frozen store."""


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


class SelectRecordsProtocol(Protocol):
    """Callable interface for selecting records from Store."""

    def __call__(  # pragma: no branch  # noqa: D102
        self, file_identifiers: set[str] | None = None
    ) -> list[RecordRevision]: ...


class SelectRecordProtocol(Protocol):
    """Callable interface for selecting a record from Store."""

    def __call__(self, file_identifier: str) -> RecordRevision: ...  # pragma: no branch  # noqa: D102


class StoreBase(ABC):
    """
    Abstract base class for stores.

    Stores manage Records held in a temporary or permanent storage system, such as an in-memory dict or remote database.

    This class defines the abstract interface Stores must implement to manage Records and RecordSummaries.
    """

    @abstractmethod
    def __len__(self) -> int:
        """Number of available records."""
        ...

    @property
    @abstractmethod
    def frozen(self) -> bool:
        """Whether store can be modified/updated."""
        ...

    @abstractmethod
    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return all or specified records, raises `RecordsNotFoundError` if any specified records aren't found."""
        ...

    @abstractmethod
    def select_one(self, file_identifier: str) -> RecordRevision:
        """Return a specific record or raise a `RecordNotFoundError`."""
        ...

    @abstractmethod
    def freeze(self) -> None:
        """
        Attempt to freeze store.

        Raises `StoreFrozenUnsupportedError` if not supported.
        """
        ...

    def prep_parallel(self) -> StoreBase:
        """
        Return store configured for use in parallel workers.

        When used in parallel processing, Stores are pickled for each parallel worker (not job), which may be
        impossible (e.g. for active database connections) or inefficient (e.g. for in-memory state).

        Stores MUST support pickling and SHOULD exclude, or otherwise mitigate, any significant overheads within a
        returned COPY. Stores MUST NOT modify the current instance, as it MAY remain in use by a calling process.

        Where changes are not needed, the current store SHOULD be returned unchanged.

        Paired with `restore_parallel()`, which reverses/restores any changes.
        """
        return self

    def restore_parallel(self) -> None:
        """
        Re-configure store for optimum use after assignment to a parallel worker.

        Called after `prep_parallel()` per worker process.

        Intended to regenerate in-memory caches or other performance orientated features.

        Where changes are not needed, the current store SHOULD be returned unchanged.
        """
        return
