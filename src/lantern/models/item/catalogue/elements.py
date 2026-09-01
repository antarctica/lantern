import json
from dataclasses import dataclass
from datetime import UTC, date, timedelta
from datetime import datetime as DateTime  # noqa: N812
from itertools import chain
from typing import TYPE_CHECKING, TypedDict, TypeVar

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.common import Dates as RecordDates
from lantern.lib.metadata_library.models.record.elements.common import Identifiers as RecordIdentifiers
from lantern.lib.metadata_library.models.record.elements.common import Maintenance as RecordMaintenance
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    DateTypeCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.elements import Link, unpack
from lantern.models.item.base.enums import ResourceTypeIcon, ResourceTypeLabel
from lantern.models.item.base.item import ItemSummaryBase
from lantern.models.item.base.utils import md_as_plain
from lantern.models.item.catalogue.enums import ItemSuperType
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.utils import is_live_record

if TYPE_CHECKING:
    from lantern.lib.metadata_library.models.record.elements.identification import Aggregations as RecordAggregations
    from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
    from lantern.stores.base import SelectRecordProtocol

TFormattedDate = TypeVar("TFormattedDate", bound="FormattedDate")


@dataclass(kw_only=True)
class FormattedDate:
    """Represents an HTML time element."""

    value: str
    datetime: str

    @classmethod
    def from_rec_date(cls: type[TFormattedDate], value: Date, relative_to: DateTime | None = None) -> FormattedDate:
        """
        Create a formatted date (time) from a Python value.

        Time elements consist of human-readable value and a machine-readable 'datetime' attribute.

        For time values:
        - a 'DD MMM YYYY' (e.g. 01 Oct 2023) representation is used where precision allows
        - where a value is within 24 hours of a reference point (defaults to now) the date and time is used

        For time 'datetime' attributes:
        - the relevant ISO 8601 representation is used (e.g. 2023-10-01T12:00:00+00:00)
        """
        if not isinstance(value, Date):
            msg = "Value must be a record Date object."
            raise TypeError(msg) from None

        dt = value.date.strftime("%Y-%m-%d")
        val = value.date.strftime("%d %B %Y")
        relative_to = relative_to or DateTime.now(tz=UTC)

        if isinstance(value.date, DateTime) and not relative_to - value.date > timedelta(hours=24):
            val = value.date.strftime("%d %B %Y %H:%M:%S %Z")
            dt = value.date.isoformat()
        if isinstance(value.date, date) and value.precision is DatePrecisionCode.YEAR:
            val = value.date.strftime("%Y")
            dt = str(value.date.year)
        if isinstance(value.date, date) and value.precision is DatePrecisionCode.MONTH:
            val = value.date.strftime("%B %Y")
            dt = value.date.strftime("%Y-%m")

        return cls(value=val, datetime=dt)


class ItemSummaryFragments(TypedDict):
    """Properties shown as part of an ItemSummaryCatalogue."""

    live: bool
    restricted: bool
    item_type_label: str
    item_type_icon: str
    edition: str | None
    published: FormattedDate | None
    children: str | None


class ItemCatalogueSummary(ItemSummaryBase):
    """
    Summary of a Catalogue item.

    Catalogue item summaries provide additional context for other catalogue items related to a current item.
    """

    @property
    def date_fmt(self) -> FormattedDate | None:
        """Formatted summary date, if available."""
        _date = self.date
        return FormattedDate.from_rec_date(_date) if _date else None

    @property
    def title_no_fmt(self) -> str:
        """Unformatted title, without any markup."""
        return md_as_plain(self.record.identification.title)

    @property
    def fragments(self) -> ItemSummaryFragments:
        """UI fragments (icons and labels) for item summary."""
        return ItemSummaryFragments(
            live=is_live_record(self.record),
            restricted=self.restricted,
            item_type_label=self.resource_type_label,
            item_type_icon=self.resource_type_icon,
            edition=self.edition_fmt,
            published=self.date_fmt,
            children=self.children,
        )

    @property
    def graphic_href(self) -> tuple[str, str]:
        """
        URL to an image representing the item, or a generic default.

        Returned as light mode, dark mode tuple.
        """
        item_graphic = super().graphic_href
        if item_graphic:
            return item_graphic, item_graphic
        defaults = [f"/static/img/item-default-{v}.png" for v in ["light", "dark"]][:2]
        return defaults[0], defaults[1]


