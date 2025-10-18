import pytest

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat


class TestMakeBasCat:
    """Tests for `make_bas_cat()` preset."""

    def test_default(self):
        """Can make an identifier for an item."""
        value = "x"
        expected = Identifier(
            identifier=value, href=f"https://data.bas.ac.uk/items/{value}", namespace="data.bas.ac.uk"
        )

        result = make_bas_cat(value)
        assert result == expected

    def test_no_id(self):
        """Can't make an identifier when an item isn't specified."""
        with pytest.raises(ValueError, match=r"Item identifier is required"):
            # noinspection PyTypeChecker
            _ = make_bas_cat(None)
