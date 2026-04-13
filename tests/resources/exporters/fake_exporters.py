import logging
from collections.abc import Collection

from lantern.exporters.base import ExporterBase
from lantern.models.site import SiteContent


class FakeExporterBase(ExporterBase):
    """Fake exporter for testing."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger, name="Fake Base")

    def export(self, content: Collection[SiteContent]) -> None:
        """Persist content."""
        pass