class Aggregations:
    """
    Aggregations.

    Container for ItemBase Aggregations formatted as links and grouped by type.
    """

    def __init__(
        self,
        admin_meta_keys: AdministrationKeys | None,
        aggregations: RecordAggregations,
        select_record: SelectRecordProtocol,
    ) -> None:
        self._admin_keys = admin_meta_keys
        self._aggregations = aggregations
        self._summaries = self._generate_summaries(select_record)

    def _generate_summaries(self, select_record: SelectRecordProtocol) -> dict[str, ItemCatalogueSummary]:
        """Generate item summaries for aggregations indexed by resource identifier."""
        summaries = {}
        for aggregation in self._aggregations:
            identifier = aggregation.identifier.identifier
            summaries[identifier] = ItemCatalogueSummary(select_record(identifier), admin_keys=self._admin_keys)
        return summaries

    def __len__(self) -> int:
        """Count."""
        return len(self._aggregations)

    def _filter(
        self,
        associations: AggregationAssociationCode | list[AggregationAssociationCode] | None = None,
        initiatives: AggregationInitiativeCode | list[AggregationInitiativeCode] | None = None,
    ) -> list[ItemCatalogueSummary]:
        """
        Filter aggregations as item summaries, by namespace and/or association(s) and/or initiative(s).

        Wrapper around Record Aggregations.filter() returning results as ItemSummaryCatalogue instances.

        Note: Aggregations are scoped to the BAS Data Catalogue namespace so they can be returned as item summaries.
        """
        results = self._aggregations.filter(
            namespace=CATALOGUE_NAMESPACE, associations=associations, initiatives=initiatives
        )
        return [self._summaries[aggregation.identifier.identifier] for aggregation in results]

    @property
    def peer_collections(self) -> list[ItemCatalogueSummary]:
        """Collections item is related with."""
        return self._filter(
            associations=AggregationAssociationCode.CROSS_REFERENCE,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )

    @property
    def peer_projects(self) -> list[ItemCatalogueSummary]:
        """Collections item is related with."""
        return self._filter(
            associations=AggregationAssociationCode.CROSS_REFERENCE,
            initiatives=AggregationInitiativeCode.PROJECT,
        )

    @property
    def peer_cross_reference(self) -> list[ItemCatalogueSummary]:
        """
        Other items item is related with.

        Returns cross-references not in scope of other aggregation types (such as peer collections).
        """
        results = self._aggregations.filter(
            namespace=CATALOGUE_NAMESPACE, associations=AggregationAssociationCode.CROSS_REFERENCE
        )
        non_exclusive = [item.record.file_identifier for item in chain(self.peer_collections, self.peer_projects)]
        exclusive = [aggregation for aggregation in results if aggregation.identifier.identifier not in non_exclusive]
        return [self._summaries[aggregation.identifier.identifier] for aggregation in exclusive]

    @property
    def peer_supersedes(self) -> list[ItemCatalogueSummary]:
        """Items item supersedes (replaces)."""
        return self._filter(associations=AggregationAssociationCode.REVISION_OF)

    @property
    def peer_opposite_side(self) -> ItemCatalogueSummary | None:
        """Item that forms the opposite side of a published map."""
        items = self._filter(
            associations=AggregationAssociationCode.PHYSICAL_REVERSE_OF,
            initiatives=AggregationInitiativeCode.PAPER_MAP,
        )
        return items[0] if items else None

    @property
    def parent_collections(self) -> list[ItemCatalogueSummary]:
        """Collections item is contained within."""
        return self._filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )

    @property
    def parent_projects(self) -> list[ItemCatalogueSummary]:
        """Projects item is contained within."""
        return self._filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.PROJECT,
        )

    @property
    def child_items(self) -> list[ItemCatalogueSummary]:
        """Items contained within item."""
        return self._filter(
            associations=AggregationAssociationCode.IS_COMPOSED_OF,
            initiatives=[AggregationInitiativeCode.COLLECTION, AggregationInitiativeCode.PROJECT],
        )

    @property
    def parent_printed_map(self) -> ItemCatalogueSummary | None:
        """Printed map item is a side of."""
        items = self._filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.PAPER_MAP,
        )
        return items[0] if items else None

    @property
    def parent_maps(self) -> list[ItemCatalogueSummary]:
        """Map based items the item forms a layer within."""
        return self._filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=[AggregationInitiativeCode.MAP_LAYER],
        )

    @property
    def map_layers(self) -> list[ItemCatalogueSummary]:
        """Items that comprise layers within a map based item."""
        return self._filter(
            associations=AggregationAssociationCode.IS_COMPOSED_OF,
            initiatives=[AggregationInitiativeCode.MAP_LAYER],
        )


