import logging
from pathlib import Path

import pytest

from lantern.exporters.local import LocalExporter
from lantern.models.site import SiteContent


class TestLocalExporter:
    """Test local exporter."""

    def test_init(self, fx_logger: logging.Logger):
        """Can create a local exporter."""
        local = LocalExporter(logger=fx_logger, path=Path("x"))
        assert isinstance(local, LocalExporter)
        assert local.name == "Local Filesystem"

    @pytest.mark.parametrize("mode_d", [0o755, 0o770])
    @pytest.mark.parametrize("mode_f", [0o644, 0o660])
    def test_export(
        self,
        fx_local_exporter: LocalExporter,
        fx_site_content: SiteContent,
        mode_d: int,
        mode_f: int,
    ):
        """Can export some content with optional file and directory modes."""
        fx_local_exporter._mode_dir = mode_d
        fx_local_exporter._mode_file = mode_f
        fx_site_content.path = Path("d_0/d_1/f.txt")

        assert not fx_local_exporter.base_path.exists()
        fx_local_exporter.export(content=[fx_site_content])
        assert fx_local_exporter.base_path.joinpath(fx_site_content.path).exists()
        d0_raw_mode = fx_local_exporter.base_path.joinpath(fx_site_content.path).parent.stat().st_mode
        d1_raw_mode = fx_local_exporter.base_path.joinpath(fx_site_content.path).parent.parent.stat().st_mode
        f_raw_mode = fx_local_exporter.base_path.joinpath(fx_site_content.path).stat().st_mode
        assert d0_raw_mode & 0o777 == mode_d
        assert d1_raw_mode & 0o777 == mode_d
        assert f_raw_mode & 0o777 == mode_f

    @pytest.mark.cov()
    @pytest.mark.parametrize("meta", [False, True])
    @pytest.mark.parametrize("redirect", [False, True])
    def test_export_meta_logging(
        self,
        caplog: pytest.LogCaptureFixture,
        fx_local_exporter: LocalExporter,
        fx_site_content: SiteContent,
        meta: bool,
        redirect: bool,
    ):
        """Can log any object metadata that can't be set on the filesystem."""
        caplog.at_level(logging.DEBUG)
        if meta:
            fx_site_content.object_meta = {"x": "x"}
        if redirect:
            fx_site_content.redirect = "x"

        fx_local_exporter.export(content=[fx_site_content])
        if meta or redirect:
            assert "Additional properties for" in caplog.text
        else:
            assert "Additional properties for" not in caplog.text
