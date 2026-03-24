from collections.abc import Collection

from lantern.exporters.base import ExporterBase
from lantern.models.site import SiteContent


class FakeExporterBase(ExporterBase):
    """Fake exporter for testing."""

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Fake Base"

    def export(self, content: Collection[SiteContent]) -> None:
        """Persist content."""
        pass
