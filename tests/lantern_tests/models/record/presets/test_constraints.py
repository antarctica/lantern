from lantern.models.record.presets.constraints import OGL_V3, OPEN_ACCESS


class TestOpenAccess:
    """Test `OPEN_ACCESS` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = OPEN_ACCESS
        assert result.statement == "Open Access (Anonymous)"


class TestOglV3:
    """Test `OGL_V3` preset constant."""

    def test_default(self):
        """Can get constant."""
        result = OGL_V3
        assert result.href == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
