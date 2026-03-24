import logging
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
        assert output.name == "Site Pages"

    def test_outputs(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
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
        outputs = _index_site_content_outputs(output.outputs)

        assert len(outputs) > 1
        for path in expected_paths:
            assert path in outputs
            result = outputs[path]
            assert result.object_meta == {"build_key": fx_export_meta.build_key}
            assert result.media_type == "text/html"
