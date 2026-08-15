from typing import TYPE_CHECKING

import pytest

from lantern.contrib.deployment_updates import entrypoint

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from lantern.models.site import SiteEnvironment


class TestHealthExport:
    """Test deployment site updates contrib module."""

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("env", ["testing", "live"])
    def test_entrypoint(self, mocker: MockerFixture, env: SiteEnvironment):
        """Can export site content."""
        # Rsync call for trusted content doesn't use requests etc. so not captured by VCR
        mock = mocker.MagicMock()
        mock.returncode = 0
        mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)

        entrypoint(env=env)
