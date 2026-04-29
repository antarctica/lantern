import logging
from abc import ABC, abstractmethod
from collections.abc import Collection

from lantern.models.site import SiteContent


class ExporterBase(ABC):
    """
    Abstract base class for exporters.

    Exporters persist content created by Outputs as files or objects in a storage system, such as a local or remote
    Posix file system or object store such as AWS S3.

    This base exporter class is intended to be generic, with subclasses being more opinionated.
    """

    def __init__(self, logger: logging.Logger, name: str) -> None:
        self._logger = logger
        self._name = name

    @property
    def name(self) -> str:
        """Exporter name."""
        return self._name

    @abstractmethod
    def export(self, content: Collection[SiteContent]) -> None:
        """Persist content."""
        ...
