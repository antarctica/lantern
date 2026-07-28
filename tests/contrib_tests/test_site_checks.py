import pytest

from lantern.contrib.site_checks import entrypoint


class TestSiteChecks:
    """Test scheduled site checks contrib module."""

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_entrypoint(self):
        """Can run site checks."""
        entrypoint()
