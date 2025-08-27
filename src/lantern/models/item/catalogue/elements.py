import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TypeVar

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.common import Dates as RecordDates
from lantern.lib.metadata_library.models.record.elements.common import Identifiers as RecordIdentifiers
from lantern.lib.metadata_library.models.record.elements.identification import Aggregations as RecordAggregations
from lantern.lib.metadata_library.models.record.elements.identification import Maintenance as RecordMaintenance
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    DateTypeCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.models.item.base import ItemBase
from lantern.models.item.base.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE, GITLAB_NAMESPACE
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.elements import Link, unpack
from lantern.models.item.base.enums import AccessLevel, ResourceTypeLabel
from lantern.models.item.base.utils import md_as_html
from lantern.models.item.catalogue.enums import ResourceTypeIcon
from lantern.models.record.revision import RecordRevision

TFormattedDate = TypeVar("TFormattedDate", bound="FormattedDate")


@dataclass(kw_only=True)
class FormattedDate:
    """Represents a HTML time element."""

    value: str
    datetime: str

    @classmethod
    def from_rec_date(cls: type[TFormattedDate], value: Date, relative_to: datetime | None = None) -> "FormattedDate":
        """
        Format a Record date for use in HTML time elements.

        Time elements consist of human-readable value and a machine-readable 'datetime' attribute.

        For time values:
        - uses a 'DD MMM YYYY' (e.g. 01 Oct 2023) representation where precision allows
        - Date times within 24 hours of a reference point (defaults to now) returns the date and time (otherwise omitted)

        For time 'datetime' attributes:
        - uses the relevant ISO 8601 representation (e.g. 2023-10-01T12:00:00+00:00)
        """
        if not isinstance(value, Date):
            msg = "Value must be a record Date object."
            raise TypeError(msg) from None

        dt = value.date.strftime("%Y-%m-%d")
        val = value.date.strftime("%d %B %Y")
        relative_to = relative_to or datetime.now(tz=UTC)

        if isinstance(value.date, datetime) and not relative_to - value.date > timedelta(hours=24):
            val = value.date.strftime("%d %B %Y %H:%M:%S %Z")
            dt = value.date.isoformat()
        if isinstance(value.date, date) and value.precision is DatePrecisionCode.YEAR:
            val = value.date.strftime("%Y")
            dt = str(value.date.year)
        if isinstance(value.date, date) and value.precision is DatePrecisionCode.MONTH:
            val = value.date.strftime("%B %Y")
            dt = value.date.strftime("%Y-%m")

        return cls(value=val, datetime=dt)


@dataclass(kw_only=True)
class ItemSummaryFragments:
    """Properties shown as part of an ItemSummaryCatalogue."""

    access: AccessLevel
    item_type: str
    item_type_icon: str
    edition: str | None
    published: FormattedDate | None
    children: str | None


