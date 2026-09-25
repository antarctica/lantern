import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from lantern.outputs.site_health import SiteHealthOutput, SiteHealthOutputComponentValues
from tests.conftest import _index_site_entries

if TYPE_CHECKING:
    import logging

    from lantern.models.site import ExportMeta


class TestSiteHealthOutput:
    """Test site health output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site health output."""
        component_values = SiteHealthOutputComponentValues(
            site_records_count=1,
            search_records_count=1,
            entra_client_secret_expiry=date(2014, 6, 30),
            entra_client_secret_id="x",  # noqa: S106
        )
        output = SiteHealthOutput(logger=fx_logger, meta=fx_export_meta, component_values=component_values)
        assert isinstance(output, SiteHealthOutput)

    def test_entries(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content entries."""
        build_ref = "x"
        fx_export_meta.build_repo_ref = build_ref
        component_values = SiteHealthOutputComponentValues(
            site_records_count=1,
            search_records_count=1,
            entra_client_secret_expiry=date(2014, 6, 30),
            entra_client_secret_id="x",  # noqa: S106
        )

        output = SiteHealthOutput(logger=fx_logger, meta=fx_export_meta, component_values=component_values)
        results = _index_site_entries(output.entries)
        assert len(results) > 1

        catalog_redirect = results[Path("-/health")]
        assert catalog_redirect.redirect == "https://example.com/static/json/health.json"

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        build_ref = "x"
        fx_export_meta.build_repo_ref = build_ref
        component_values = SiteHealthOutputComponentValues(
            site_records_count=1,
            search_records_count=1,
            entra_client_secret_expiry=date(2014, 6, 30),
            entra_client_secret_id="x",  # noqa: S106
        )

        output = SiteHealthOutput(logger=fx_logger, meta=fx_export_meta, component_values=component_values)
        results = _index_site_entries(output.content)

        health_output = results[Path("static/json/health.json")]
        # noinspection unresolved-references
        health_data = json.loads(health_output.content)
        assert "description" in health_data
        assert health_data["checks"]["site:records"]["observedValue"] == 1
        assert health_data["checks"]["search:records"]["observedValue"] == 1
        assert health_output.media_type == "application/health+json"
