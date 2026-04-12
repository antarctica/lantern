import logging
from pathlib import Path

from lantern.models.site import ExportMeta
from lantern.outputs.site_resources import SiteResourcesOutput
from tests.conftest import _index_site_content_outputs


class TestSiteResourcesOutput:
    """Test site resources output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site resources output."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        assert isinstance(output, SiteResourcesOutput)

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        expected_path_media = {
            Path("static/css/main.css"): "text/css",
            Path("static/fonts/work-sans.ttf"): "font/ttf",
            Path("static/fonts/work-sans-italic.ttf"): "font/ttf",
            Path("favicon.ico"): "image/x-icon",
            Path("static/img/favicon.svg"): "image/svg+xml",
            Path("static/img/favicon-192.png"): "image/png",
            Path("static/img/favicon-512.png"): "image/png",
            Path("static/img/favicon-mask.png"): "image/png",
            Path("static/img/apple-touch-icon.png"): "image/png",
            Path("static/txt/heartbeat.txt"): "text/plain",
            Path("static/js/enhancements.js"): "application/javascript",
            Path("static/js/lib/scalar.min.js"): "application/javascript",
            Path("static/json/manifest.webmanifest"): "application/manifest+json",
        }

        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        outputs = _index_site_content_outputs(output.content)

        assert len(outputs) > 1
        for path, media_type in expected_path_media.items():
            assert path in outputs
            result = outputs[path]
            assert result.media_type == media_type
            assert result.object_meta == {"build_key": fx_export_meta.build_key}

    def test_checks(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate checks for a subset of content."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        checks = output.checks
        assert len(checks) == 3