class ItemCatalogueSummary(ItemBase):
    """
    Summary of a resource within the BAS Data Catalogue.

    Catalogue item summaries provide additional context for base summaries for use when presenting search results or
    resources related to the current item within the BAS Data Catalogue website.
    """

    @property
    def _resource_type_label(self) -> str:
        """Resource type label."""
        return ResourceTypeLabel[self.resource_type.name].value

    @property
    def _resource_type_icon(self) -> str:
        """Resource type icon."""
        return ResourceTypeIcon[self.resource_type.name].value

    @property
    def _date(self) -> FormattedDate | None:
        """Formatted date."""
        publication = self._record.identification.dates.publication
        return FormattedDate.from_rec_date(publication) if publication else None

    @property
    def _edition(self) -> str | None:
        """Formatted edition."""
        if self.edition is None or self.resource_type == HierarchyLevelCode.COLLECTION:
            return None
        if (
            self.resource_type == HierarchyLevelCode.PRODUCT
            or self.resource_type == HierarchyLevelCode.PAPER_MAP_PRODUCT
        ):
            return f"Ed. {self.edition}"
        return f"v{self.edition}"

    @property
    def _children(self) -> str | None:
        """
        Count of items contained within item.

        E.g. For collections, the number of items it contains.
        """
        count = len(
            self._record.identification.aggregations.filter(associations=AggregationAssociationCode.IS_COMPOSED_OF)
        )
        if count == 1:
            return "1 item"
        if count > 1:
            return f"{count} items"
        return None

    @property
    def summary_html(self) -> str:
        """Summary with Markdown formatting encoded as HTML if present or a blank string."""
        return md_as_html(self.summary_md) if self.summary_md else md_as_html(" ")

    @property
    def fragments(self) -> ItemSummaryFragments:
        """UI fragments (icons and labels) for item summary."""
        published = self._date if self.resource_type != HierarchyLevelCode.COLLECTION else None
        return ItemSummaryFragments(
            access=self.access_level,
            item_type=self._resource_type_label,
            item_type_icon=self._resource_type_icon,
            edition=self._edition,
            published=published,
            children=self._children,
        )

    @property
    def href_graphic(self) -> str:
        """Item graphic, or generic default (BAS roundel)."""
        default = (
            "data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAAC+lBMVEUAAADu7u739/fz8/Pt7e3w"
            "8PDv7+/t7e3u7u7u7u7t7e3v7+/u7u7u7u7v7+/x8fH////9/f3s7Ozu7u7s7Ozv7+/u7u7v7+/u7u7u7u7u7u7u7u7u7u7v7+/"
            "////u7u709PTu7u76+vrv7+/x8fHt7e3v7+/u7u7u7u6AgIDs7Ozv7+/u7u7v7+/u7u7u7u7u7u7u7u7u7u7////u7u7u7u7u7u"
            "7p6enr6+vv7+/s7Ozu7u7v7+/u7u7////u7u7t7e3u7u7y8vLs7Oz19fXs7Ozw8PDu7u74+Pjv7+/8/Pzu7u7t7e3u7u7////v7"
            "+/w8PDu7u7q6uru7u7v7+/v7+/v7+/v7+/v7+/u7u7v7+/u7u7u7u7t7e3u7u7+/v7v7+/z8/Pu7u7u7u7y8vLu7u7u7u7u7u7u"
            "7u7u7u7////09PTw8PD29vb5+fnr6+vt7e3u7u7t7e3u7u7u7u7////t7e3u7u7v7+/t7e37+/vu7u7u7u7u7u7////u7u7w8PD"
            "v7+/x8fHu7u7v7+/////u7u7v7+/s7Ozu7u7u7u7u7u7v7+/u7u7x8fHu7u7u7u7y8vLu7u7t7e3u7u7v7+/u7u7v7+/t7e3x8f"
            "Hu7u7u7u7t7e3q6urv7+/u7u7u7u7u7u7u7u7u7u7v7+/u7u7v7+/t7e3v7+/w8PDs7Ozu7u7u7u719fXu7u7x8fHu7u7u7u7u7"
            "u7v7+/u7u7v7+/t7e3u7u7s7Ozu7u7u7u7v7+/u7u7v7+/s7Ozt7e3////v7+/v7+/u7u7u7u7////u7u7v7+/u7u7u7u7u7u7u"
            "7u7t7e3t7e3t7e3v7+/v7+/v7+/v7+/u7u7u7u7u7u7u7u7u7u7t7e3t7e3v7+/w8PDt7e3b29vr6+vz8/Pt7e3o6Oi/v7/w8PD"
            "u7u7y8vLw8PDt7e3V1dXf39/u7u7t7e3t7e3t7e3t7e3q6urt7e3t7e3h4eHt7e3s7Oyqqqru7u7n5+fr6+vt7e3u7u7t7e3u7u"
            "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"
        )
        return self.overview_graphic.href if self.overview_graphic else default


