from copy import deepcopy
from datetime import UTC, datetime

import pytest

from lantern.config import Config
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.catalogue import Dates, Identifiers
from lantern.models.item.catalogue.elements import ItemSummaryCatalogue
from lantern.models.item.catalogue.special.physical_map import (
    AdditionalInfoTab,
    Extent,
    ExtentTab,
    ItemCataloguePhysicalMap,
    side_index_label,
)
from lantern.models.record import HierarchyLevelCode, Record
from lantern.models.record.elements.common import Date
from lantern.models.record.elements.common import Dates as RecordDates
from lantern.models.record.elements.common import Identifiers as RecordIdentifiers
from lantern.models.record.elements.identification import BoundingBox, ExtentGeographic, GraphicOverview
from lantern.models.record.elements.identification import Extent as RecordExtent
from lantern.models.record.enums import AggregationAssociationCode, AggregationInitiativeCode
from tests.conftest import _get_record, _get_record_summary


@pytest.mark.parametrize(("value", "expected"), [(0, "A"), (25, "Z"), (26, "AA")])
def test_side_index_label(value: int, expected: str) -> None:
    """Can get letter corresponding to an index."""
    assert side_index_label(value) == expected


class TestExtent:
    """Test catalogue physical map extent."""

    def test_init(self):
        """Can create an Extent element."""
        item_extent = ItemExtent(
            RecordExtent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
            )
        )

        extent = Extent(label="x", extent=item_extent, embedded_maps_endpoint="x")

        assert isinstance(extent, Extent)

    def test_label(self):
        """Can get extent label."""
        item_extent = ItemExtent(
            RecordExtent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
            )
        )

        extent = Extent(label="x", extent=item_extent, embedded_maps_endpoint="x")

        assert extent.label == "x"


class TestExtentTab:
    """Test catalogue physical map extent tab."""

    def test_init(self):
        """Can create an Extent tab."""
        a = Extent(
            label="A",
            extent=ItemExtent(
                RecordExtent(
                    identifier="bounding",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                )
            ),
            embedded_maps_endpoint="x",
        )
        b = deepcopy(a)
        b._label = "B"
        expected = [a, b]

        tab = ExtentTab(extents=expected)
        assert isinstance(tab, ExtentTab)
        assert tab.extents == expected

    @pytest.mark.parametrize("enabled", [True, False])
    def test_enabled(self, enabled: bool):
        """Can determine if tab is enabled based on extents."""
        extent = Extent(
            label="A",
            extent=ItemExtent(
                RecordExtent(
                    identifier="bounding",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                )
            ),
            embedded_maps_endpoint="x",
        )
        extents = [extent] if enabled else []

        tab = ExtentTab(extents=extents)
        assert tab.enabled == enabled


class TestAdditionalInfoTab:
    """Test catalogue physical map additional information tab."""

    def test_init(self):
        """Can create an AdditionalInformation tab."""
        item_id = "x"
        item_type = HierarchyLevelCode.PRODUCT
        identifiers = Identifiers(RecordIdentifiers([]))
        dates = Dates(dates=RecordDates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
        datestamp = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC).date()

        tab = AdditionalInfoTab(
            scales=[],
            item_id=item_id,
            item_type=item_type,
            identifiers=identifiers,
            dates=dates,
            datestamp=datestamp,
            kv={},
        )

        assert isinstance(tab, AdditionalInfoTab)

    def test_scales(self):
        """Can get multiple scales."""
        item_id = "x"
        item_type = HierarchyLevelCode.PRODUCT
        identifiers = Identifiers(RecordIdentifiers([]))
        dates = Dates(dates=RecordDates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
        datestamp = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC).date()

        tab = AdditionalInfoTab(
            scales=[1_000_000, 2_000_000],
            item_id=item_id,
            item_type=item_type,
            identifiers=identifiers,
            dates=dates,
            datestamp=datestamp,
            kv={},
        )

        assert tab.scales == ["1:1,000,000 (Side A)", "1:2,000,000 (Side B)"]


class TestItemCataloguePhysicalMap:
    """Test catalogue item."""

    def test_init(self, fx_config: Config, fx_record_minimal_item_catalogue_physical_map: Record):
        """Can create an ItemCatalogue."""
        item = ItemCataloguePhysicalMap(
            config=fx_config,
            record=fx_record_minimal_item_catalogue_physical_map,
            get_record=_get_record,
            get_record_summary=_get_record_summary,
        )

        assert isinstance(item, ItemCataloguePhysicalMap)
        assert item._record == fx_record_minimal_item_catalogue_physical_map

    @pytest.mark.parametrize("matches", [True, False])
    def test_matches(
        self,
        matches: bool,
        fx_record_minimal_item_catalogue_physical_map: Record,
        fx_record_minimal_item_catalogue: Record,
    ):
        """Can determine if record matches this subclass."""
        record = fx_record_minimal_item_catalogue_physical_map if matches else fx_record_minimal_item_catalogue
        assert ItemCataloguePhysicalMap.matches(record) == matches

    def test_sides(self, fx_config: Config, fx_item_catalogue_min_physical_map: ItemCataloguePhysicalMap):
        """Can get records representing the sides of a physical map."""
        expected = [
            _get_record(side.identifier.identifier)
            for side in fx_item_catalogue_min_physical_map._record.identification.aggregations.filter(
                associations=AggregationAssociationCode.IS_COMPOSED_OF,
                initiatives=AggregationInitiativeCode.PAPER_MAP,
            )
        ]

        assert fx_item_catalogue_min_physical_map._sides == expected

    def test_tabs(self, fx_item_catalogue_min_physical_map: ItemCataloguePhysicalMap):
        """Can get physical map specific tabs."""
        assert isinstance(fx_item_catalogue_min_physical_map._extent, ExtentTab)
        assert isinstance(fx_item_catalogue_min_physical_map._additional_info, AdditionalInfoTab)

    @staticmethod
    def _get_record_graphics(identifier: str) -> Record:
        """Extension of `_lib_get_record` to include graphic overviews."""
        record = _get_record(identifier=identifier)
        record.identification.graphic_overviews.append(GraphicOverview(identifier="x", href="x", mime_type="image/png"))
        return record

    def test_graphics(
        self,
        fx_config: Config,
        fx_record_minimal_item_catalogue_physical_map: Record,
        fx_get_record_summary: callable,
    ):
        """Can get any graphics for the physical map and each side."""
        fx_record_minimal_item_catalogue_physical_map.identification.graphic_overviews.append(
            GraphicOverview(identifier="x", href="x", mime_type="image/png")
        )
        item = ItemCataloguePhysicalMap(
            config=fx_config,
            record=fx_record_minimal_item_catalogue_physical_map,
            get_record=self._get_record_graphics,
            get_record_summary=_get_record_summary,
        )

        graphics = item.graphics
        assert len(graphics) > 1

    def test_side_summaries(self, fx_item_catalogue_min_physical_map: ItemCataloguePhysicalMap):
        """Can get ItemSummaries for each map side."""
        sides = fx_item_catalogue_min_physical_map.sides
        assert len(sides) > 0
        # assert sides are a tuple of (side_index, ItemSummaryCatalogue)
        assert all(
            isinstance(side, tuple) and len(side) == 2 and isinstance(side[1], ItemSummaryCatalogue) for side in sides
        )
        assert sides[0][0] == "Side A"