class Dates(RecordDates):
    """
    Dates.

    Wrapper around Record Dates to apply automatic formatting.

    Includes a derived relative revision date for use in catalogue item page summaries.
    """

    def __init__(self, dates: RecordDates) -> None:
        super().__init__(**unpack(dates))

    def __getattribute__(self, name: str) -> FormattedDate | None:
        """Get formatted date by name."""
        if name not in object.__getattribute__(self, "__dataclass_fields__"):
            return object.__getattribute__(self, name)

        val: Date = super().__getattribute__(name)
        if val is None:
            return None
        return FormattedDate.from_rec_date(val)

    @property
    def revision_relative(self) -> FormattedDate | None:
        """
        Revision date relative to now.

        Returns a formatted date with a time only value where the revision date is within the current day.
        """
        val = super().__getattribute__("revision")
        if val is None:
            return None

        fmt_val = FormattedDate.from_rec_date(val)
        if isinstance(val.date, DateTime) and val.date.date() == DateTime.now(tz=UTC).date():
            fmt_val.value = val.date.strftime("%H:%M:%S %Z")
        return fmt_val

    def as_dict_enum_formatted(self) -> dict[DateTypeCode, FormattedDate]:
        """
        Non-None values as a dictionary with DateTypeCode enum keys, with values formatted as FormattedDate.

        Converts from the base-class Date values to FormattedDate instances to stay type compatible.
        """
        return super().as_dict_enum()  # ty:ignore[invalid-return-type]

    def as_dict_labeled(self) -> dict[str, FormattedDate]:
        """Non-None values as a dictionary with human-readable labels as keys."""
        mapping = {
            DateTypeCode.CREATION: "Item Created",
            DateTypeCode.PUBLICATION: "Item Published",
            DateTypeCode.REVISION: "Item Updated",
            DateTypeCode.ADOPTED: "Item Adopted",
            DateTypeCode.DEPRECATED: "Item Deprecated",
            DateTypeCode.DISTRIBUTION: "Item Distributed",
            DateTypeCode.EXPIRY: "Item Expiry",
            DateTypeCode.IN_FORCE: "Item In Force From",
            DateTypeCode.LAST_REVISION: "Item Last Revised",
            DateTypeCode.LAST_UPDATE: "Item Last Updated",
            DateTypeCode.NEXT_UPDATE: "Item Next Update",
            DateTypeCode.RELEASED: "Item Released",
            DateTypeCode.SUPERSEDED: "Item Superseded",
            DateTypeCode.UNAVAILABLE: "Item Unavailable From",
            DateTypeCode.VALIDITY_BEGINS: "Item Valid From",
            DateTypeCode.VALIDITY_EXPIRES: "Item Valid Until",
        }
        return {mapping[key]: value for key, value in self.as_dict_enum_formatted().items()}