class Aggregations:
    """
    Aggregations.

    Container for ItemBase Aggregations formatted as links and grouped by type.
    """

    def __init__(self, aggregations: RecordAggregations, get_record: Callable[[str], RecordRevision]) -> None:
        self._aggregations = aggregations
        self._summaries = self._generate_summaries(get_record)

    def _generate_summaries(self, get_record: Callable[[str], RecordRevision]) -> dict[str, ItemCatalogueSummary]:
        """Generate item summaries for aggregations indexed by resource identifier."""
        summaries = {}
        for aggregation in self._aggregations:
            identifier = aggregation.identifier.identifier
            summaries[identifier] = ItemCatalogueSummary(get_record(identifier))
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
    def peer_cross_reference(self) -> list[ItemCatalogueSummary]:
        """
        Other items item is related with.

        Returns cross-references not in scope of other aggregation types (such as peer collections).
        """
        results = self._aggregations.filter(
            namespace=CATALOGUE_NAMESPACE, associations=AggregationAssociationCode.CROSS_REFERENCE
        )
        non_exclusive = [item.resource_id for item in self.peer_collections]
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
    def child_items(self) -> list[ItemCatalogueSummary]:
        """Items contained within item."""
        return self._filter(
            associations=AggregationAssociationCode.IS_COMPOSED_OF,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )

    @property
    def parent_printed_map(self) -> ItemCatalogueSummary | None:
        """Printed map item is a side of."""
        items = self._filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.PAPER_MAP,
        )
        return items[0] if items else None


class Dates(RecordDates):
    """
    Dates.

    Wrapper around Record Dates to apply automatic formatting.
    """

    def __init__(self, dates: RecordDates) -> None:
        # noinspection PyTypeChecker
        super().__init__(**unpack(dates))

    def __getattribute__(self, name: str) -> FormattedDate | None:
        """Get formatted date by name."""
        if name not in object.__getattribute__(self, "__dataclass_fields__"):
            return object.__getattribute__(self, name)

        val: Date = super().__getattribute__(name)
        if val is None:
            return None
        return FormattedDate.from_rec_date(val)

    def as_dict_enum(self) -> dict[DateTypeCode, FormattedDate]:
        """Non-None values as a dictionary with DateTypeCode enum keys."""
        # noinspection PyTypeChecker
        return super().as_dict_enum()

    def as_dict_labeled(self) -> dict[str, FormattedDate]:
        """Non-None values as a dictionary with human-readable labels as keys."""
        mapping = {
            DateTypeCode.CREATION: "Item created",
            DateTypeCode.PUBLICATION: "Item published",
            DateTypeCode.REVISION: "Item updated",
            DateTypeCode.ADOPTED: "Item adopted",
            DateTypeCode.DEPRECATED: "Item deprecated",
            DateTypeCode.DISTRIBUTION: "Item distributed",
            DateTypeCode.EXPIRY: "Item expiry",
            DateTypeCode.IN_FORCE: "Item in force from",
            DateTypeCode.LAST_REVISION: "Item last revised",
            DateTypeCode.LAST_UPDATE: "Item last updated",
            DateTypeCode.NEXT_UPDATE: "Item next update",
            DateTypeCode.RELEASED: "Item released",
            DateTypeCode.SUPERSEDED: "Item superseded",
            DateTypeCode.UNAVAILABLE: "Item unavailable from",
            DateTypeCode.VALIDITY_BEGINS: "Item valid from",
            DateTypeCode.VALIDITY_EXPIRES: "Item valid until",
        }
        return {mapping[key]: value for key, value in self.as_dict_enum().items()}


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
        return FormattedDate.from_rec_date(super().start) if super().start else None

    @property
    def end(self) -> FormattedDate | None:
        """Temporal period end."""
        return FormattedDate.from_rec_date(super().end) if super().end else None

    @property
    def map_iframe(self) -> str:
        """Visualise bounding box as an embedded map using the BAS Embedded Maps Service."""
        bbox = json.dumps(list(self.bounding_box)).replace(" ", "")
        params = f"bbox={bbox}&globe-overview"
        return f"{self._map_endpoint}/?{params}"


