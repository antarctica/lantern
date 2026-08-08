from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from lantern.models.site import ExportMeta, SiteContent, SiteRedirect
from lantern.outputs.redirects import RedirectsOutput

if TYPE_CHECKING:
    import logging


class TestChecksOutput:
    """Test redirects output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_site_content: SiteContent):
        """Can create a checks output."""
        output = RedirectsOutput(logger=fx_logger, meta=fx_export_meta, content=[fx_site_content])
        assert isinstance(output, RedirectsOutput)

    @pytest.mark.cov()
    @pytest.mark.parametrize("build_ref", [True, False])
    def test_object_meta(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_site_content: SiteContent, build_ref: bool
    ):
        """Can get object metadata if build_ref is available."""
        if not build_ref:
            fx_export_meta.build_repo_ref = None
        output = RedirectsOutput(logger=fx_logger, meta=fx_export_meta, content=[fx_site_content])
        object_meta = output._object_meta
        if build_ref:
            assert "build_ref" in object_meta
        else:
            assert "build_ref" not in object_meta

    @pytest.mark.parametrize("build_ref", [True, False])
    def test_data(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, build_ref: bool):
        """Can filter and process content into redirect tuples."""
        content = [
            SiteContent(content="x", path=Path("x"), media_type="x"),
            SiteContent(content="x", path=Path("x"), media_type="x", redirect=f"{fx_export_meta.base_url}/y"),
            SiteRedirect(path=Path("x/index.html"), target=f"{fx_export_meta.base_url}/y/index.html"),
        ]
        expected = [
            {
                "_build_ref": fx_export_meta.build_repo_ref if build_ref else "",
                "_build_time": fx_export_meta.build_time.isoformat(),
                "source": "x",
                "target": "https://example.com/y",
            },
            {
                "_build_ref": fx_export_meta.build_repo_ref if build_ref else "",
                "_build_time": fx_export_meta.build_time.isoformat(),
                "source": "x/index.html",
                "target": "https://example.com/y/index.html",
            },
            # to redirect pretty URLs
            {
                "_build_ref": fx_export_meta.build_repo_ref if build_ref else "",
                "_build_time": fx_export_meta.build_time.isoformat(),
                "source": "x/",
                "target": "https://example.com/y/index.html",
            },
            {
                "_build_ref": fx_export_meta.build_repo_ref if build_ref else "",
                "_build_time": fx_export_meta.build_time.isoformat(),
                "source": "x",
                "target": "https://example.com/y/index.html",
            },
        ]
        if not build_ref:
            fx_export_meta.build_repo_ref = None
            fx_export_meta.build_repo_url = None
        output = RedirectsOutput(logger=fx_logger, meta=fx_export_meta, content=content)

        results = output._data
        assert results == expected

    @pytest.mark.parametrize("has_redirects", [False, True])
    def test_raw_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, has_redirects: bool):
        """Can process redirect tuples into a CSV string."""
        content = SiteRedirect(path=Path("x"), target=f"{fx_export_meta.base_url}/y") if has_redirects else []
        expected = (
            f"source,target,_build_ref,_build_time\r\nx,https://example.com/y,83fake48,{fx_export_meta.build_time.isoformat()}"
            if has_redirects
            else ""
        )
        output = RedirectsOutput(
            logger=fx_logger,
            meta=fx_export_meta,
            content=[content],
        )
        results = output._content
        assert results == expected

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can generate site content items."""
        output = RedirectsOutput(
            logger=fx_logger,
            meta=fx_export_meta,
            content=[SiteRedirect(path=Path("x"), target=f"{fx_export_meta.base_url}/y")],
        )
        results = output.content
        assert len(results) == 1

        data = results[0]
        assert isinstance(data, SiteContent)
        assert data.path == Path("-/redirects.csv")
        assert data.media_type == "text/csv"
        assert "source,target,_build_ref,_build_time" in data.content
