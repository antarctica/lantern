import json
from json import JSONDecodeError
from typing import Any

from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.elements.common import Series
from lantern.lib.metadata_library.models.record.elements.identification import GraphicOverviews
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    HierarchyLevelCode,
)
from lantern.models.item.catalogue import AdditionalInfoTab as CatalogueAdditionalInfoTab
from lantern.models.item.catalogue import Extent as CatalogueExtent
from lantern.models.item.catalogue import ExtentTab as CatalogueExtentTab
from lantern.models.item.catalogue import ItemCatalogue
from lantern.models.item.catalogue.elements import ItemCatalogueSummary
from lantern.models.record.revision import RecordRevision


def side_index_label(index: int) -> str:
    """Return label for the side index (0 -> A, 27 -> AA etc.)."""
    number = index + 1
    label = ""
    while number > 0:
        number, rem = divmod(number - 1, 26)
        label = chr(ord("A") + rem) + label
    return label


class Extent(CatalogueExtent):
    """
    Special form of Extent for physical maps.

    Extends catalogue item extent to include a label for each extent (corresponding to each map side).
    """

    def __init__(self, label: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._label = label

    @property
    def label(self) -> str:
        """Extent label."""
        return self._label


class ExtentTab(CatalogueExtentTab):
    """
    Special form of ExtentTab for physical maps.

    Extends catalogue item extent tab to include a list of extents (corresponding to each map side).
    """

    def __init__(self, extents: list[Extent]) -> None:
        super().__init__()
        self._extents = extents

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return len(self._extents) > 0

    @property
    def extents(self) -> list[Extent]:
        """Extents for each side of a physical map."""
        return self._extents


class AdditionalInfoTab(CatalogueAdditionalInfoTab):
    """
    Special form of AdditionalInfoTab for physical maps.

    Extends tab with properties returning values for each side of a physical map (e.g. `scales`: scale in each side).

    Where properties are the same (or all None) for all sides, these properties should return None. Templates will try
    the plural properties first and fall back to the singular version.
    """

    def __init__(self, serieses: list[Series | None], scales: list[int | None], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._serieses = serieses
        self._scales = scales

    @staticmethod
    def _distinct_values(items: dict[int, str | None]) -> bool:
        """
        Check if values are distinct or all None.

        Where values is a side indexed dict of a given property (e.g. scales for each side).

        Util method to avoid duplicating logic.
        """
        distinct = set(items.values())
        return len(distinct) > 1 or distinct == {None}

    def _series_property(self, property_name: str) -> list[str | None] | None:
        """
        Get formatted property from series values for each side.

        Utility method to avoid duplicating logic.
        """
        items: dict[int, str | None] = {
            i: getattr(series, property_name) if series and getattr(series, property_name) else "-"
            for i, series in enumerate(self._serieses)
        }
        if not self._distinct_values(items):
            return None
        return [f"{value} (Side {side_index_label(i)})" for i, value in items.items()]

    @property
    def series_names(self) -> list[str | None] | None:
        """Formatted descriptive series names if set and all the same."""
        return self._series_property("name")

    @property
    def sheet_numbers(self) -> list[str | None] | None:
        """Formatted descriptive series sheet numbers if set and not all the same."""
        return self._series_property("page")

    @property
    def scales(self) -> list[str] | None:
        """Formatted scales if set."""
        if all(scale is None for scale in self._scales):
            return None
        items: dict[int, str | None] = {
            i: self._format_scale(scale) if scale else "-" for i, scale in enumerate(self._scales)
        }
        if not self._distinct_values(items):
            return None
        return [f"{value} (Side {side_index_label(i)})" for i, value in items.items()]


class ItemCataloguePhysicalMap(ItemCatalogue):
    """
    Special form of ItemCatalogue for physical maps.

    Represents a physical map with multiple sides (typically 2 but could be more for say an atlas).

    Extends catalogue items to get (product) records representing each side and use these to configure:
    - the extents tab to show multiple extents
    - the additional info tab to show multiple series, scales and other properties
    - graphic overviews to include those from each side
    - item summaries for each side
    """

    @classmethod
    def matches(cls, record: Record) -> bool:
        """Whether this class matches the record."""
        if record.hierarchy_level != HierarchyLevelCode.PAPER_MAP_PRODUCT:
            return False
        return (
            len(
                record.identification.aggregations.filter(
                    associations=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiatives=AggregationInitiativeCode.PAPER_MAP,
                )
            )
            > 0
        )

    @property
    def _sides(self) -> list[RecordRevision]:
        """Records that make up the sides/pages of a physical map."""
        side_identifiers = self._record.identification.aggregations.filter(
            associations=AggregationAssociationCode.IS_COMPOSED_OF,
            initiatives=AggregationInitiativeCode.PAPER_MAP,
        )
        return [self._get_record(side_identifier.identifier.identifier) for side_identifier in side_identifiers]

    @property
    def _extent(self) -> ExtentTab:
        """
        Extent tab.

        Adapted to handle a set of extents for each side of a physical map.
        Note the extent for the combined physical map record is excluded.
        """
        extents = []
        for i, side in enumerate(self._sides):
            label = f"Side {side_index_label(i)}"
            bounding_extents = side.identification.extents.filter(identifier="bounding")
            bounding_extent = bounding_extents[0] if bounding_extents else None
            if bounding_extent:
                bounding_extent = Extent(
                    label=label,
                    extent=bounding_extent,
                    embedded_maps_endpoint=self._config.TEMPLATES_ITEM_MAPS_ENDPOINT,
                )
                extents.append(bounding_extent)

        return ExtentTab(extents=extents)

    @property
    def _additional_info(self) -> AdditionalInfoTab:
        """
        Additional info tab.

        Adapted to handle sets of values for each side of a physical map for specific properties.
        """
        kwargs = {k.lstrip("_"): v for k, v in super()._additional_info.__dict__.items()}

        # Workaround for series.page being set by supplemental information in V4 config
        for side in self._sides:
            if side.identification.supplemental_information is None:
                continue
            try:
                sup_info = json.loads(side.identification.supplemental_information)
            except JSONDecodeError:
                continue
            if "sheet_number" in sup_info:
                side.identification.series.page = sup_info["sheet_number"]

        series: list[Series] = [side.identification.series for side in self._sides]
        scales = [side.identification.spatial_resolution for side in self._sides]
        return AdditionalInfoTab(serieses=series, scales=scales, **kwargs)

    @property
    def graphics(self) -> GraphicOverviews:
        """Graphic overviews combined from the item and its sides."""
        return GraphicOverviews(
            [
                *self._record.identification.graphic_overviews,
                *(graphic for side in self._sides for graphic in side.identification.graphic_overviews),
            ]
        )

    @property
    def sides(self) -> list[tuple[str, ItemCatalogueSummary]]:
        """Item summaries for the items that make up the physical map."""
        return [(f"Side {side_index_label(i)}", ItemCatalogueSummary(side)) for i, side in enumerate(self._sides)]
