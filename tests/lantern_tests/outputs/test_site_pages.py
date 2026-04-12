import logging
from http import HTTPStatus
from pathlib import Path

from lantern.models.site import ExportMeta
from lantern.outputs.site_pages import SitePagesOutput
from tests.conftest import _index_site_content_outputs


class TestSitePagesOutput:
    """Test site pages output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site pages output."""
        output = SitePagesOutput(logger=fx_logger, meta=fx_export_meta)
        assert isinstance(output, SitePagesOutput)

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        expected_paths = [
            Path("404.html"),
            Path("legal/accessibility/index.html"),
            Path("legal/cookies/index.html"),
            Path("legal/copyright/index.html"),
            Path("legal/privacy/index.html"),
            Path("guides/formatting/index.html"),
            Path("guides/map-purchasing/index.html"),
        ]

        output = SitePagesOutput(logger=fx_logger, meta=fx_export_meta)
        content = _index_site_content_outputs(output.content)

        assert len(content) > 1
        for path in expected_paths:
            assert path in content
            result = content[path]
            assert result.object_meta == {"build_key": fx_export_meta.build_key}
            assert result.media_type == "text/html"

    def test_checks(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate additional checks for 404 error handling."""
        output = SitePagesOutput(logger=fx_logger, meta=fx_export_meta)
        content = output.content
        checks = output.checks
        assert len(checks) == len(content) + 1
        assert checks[-1].http_status == HTTPStatus.NOT_FOUND
