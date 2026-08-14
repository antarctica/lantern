import pytest

from lantern.contrib.health_export import entrypoint


class TestHealthExport:
    """Test health export contrib module."""

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_entrypoint(self):
        """Can run site checks."""
        entrypoint()
