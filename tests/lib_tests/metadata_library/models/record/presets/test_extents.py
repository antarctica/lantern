from datetime import UTC, date, datetime

import pytest

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.identification import (
    BoundingBox,
    ExtentGeographic,
    ExtentTemporal,
    TemporalPeriod,
)
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent


class TestMakeBboxExtent:
    """Tests for `make_bbox_extent()` preset."""

    def test_default(self):
        """Can make a valid ExtentGeographic element using a bbox."""
        min_x = 1.0
        max_x = 2.0
        min_y = 3.0
        max_y = 4.0
        expected = ExtentGeographic(
            bounding_box=BoundingBox(
                west_longitude=min_x, east_longitude=max_x, south_latitude=min_y, north_latitude=max_y
            )
        )
        result = make_bbox_extent(min_x, max_x, min_y, max_y)

        assert result == expected


class TestMakeTemporalExtent:
    """Tests for `make_temporal_extent()` preset."""

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                {"start": date(2014, 6, 30), "end": date(2014, 7, 1)},
                ExtentTemporal(
                    period=TemporalPeriod(start=Date(date=date(2014, 6, 30)), end=Date(date=date(2014, 7, 1)))
                ),
            ),
            (
                {"start": datetime(2014, 6, 30, tzinfo=UTC), "end": datetime(2014, 7, 1, tzinfo=UTC)},
                ExtentTemporal(
                    period=TemporalPeriod(
                        start=Date(date=datetime(2014, 6, 30, tzinfo=UTC)),
                        end=Date(date=datetime(2014, 7, 1, tzinfo=UTC)),
                    )
                ),
            ),
        ],
    )
    def test_default(self, values: dict, expected: ExtentTemporal):
        """Can make a valid ExtentTemporal element using a start and end datetime."""
        result = make_temporal_extent(**values)
        assert result == expected
