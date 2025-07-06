from abc import ABC, abstractmethod

from lantern.models.record import Record
from lantern.models.record.summary import RecordSummary


class RecordNotFoundError(Exception):
    """Raised when a record cannot be retrieved."""

    def __init__(self, file_identifier: str) -> None:
        self.file_identifier = file_identifier

    def __str__(self) -> str:
        """Exception string representation."""
        return f"Record '{self.file_identifier}' not found."


class Store(ABC):
    """
    Base representation for a container of resources.

    Stores manage Records held in a temporary or permanent storage system, such as an in-memory dict or remote database.

    This class defines the abstract interface Stores must implement to manage Records and RecordSummaries.
    """

    @abstractmethod
    def __len__(self) -> int:
        """Record count."""
        ...

    @property
    @abstractmethod
    def summaries(self) -> list[RecordSummary]:
        """All record summaries."""
        ...

    @property
    @abstractmethod
    def records(self) -> list[Record]:
        """All records."""
        ...

    @abstractmethod
    def get(self, file_identifier: str) -> Record:
        """Return a specific record or raise a RecordNotFoundError."""
        ...