class Identifiers(RecordIdentifiers):
    """
    Identifiers.

    Container for Record Identifiers formatted as links and grouped by type.
    """

    def __init__(self, identifiers: RecordIdentifiers) -> None:
        # noinspection PyTypeChecker
        super().__init__(identifiers)

    @staticmethod
    def _make_gitlab_issue_ref(href: str) -> str:
        """
        Create GitLab issue reference.

        E.g. https://gitlab.data.bas.ac.uk/MAGIC/foo/-/issues/123 -> MAGIC/foo#123                                                                                                                                                                              .
        """
        return f"{href.split('/')[-5]}/{href.split('/')[-4]}#{href.split('/')[-1]}"

    @property
    def doi(self) -> list[Link]:
        """DOIs for Item."""
        return [
            Link(value=identifier.identifier, href=identifier.href, external=True) for identifier in self.filter("doi")
        ]

    @property
    def isbn(self) -> list[str]:
        """ISBNs for Item."""
        # noinspection PyTypeChecker
        return [identifier.identifier for identifier in self.filter("isbn")]

    @property
    def gitlab_issues(self) -> list[str]:
        """
        GitLab issues for Item.

        Returned as references rather than links to discourage others viewing issues.
        """
        return [self._make_gitlab_issue_ref(identifier.href) for identifier in self.filter(GITLAB_NAMESPACE)]

    @property
    def aliases(self) -> list[Link]:
        """
        Aliases for Item.

        Alias URLs are converted to relative links so they can be tested in non-production environments.
        """
        return [
            Link(href=identifier.href.replace(f"https://{CATALOGUE_NAMESPACE}", ""), value=identifier.identifier)
            for identifier in self.filter(ALIAS_NAMESPACE)
        ]


class Maintenance(RecordMaintenance):
    """
    ItemCatalogue Maintenance.

    Wrapper around Record Maintenance to use more human-readable labels.
    """

    def __init__(self, maintenance: RecordMaintenance) -> None:
        # noinspection PyTypeChecker
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
        item_type: HierarchyLevelCode,
        edition: str | None,
        published_date: FormattedDate | None,
        revision_date: FormattedDate | None,
        aggregations: Aggregations,
        access_level: AccessLevel,
        citation: str | None,
        abstract: str,
    ) -> None:
        self._item_type = item_type
        self._edition = edition
        self._published_date = published_date
        self._revision_date = revision_date
        self._aggregations = aggregations
        self._access_type = access_level
        self._citation = citation
        self._abstract = abstract

    @property
    def grid_enabled(self) -> bool:
        """
        Whether to show summary grid section in UI.

        Contains all properties except abstract and citation.
        """
        if self.access != AccessLevel.PUBLIC:
            return True
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return False
        return (
            self.edition is not None or self.published is not None or len(self.collections) > 0 or self.items_count > 0
        )

    @property
    def edition(self) -> str | None:
        """Edition."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return None
        return self._edition

    @property
    def published(self) -> FormattedDate | None:
        """Formatted published date with revision date if set and different to publication."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return None
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
        return [Link(value=summary.title_html, href=summary.href) for summary in self._aggregations.parent_collections]

    @property
    def physical_parent(self) -> Link | None:
        """Item that represents the physical map an item is one side of."""
        item = self._aggregations.parent_printed_map
        return Link(value=item.title_html, href=item.href) if item else None

    @property
    def items_count(self) -> int:
        """Number of items that form item."""
        return len(self._aggregations.child_items)

    @property
    def access(self) -> AccessLevel:
        """Access restrictions."""
        return self._access_type

    @property
    def citation(self) -> str | None:
        """Citation."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return None
        return self._citation

    @property
    def abstract(self) -> str:
        """Abstract."""
        return self._abstract
