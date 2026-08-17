import os
from typing import TYPE_CHECKING

import pytest

from lantern.contrib.site_checks import entrypoint

if TYPE_CHECKING:
    from pathlib import Path


class TestSiteChecks:
    """Test scheduled site checks contrib module."""

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_entrypoint(self, tmp_path: Path):
        """Can run site checks."""
        os.environ["LANTERN_STORE_GITLAB_CACHE_PATH"] = str(tmp_path)
        entrypoint()