class Extent(ItemExtent):
    """
    ItemCatalogue Extent.

    Wrapper around ItemBase Extent adding date formatting and extent map properties.
    """

    def __init__(self, extent: ItemExtent, embedded_maps_endpoint: str) -> None:
        super().__init__(extent)
        self._map_endpoint = embedded_maps_endpoint

    @property
    def start(self) -> FormattedDate | None:
        """Temporal period start."""
        return (FormattedDate.from_rec_date(start) if start else None) if (start := super().start) is not None else None

    @property
    def end(self) -> FormattedDate | None:
        """Temporal period end."""
        return (FormattedDate.from_rec_date(end) if end else None) if (end := super().end) is not None else None

    @property
    def map_iframe(self) -> str:
        """Visualise bounding box as an embedded map using the BAS Embedded Maps Service."""
        bbox = json.dumps(list(self.bounding_box)).replace(" ", "")
        params = f"theme=bsk2&bbox={bbox}&globe-overview"
        return f"{self._map_endpoint}/?{params}"


class Identifiers(RecordIdentifiers):
    """
    Identifiers.

    Container for Record Identifiers formatted as links and grouped by type.
    """

    def __init__(self, identifiers: RecordIdentifiers) -> None:
        super().__init__(identifiers)

    @property
    def doi(self) -> list[Link]:
        """DOIs for Item."""
        return [
            Link(value=identifier.identifier, href=identifier.href, external=True) for identifier in self.filter("doi")
        ]

    @property
    def isbn(self) -> list[str]:
        """ISBNs for Item."""
        return [identifier.identifier for identifier in self.filter("isbn")]

    @property
    def aliases(self) -> list[Link]:
        """
        Aliases for Item.

        Aliases consists of a `{prefix}/{value}` identifier and `https://{alias_namespace}/{identifier}` as a href.
        E.g. `https://alias.lantern.data.bas.ac.uk/product/foo`.

        Note: The alias_namespace used is a constant independent of the site environment (live, testing, dev).

        Links are made non-fully qualified for use in any environment.
        """
        identifiers = list(self.filter(ALIAS_NAMESPACE))
        aliases = []
        for identifier in identifiers:
            if not identifier.href:
                msg = "Aliases must have a href."
                raise ValueError(msg) from None
            href = identifier.href.replace(f"https://{CATALOGUE_NAMESPACE}", "")
            aliases.append(Link(value=identifier.identifier, href=href, external=False))
        return aliases


class Maintenance(RecordMaintenance):
    """
    ItemCatalogue Maintenance.

    Wrapper around Record Maintenance to use more human-readable labels.
    """

    def __init__(self, maintenance: RecordMaintenance) -> None:
        super().__init__(**unpack(maintenance))

    @property
    def status(self) -> str | None:
        """Non-None progress as a human-readable status label."""
        if self.progress is None:
            return None

        mapping = {
            ProgressCode.COMPLETED: "Item is complete and recommended for general use",
            ProgressCode.HISTORICAL_ARCHIVE: "Item has been archived and may be outdated",
            ProgressCode.OBSOLETE: "Item is obsolete and should be used with caution",
            ProgressCode.SUPERSEDED: "Item has been replaced with a newer edition",
            ProgressCode.ON_GOING: "Item is being regularly updated and recommended for general use",
            ProgressCode.PLANNED: "Item is planned and does not yet exist",
            ProgressCode.REQUIRED: "Required (Contact us for further information)",
            ProgressCode.UNDER_DEVELOPMENT: "Item is a draft and should not yet be used",
        }
        return mapping[self.progress]

    @property
    def frequency(self) -> str | None:
        """
        Non-None maintenance frequency as a human-readable frequency label.

        Values should complete 'Item is updated ...'.
        """
        if self.maintenance_frequency is None:
            return None

        mapping = {
            MaintenanceFrequencyCode.CONTINUAL: "Item is updated more than once a day",
            MaintenanceFrequencyCode.DAILY: "Item is updated every day",
            MaintenanceFrequencyCode.WEEKLY: "Item is updated every week",
            MaintenanceFrequencyCode.FORTNIGHTLY: "Item is updated every fortnight",
            MaintenanceFrequencyCode.MONTHLY: "Item is updated every month",
            MaintenanceFrequencyCode.QUARTERLY: "Item is updated every four months",
            MaintenanceFrequencyCode.BIANNUALLY: "Item is updated twice a year",
            MaintenanceFrequencyCode.ANNUALLY: "Item is updated every year",
            MaintenanceFrequencyCode.AS_NEEDED: "Item may be updated if needed",
            MaintenanceFrequencyCode.IRREGULAR: "Item is updated irregularly",
            MaintenanceFrequencyCode.NOT_PLANNED: "No updates are planned for this item",
            MaintenanceFrequencyCode.UNKNOWN: "Unknown",
        }
        return mapping[self.maintenance_frequency]


