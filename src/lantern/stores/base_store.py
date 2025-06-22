from abc import ABC, abstractmethod

from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary


class Store(ABC):
    """
    Base representation of a container for resources within the BAS Data Catalogue / Metadata ecosystem.

    Stores manage a set of Records using some form of temporary or more permanent storage, such as an in-memory dict
    or a remote database.

    This class defines the abstract interface Stores must implement to load, remove, and access stored Records and
    RecordSummaries.
    """

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
    def purge(self) -> None:
        """Empty records from store."""
        ...

    @abstractmethod
    def loads(self, *args: list) -> None:
        """Populate store with record(s)."""
        ...
