import json
import logging
from pathlib import Path

from lantern.models.site import ExportMeta
from lantern.outputs.site_api import SiteApiOutput
from tests.conftest import _index_site_content_outputs


class TestSiteApiOutput:
    """Test site API output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site API output."""
        output = SiteApiOutput(logger=fx_logger, meta=fx_export_meta)
        assert isinstance(output, SiteApiOutput)

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        output = SiteApiOutput(logger=fx_logger, meta=fx_export_meta)
        contents = _index_site_content_outputs(output.content)
        assert len(contents) > 1

        catalog_output = contents[Path("static/json/api-catalog.json")]
        assert "linkset" in json.loads(catalog_output.content)
        assert catalog_output.media_type == "application/linkset+json; profile=https://www.rfc-editor.org/info/rfc9727"

        catalog_redirect = contents[Path(".well-known/api-catalog")]
        assert catalog_redirect.redirect == "https://example.com/static/json/api-catalog.json"

        openapi_output = contents[Path("static/json/openapi.json")]
        assert "openapi" in json.loads(openapi_output.content)
        assert openapi_output.media_type == "application/vnd.oai.openapi+json;version=3.1"

        docs_output = contents[Path("guides/api/index.html")]
        docs_output.media_type = "text/html"
        assert docs_output.object_meta == {"build_key": fx_export_meta.build_key}
