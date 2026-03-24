import logging

import pytest

from lantern.exporters.base import ExporterBase
from tests.resources.exporters.fake_exporters import FakeExporterBase


class TestBaseExporter:
    """Test base exporter via fake exporter class."""

    @pytest.mark.cov()
    def test_init(self, fx_logger: logging.Logger):
        """Can create an exporter."""
        base = FakeExporterBase(logger=fx_logger)
        assert isinstance(base, ExporterBase)
        assert base.name == "Fake Base"

    @pytest.mark.cov()
    def test_export(self, fx_logger: logging.Logger):
        """Can export some content."""
        base = FakeExporterBase(logger=fx_logger)
        base.export(content=[])
