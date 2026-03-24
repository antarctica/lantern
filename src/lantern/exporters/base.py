import logging
from abc import ABC, abstractmethod
from collections.abc import Collection

from lantern.models.site import SiteContent


class ExporterBase(ABC):
    """
    Abstract base class for exporters.

    Exporters persist content created by Outputs as files or objects in a storage system, such as a local or remote
    Posix file system or object store such as AWS S3.

    Some providers act at a site level, such as SiteExporter (which coordinates other exporters).

    This base exporter class is intended to be generic with subclasses being more opinionated.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialise."""
        self._logger = logger

    @property
    @abstractmethod
    def name(self) -> str:
        """Exporter name."""
        ...

    @abstractmethod
    def export(self, content: Collection[SiteContent]) -> None:
        """Persist content."""
        ...
