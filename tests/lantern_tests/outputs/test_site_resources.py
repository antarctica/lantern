from pathlib import Path
from typing import TYPE_CHECKING

from lantern.outputs.site_resources import SiteResourcesOutput
from tests.conftest import _index_site_entries

if TYPE_CHECKING:
    import logging

    from lantern.models.site import ExportMeta


class TestSiteResourcesOutput:
    """Test site resources output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site resources output."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        assert isinstance(output, SiteResourcesOutput)

    def test_entries(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content entries."""
        expected_path_media = {
            Path("favicon.ico"): "image/x-icon",
            Path("robots.txt"): "text/plain",
            Path("static/css/main.css"): "text/css",
            Path("static/fonts/work-sans.ttf"): "font/ttf",
            Path("static/fonts/work-sans-italic.ttf"): "font/ttf",
            Path("static/img/favicon.ico"): "image/x-icon",
            Path("static/img/favicon.svg"): "image/svg+xml",
            Path("static/img/favicon-192.png"): "image/png",
            Path("static/img/favicon-512.png"): "image/png",
            Path("static/img/favicon-mask.png"): "image/png",
            Path("static/img/apple-touch-icon.png"): "image/png",
            Path("static/img/item-default-dark.png"): "image/png",
            Path("static/img/item-default-light.png"): "image/png",
            Path("static/txt/heartbeat.txt"): "text/plain",
            Path("static/txt/security.txt"): "text/plain",
            Path("static/js/enhancements.js"): "application/javascript",
            Path("static/js/lib/scalar.min.js"): "application/javascript",
            Path("static/json/manifest.webmanifest"): "application/manifest+json",
        }

        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        results = _index_site_entries(output.entries)

        assert len(results) > 1
        for path, media_type in expected_path_media.items():
            assert path in results
            result = results[path]
            assert result.media_type == media_type
            assert result.object_meta == {"build_key": fx_export_meta.build_key}

        catalog_redirect = results[Path(".well-known/security.txt")]
        assert catalog_redirect.redirect == "https://example.com/static/txt/security.txt"

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        results = _index_site_entries(output.content)
        # noinspection unresolved-references
        assert len(results[Path("robots.txt")].content) > 0
        assert isinstance(results[Path("robots.txt")].content, bytes)
        assert isinstance(results[Path("static/txt/robots.txt")].content, str)
        assert isinstance(results[Path("static/fonts/work-sans.ttf")].content, bytes)
        assert isinstance(results[Path("static/img/favicon.svg")].content, bytes)
        assert isinstance(results[Path("static/js/enhancements.js")].content, str)

    def test_entries_match_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Each resource group describes the same paths and metadata as its rendered content."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        assert [vars(entry) for entry in output.entries] == [
            {key: value for key, value in vars(item).items() if key != "content"} for item in output.content
        ]

    def test_checks(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate checks for a subset of content."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        results = output.checks
        assert len(results) == 6  # noqa: PLR2004

    def test_invalidation_keys(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate invalidation paths for content."""
        output = SiteResourcesOutput(logger=fx_logger, meta=fx_export_meta)
        assert output.invalidation_keys == ["/static/*"]