class PageHeader:
    """Item Page header information."""

    def __init__(self, title: str, item_type: HierarchyLevelCode) -> None:
        self._title = title
        self._item_type = item_type

    @property
    def title(self) -> str:
        """Title."""
        return self._title.replace("<p>", "").replace("</p>", "")

    @property
    def subtitle(self) -> tuple[str, str]:
        """Subtitle."""
        return ResourceTypeLabel[self._item_type.name].value, ResourceTypeIcon[self._item_type.name].value


class PageSummary:
    """Item summary information."""

    def __init__(
        self,
        item_super_type: ItemSuperType,
        edition: str | None,
        published_date: FormattedDate | None,
        revision_date: FormattedDate | None,
        aggregations: Aggregations,
        live: bool,
        restricted: bool,
        citation: str | None,
        description: str,
    ) -> None:
        self._item_super_type = item_super_type
        self._edition = edition
        self._published_date = published_date
        self._revision_date = revision_date
        self._aggregations = aggregations
        self._live = live
        self._restricted = restricted
        self._citation = citation
        self._description = description

    @property
    def grid_enabled(self) -> bool:
        """
        Whether to show summary grid section in UI.

        Contains all item summary properties except about (abstract) and citation.

        Shown if item has any summary grid properties (e.g. restricted, edition, one or more collections, etc.).
        """
        return (
            self.restricted
            or self.live
            or self.edition is not None
            or self.published is not None
            or len(self.collections) > 0
            or len(self.projects) > 0
        )

    @property
    def edition(self) -> str | None:
        """Edition."""
        return self._edition

    @property
    def published(self) -> FormattedDate | None:
        """
        Formatted published date.

        With revision date if set and different to publication.
        """
        if self._published_date is None:
            return None
        if self._published_date != self._revision_date and self._revision_date is not None:
            return FormattedDate(
                value=f"{self._published_date.value} (last updated: {self._revision_date.value})",
                datetime=self._published_date.datetime,
            )
        return self._published_date

    @property
    def collections(self) -> list[Link]:
        """Collections item is part of."""
        return [Link(value=related.title_fmt, href=related.href) for related in self._aggregations.parent_collections]

    @property
    def projects(self) -> list[Link]:
        """Projects item is part of."""
        return [Link(value=related.title_fmt, href=related.href) for related in self._aggregations.parent_projects]

    @property
    def physical_parent(self) -> Link | None:
        """Item that represents the physical map an item is one side of."""
        related = self._aggregations.parent_printed_map
        return Link(value=related.title_fmt, href=related.href) if related else None

    @property
    def live(self) -> bool:
        """Live updating."""
        return self._live

    @property
    def restricted(self) -> bool:
        """Access restricted."""
        return self._restricted

    @property
    def citation(self) -> str | None:
        """
        Citation.

        Not shown for container type items (e.g. collections).
        """
        if self._item_super_type == ItemSuperType.CONTAINER:
            return None
        return self._citation

    @property
    def about(self) -> str:
        """Abstract/description."""
        return self._description
