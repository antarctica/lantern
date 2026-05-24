from lantern.lib.metadata_library.models.record.presets.constraints import (
    BAS_ACCESS,
    CC_BY_ND_V4,
    CLOSED_ACCESS,
    MAGIC_PRODUCTS_V1,
    OGL_V3,
    OPEN_ACCESS,
)


class TestOpenAccess:
    """Test `OPEN_ACCESS` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = OPEN_ACCESS
        assert result.statement == "Open Access (Anonymous)"


class TestClosedAccess:
    """Test `CLOSED_ACCESS` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = CLOSED_ACCESS
        assert result.statement == "Closed Access (Restricted)"


class TestBasAccess:
    """Test `BAS_ACCESS` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = BAS_ACCESS
        assert result.statement == "Closed Access (BAS Staff)"


class TestOglV3:
    """Test `OGL_V3` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = OGL_V3
        assert result.href == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"


class TestCcByNdV4:
    """Test `CC_BY_ND_V4` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = CC_BY_ND_V4
        assert result.href == "https://creativecommons.org/licenses/by-nd/4.0/"


class TestMagicProductsV1:
    """Test `MagicProductsV1` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = MAGIC_PRODUCTS_V1
        assert result.href == "https://metadata-resources.data.bas.ac.uk/licences/magic-products-v1/"
