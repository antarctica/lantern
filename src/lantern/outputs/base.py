import logging
from abc import ABC, abstractmethod

from lantern.models.checks import Check, CheckType
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.stores.base import SelectRecordsProtocol
from lantern.utils import get_jinja_env


class OutputBase(ABC):
    """
    Abstract base class for Outputs.

    Outputs are responsible for producing:
    - one or more items of SiteContent, to populate a Site
    - one or more Check items, corresponding to these SiteContent items

    (I.e. Outputs product content, and checks for ensuring that content exists correctly in an exported site).

    Outputs do not persist content, see Exporters.

    Some outputs are resource specific (Record, Item representations), termed 'individual' in other classes.
    Others are site wide (index, health endpoints), termed 'global' in other classes.

    This base Output class is intended to be generic with subclasses being more opinionated.

    Outputs include an ExportMetadata instance, which extends SiteMetadata to provide information such as whether a
    trusted context applies. SiteMetadata includes properties such as the build time and base URL.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, name: str, check_type: CheckType) -> None:
        self._logger = logger
        self._meta = meta
        self._name = name
        self._check_type = check_type

    @property
    def name(self) -> str:
        """Output name."""
        return self._name

    @property
    def check_type(self) -> CheckType:
        """Check type for output."""
        return self._check_type

    @property
    def _object_meta(self) -> dict[str, str]:
        """
        Optional key-value metadata to include alongside output content where supported.

        Ignored where not supported even if set. Supported in AWS S3 for example. Not supported for POSIX file systems.
        """
        return {}

    @property
    @abstractmethod
    def content(self) -> list[SiteContent]:
        """Output content."""
        ...

    @property
    def checks(self) -> list[Check]:
        """Output checks."""
        return [
            Check.from_site_content(content=c, check_type=self._check_type, base_url=self._meta.base_url)
            for c in self.content
        ]


class OutputSite(OutputBase, ABC):
    """Outputs relating to the overall static site."""

    def __init__(self, logger: logging.Logger, meta: ExportMeta, name: str, check_type: CheckType) -> None:
        super().__init__(logger=logger, meta=meta, name=name, check_type=check_type)
        self._jinja = get_jinja_env()


class OutputRecord(OutputBase, ABC):
    """Outputs relating to processing a target record."""

    def __init__(
        self, logger: logging.Logger, meta: ExportMeta, name: str, check_type: CheckType, record: RecordRevision
    ) -> None:
        super().__init__(logger=logger, meta=meta, name=name, check_type=check_type)
        self._record = record
        self._strip_admin = not self._meta.trusted


class OutputRecords(OutputBase, ABC):
    """Outputs relating to processing multiple records."""

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        name: str,
        check_type: CheckType,
        select_records: SelectRecordsProtocol,
    ) -> None:
        super().__init__(logger=logger, meta=meta, name=name, check_type=check_type)
        self._select_records = select_records
