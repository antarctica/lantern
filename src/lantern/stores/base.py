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


class StoreBase(ABC):
    """
    Abstract base class for stores.

    Stores manage Records held in a temporary or permanent storage system, such as an in-memory dict or remote database.

    This class defines the abstract interface Stores must implement to manage Records and RecordSummaries.
    """

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of records a store contains."""
        ...

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

    @abstractmethod
    def freeze(self) -> None:
        """
        Attempt to freeze store.

        Raises `StoreFrozenUnsupportedError` if not supported.
        """
        ...

    def prep_parallel(self) -> StoreBase:
        """
        Return store configured for use in parallel jobs.

        Stores are pickled for each parallel job, which may be inefficient for e.g. in-memory state.

        Where applicable, stores SHOULD exclude or otherwise mitigate such overheads within a returned copy.
        Stores MUST NOT modify the current instance, as it remains in use by the calling process.

        Paired with `restore_parallel()`, which recreates any excluded state for each worker process.

        Where this is not a problem, the current store SHOULD be returned unchanged.
        """
        return self

    def restore_parallel(self) -> None:
        """
        Rebuild any state excluded by `prep_parallel()`.

        Called once per worker process if needed, otherwise this method SHOULD not be overridden.
        """
        return


class SelectRecordsProtocol(Protocol):
    """Callable protocol for selecting records from Store."""

    def __call__(  # pragma: no branch  # noqa: D102
        self, file_identifiers: set[str] | None = None
    ) -> list[RecordRevision]: ...


class SelectRecordProtocol(Protocol):
    """Callable protocol for selecting a record from Store."""

    def __call__(self, file_identifier: str) -> RecordRevision: ...  # pragma: no branch  # noqa: D102
