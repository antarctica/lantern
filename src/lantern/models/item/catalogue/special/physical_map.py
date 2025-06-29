from collections.abc import Callable
from typing import Any

from lantern.models.item.catalogue import AdditionalInfoTab as CatalogueAdditionalInfoTab
from lantern.models.item.catalogue import Extent as CatalogueExtent
from lantern.models.item.catalogue import ExtentTab as CatalogueExtentTab
from lantern.models.item.catalogue import ItemCatalogue
from lantern.models.item.catalogue.elements import ItemSummaryCatalogue
from lantern.models.record import Record
from lantern.models.record.elements.identification import GraphicOverviews
from lantern.models.record.enums import AggregationAssociationCode, AggregationInitiativeCode, HierarchyLevelCode
from lantern.models.record.summary import RecordSummary


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

    Extends catalogue item additional info tab to include a list of scales (corresponding to each map side).
    """

    def __init__(self, scales: list[int | None], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._scales = scales

    @property
    def scales(self) -> list[str]:
        """Formatted scales if set."""
        scales = [self._format_scale(scale) for scale in self._scales]
        return [f"{scale} (Side {side_index_label(i)})" for i, scale in enumerate(scales)]


class ItemCataloguePhysicalMap(ItemCatalogue):
    """
    Special form of ItemCatalogue for physical maps.

    Represents a physical map with multiple sides (typically 2 but could be more for say an atlas).

    Extends catalogue items to get (product) records representing each side and use these to configure:
    - the extents tab to show multiple extents
    - the additional info tab to show multiple scales
    - graphic overviews to include those from each side
    - item summaries for each side
    """

    def __init__(self, get_record: Callable[[str], Record], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._get_record = get_record

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
    def _sides(self) -> list[Record]:
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
                    embedded_maps_endpoint=self._config.EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT,
                )
                extents.append(bounding_extent)

        return ExtentTab(extents=extents)

    @property
    def _additional_info(self) -> AdditionalInfoTab:
        """
        Additional info tab.

        Adapted to handle a set of scales for each side of a physical map.
        """
        kwargs = {k.lstrip("_"): v for k, v in super()._additional_info.__dict__.items()}
        scales = [side.identification.spatial_resolution for side in self._sides]
        return AdditionalInfoTab(scales=scales, **kwargs)

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
    def sides(self) -> list[tuple[str, ItemSummaryCatalogue]]:
        """Item summaries for the items that make up the physical map."""
        return [
            (f"Side {side_index_label(i)}", ItemSummaryCatalogue(RecordSummary.loads(side)))
            for i, side in enumerate(self._sides)
        ]
