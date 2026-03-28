import json
import logging
from pathlib import Path

from lantern.models.site import ExportMeta
from lantern.outputs.site_health import SiteHealthOutput
from lantern.stores.base import SelectRecordsProtocol
from tests.conftest import _index_site_content_outputs


class TestSiteHealthOutput:
    """Test site health output."""

    def test_init(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records_fixed: SelectRecordsProtocol
    ):
        """Can create a site health output."""
        output = SiteHealthOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records_fixed)
        assert isinstance(output, SiteHealthOutput)
        assert output.name == "Site Health"

    def test_outputs(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records_fixed: SelectRecordsProtocol
    ):
        """Can generate site content items."""
        build_ref = "x"
        fx_export_meta.build_repo_ref = build_ref
        output = SiteHealthOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records_fixed)
        outputs = _index_site_content_outputs(output.outputs)
        assert len(outputs) > 1

        health_output = outputs[Path("static/json/health.json")]
        health_data = json.loads(health_output.content)
        assert "description" in health_data
        assert health_data["checks"]["site:records"]["observedValue"] == 1
        assert health_output.media_type == "application/health+json"

        catalog_redirect = outputs[Path("-/health")]
        assert catalog_redirect.redirect == "https://example.com/static/json/health.json"
