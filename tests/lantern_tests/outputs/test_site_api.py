import json
from pathlib import Path
from typing import TYPE_CHECKING

from lantern.outputs.site_api import SiteApiOutput
from tests.conftest import _index_site_entries

if TYPE_CHECKING:
    import logging

    from lantern.models.site import ExportMeta


class TestSiteApiOutput:
    """Test site API output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site API output."""
        output = SiteApiOutput(logger=fx_logger, meta=fx_export_meta)
        assert isinstance(output, SiteApiOutput)

    def test_entries(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content entries."""
        output = SiteApiOutput(logger=fx_logger, meta=fx_export_meta)
        results = _index_site_entries(output.entries)
        assert len(results) > 1

        catalog_redirect = results[Path(".well-known/api-catalog")]
        assert catalog_redirect.redirect == "https://example.com/static/json/api-catalog.json"

        docs_output = results[Path("guides/api/index.html")]
        docs_output.media_type = "text/html"
        assert docs_output.object_meta == {"build_key": fx_export_meta.build_key}

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        output = SiteApiOutput(logger=fx_logger, meta=fx_export_meta)
        results = _index_site_entries(output.content)

        catalog_output = results[Path("static/json/api-catalog.json")]
        # noinspection unresolved-references
        assert "linkset" in json.loads(catalog_output.content)
        assert catalog_output.media_type == "application/linkset+json; profile=https://www.rfc-editor.org/info/rfc9727"

        openapi_output = results[Path("static/json/openapi.json")]
        # noinspection unresolved-references
        assert "openapi" in json.loads(openapi_output.content)
        assert openapi_output.media_type == "application/vnd.oai.openapi+json;version=3.1"
