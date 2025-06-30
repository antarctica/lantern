from datetime import date

from lantern.models.record.presets.projections import make_epsg_projection


class TestMakeEpsgProjection:
    """Tests for `make_epsg_projection()` preset."""

    def test_default(self):
        """Can make a CRS info element for an EPSG projection code."""
        value = "1"
        result = make_epsg_projection(value)

        assert result.code.value == f"urn:ogc:def:crs:EPSG::{value}"
        assert result.code.href == f"http://www.opengis.net/def/crs/EPSG/0/{value}"
        assert result.version == "6.18.3"
        assert result.authority.title == "European Petroleum Survey Group (EPSG) Geodetic Parameter Registry"
        assert result.authority.dates.publication.date == date(2008, 11, 12)
