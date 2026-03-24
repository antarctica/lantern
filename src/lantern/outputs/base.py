import logging
from abc import ABC, abstractmethod

from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.stores.base import SelectRecordsProtocol
from lantern.utils import get_jinja_env


class OutputBase(ABC):
    """
    Abstract base class for outputs.

    Output are responsible for producing one or more pieces of SiteContent to populate the catalogue static site.
    Some outputs are resource specific (Record, Item representations), others are site wide (index, health endpoints).

    Outputs do not persist content, see Exporters.

    This base Output class is intended to be generic with subclasses being more opinionated.

    Outputs include an ExportMetadata instance which extends SiteMetadata to provide information such as whether a
    trusted context applies, as well as SiteMetadata such as the build time.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        """Initialise."""
        self._logger = logger
        self._meta = meta

    @property
    @abstractmethod
    def name(self) -> str:
        """Output name."""
        ...

    @property
    def _object_meta(self) -> dict[str, str]:
        """
        Optional key-value metadata to include alongside output content where supported.

        Ignored where not supported even if set. Supported in AWS S3 for example. Not supported for POSIX file systems.
        """
        return {}

    @property
    @abstractmethod
    def outputs(self) -> list[SiteContent]:
        """Output content."""
        ...


class OutputSite(OutputBase, ABC):
    """Outputs relating to the overall static site."""

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        """Initialise."""
        super().__init__(logger=logger, meta=meta)
        self._jinja = get_jinja_env()


class OutputRecord(OutputBase, ABC):
    """Outputs relating to processing a target record."""

    def __init__(self, logger: logging.Logger, meta: ExportMeta, record: RecordRevision) -> None:
        """Initialise."""
        super().__init__(logger=logger, meta=meta)
        self._record = record
        self._strip_admin = not self._meta.trusted


class OutputRecords(OutputBase, ABC):
    """Outputs relating to processing multiple records."""

    def __init__(self, logger: logging.Logger, meta: ExportMeta, select_records: SelectRecordsProtocol) -> None:
        """Initialise."""
        super().__init__(logger=logger, meta=meta)
        self._select_records = select_records
