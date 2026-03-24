from lantern.models.site import SiteContent
from lantern.outputs.base import OutputBase, OutputRecord, OutputRecords, OutputSite


class FakeOutputBase(OutputBase):
    """Fake output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Base"

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content."""
        return []


class FakeOutputSite(OutputSite):
    """Fake site output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Site"

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content."""
        return []


class FakeOutputRecord(OutputRecord):
    """Fake record output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Record"

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content."""
        return []


class FakeOutputRecords(OutputRecords):
    """Fake records output for testing."""

    @property
    def name(self) -> str:
        """Output name."""
        return "Fake Records"

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content."""
        return []
