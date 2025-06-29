from datetime import datetime

from lantern.models.record.elements.common import Date
from lantern.models.record.elements.identification import BoundingBox, ExtentGeographic, ExtentTemporal, TemporalPeriod


def make_bbox_extent(min_x: float, max_x: float, min_y: float, max_y: float) -> ExtentGeographic:
    """Bounding box geographic extent."""
    return ExtentGeographic(
        bounding_box=BoundingBox(west_longitude=min_x, east_longitude=max_x, south_latitude=min_y, north_latitude=max_y)
    )


def make_temporal_extent(start: datetime, end: datetime) -> ExtentTemporal:
    """Temporal extent."""
    return ExtentTemporal(period=TemporalPeriod(start=Date(date=start), end=Date(date=end)))
