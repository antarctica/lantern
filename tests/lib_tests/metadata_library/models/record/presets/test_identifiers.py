import pytest

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat_alias, make_bas_cat_item


class TestMakeBasCatItem:
    """Tests for `make_bas_cat_item()` preset."""

    def test_default(self):
        """Can make an identifier for an item."""
        value = "x"
        expected = Identifier(
            identifier=value, href=f"https://lantern.data.bas.ac.uk/items/{value}", namespace="lantern.data.bas.ac.uk"
        )

        result = make_bas_cat_item(value)
        assert result == expected

    def test_no_id(self):
        """Can't make an identifier when an item isn't specified."""
        with pytest.raises(ValueError, match=r"Item identifier is required"):
            _ = make_bas_cat_item(None)


class TestMakeBasCatAlias:
    """Tests for `make_bas_cat_alias()` preset."""

    def test_default(self):
        """Can make an identifier for an alias."""
        value = "x/x"
        expected = Identifier(
            identifier=value,
            href=f"https://alias.lantern.data.bas.ac.uk/{value}",
            namespace="alias.lantern.data.bas.ac.uk",
        )

        result = make_bas_cat_alias(value)
        assert result == expected

    def test_no_id(self):
        """Can't make an identifier when an alias isn't specified."""
        with pytest.raises(ValueError, match=r"Alias is required"):
            _ = make_bas_cat_alias(None)
