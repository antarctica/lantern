from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS


class TestOpenAccess:
    """Test `OPEN_ACCESS` preset admin permission."""

    def test_default(self):
        """Can get constant."""
        result = OPEN_ACCESS
        assert result.comments == "For public release."


class TestBasStaff:
    """Test `BAS_STAFF` preset admin permission."""

    def test_default(self):
        """Can get constant."""
        result = BAS_STAFF
        assert result.comments == "Restricted to staff employed by UKRI at BAS."
