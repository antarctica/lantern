import logging

from lantern.models.checks import CheckType
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputBase, OutputRecord, OutputRecords, OutputSite


class FakeOutputBase(OutputBase):
    """Fake output for testing."""

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        super().__init__(logger, meta, name="Fake Base", check_type=CheckType.NONE)

    @property
    def content(self) -> list[SiteContent]:
        """Output content."""
        return []


class FakeOutputSite(OutputSite):
    """Fake site output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Site"

    @property
    def content(self) -> list[SiteContent]:
        """Output content."""
        return []


class FakeOutputRecord(OutputRecord):
    """Fake record output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Record"

    @property
    def content(self) -> list[SiteContent]:
        """Output content."""
        return []


class FakeOutputRecords(OutputRecords):
    """Fake records output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Records"

    @property
    def content(self) -> list[SiteContent]:
        """Output content."""
        return []
