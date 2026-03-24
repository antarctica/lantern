import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from lantern.exporters.rsync import RsyncExporter
from lantern.models.site import SiteContent


class TestRsyncExporter:
    """Test rsync exporter."""

    def test_init(self, fx_logger: logging.Logger):
        """Can create a rsync exporter."""
        rsync = RsyncExporter(logger=fx_logger, path=Path("x"))
        assert isinstance(rsync, RsyncExporter)
        assert rsync.name == "Rsync"

    @pytest.mark.parametrize("exists", [True, False])
    def test_export_local(self, fx_rsync_exporter: RsyncExporter, fx_site_content: SiteContent, exists: bool):
        """Can export some content locally, creating target path if needed."""
        if exists:
            fx_rsync_exporter._path.mkdir(parents=True, exist_ok=True)
            assert fx_rsync_exporter._path.exists()
        else:
            assert not fx_rsync_exporter._path.exists()

        fx_rsync_exporter.export(content=[fx_site_content])
        assert fx_rsync_exporter._path.joinpath(fx_site_content.path).exists()

    def test_export_remote(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """
        Can generate expected rsync command for export.

        Mocked to allow simulating remote uploads.
        """
        # mock rsync to prevent run and to capture constructed command
        mock = mocker.MagicMock()
        mock.returncode = 0
        mock_subproc = mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)

        # mock ExporterLocal used in ExporterRsync.export to use known (fake) path
        fake_local_instance = mocker.MagicMock()
        fake_local_instance.base_path = Path("/SOURCE")
        mocker.patch("lantern.exporters.rsync.LocalExporter", return_value=fake_local_instance)

        host = "x"
        path = Path("/TARGET")
        expected_target = f"{host}:{path}"
        expected = f"rsync -rlD --no-perms --no-times /SOURCE/ {expected_target}"

        # can't use fx_rsync_exporter here as the mock for the internal local exporter won't apply
        rsync = RsyncExporter(logger=fx_logger, host=host, path=path)

        rsync.export(content=[])
        mock_subproc.assert_called_once_with(expected.split(" "), cwd=str(Path.cwd()), shell=False)
