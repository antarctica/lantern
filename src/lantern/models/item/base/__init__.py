import json
from json import JSONDecodeError
from urllib.parse import unquote

from lantern.models.item.base.const import PERMISSIONS_BAS_GROUP, PERMISSIONS_NERC_DIRECTORY
from lantern.models.item.base.elements import Contact, Contacts, Extent, Extents
from lantern.models.item.base.enums import AccessType
from lantern.models.item.base.utils import md_as_html, md_as_plain
from lantern.models.record import Distribution, HierarchyLevelCode, Record
from lantern.models.record.elements.common import Date, Identifier, Identifiers, Series
from lantern.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    Constraint,
    Constraints,
    GraphicOverviews,
)
from lantern.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.models.record.summary import RecordSummary


class ItemBase:
    """
    Base representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Items are a high-level, read-only, and non-standards specific view of a resource via an underlying Record instance,
    to make it easier and less cumbersome to use through various filtering, processing and formatting methods.

    Note that Items must include a file_identifier.

    Multiple Item classes are used for different contexts and systems. This base representation contains core/common
    properties and methods shared between all Item classes. It is not expected to be used directly.

    It is expected, and acceptable, to use the underlying `_record` property to access information not made directly
    available by this class. Especially for properties this class would simply pass through to the record.
    """

    def __init__(self, record: Record) -> None:
        self._record = record

        if self.resource_id is None:
            msg = "Items require a file_identifier."
            raise ValueError(msg)

    @staticmethod
    def _parse_permissions(href: str | None) -> list[AccessType]:
        """
        Decode permissions encoded in an access constraint.

        Decodes and maps supported payloads to members of the AccessType enum.

        The ISO 19115 information model does not provide for detailed access permissions to be defined. As a workaround
        a local convention is used to encode permissions via a URL fragment containing URL encoded serialised JSON data.

        These permissions are only understood (and only intended to be understood) by systems and tools within the BAS
        Data Catalogue / Metadata ecosystem. They are not considered sensitive information.

        If configured, the JSON data defines a payload defined, and specific to, a scheme name and version. Payloads are
        not intended to be portable between these schemes. Resources may contain multiple payloads, either to encode
        multiple permissions within a given scheme (e.g. using logical OR) or to encode permissions in multiple schemes.

        This method only returns of a list of supported/parsable permissions. Other methods will use this list to
        determine which permissions are applicable in a given context.
        """
        permissions = []

        if href is None:
            return permissions

        href_decoded = unquote(href.replace("#", ""))
        try:
            data = json.loads(href_decoded)
        except JSONDecodeError:
            return permissions

        for item in data:
            if (
                "scheme" not in item
                or item["scheme"] != "ms_graph"
                or "schemeVersion" not in item
                or item["schemeVersion"] != "1"
            ):
                continue
            if item["directoryId"] == PERMISSIONS_NERC_DIRECTORY and item["objectId"] == PERMISSIONS_BAS_GROUP:
                permissions.append(AccessType.BAS_ALL)

        return permissions

    @staticmethod
    def _parse_access(constraints: Constraints) -> AccessType:
        """
        Determine item access based on access constraints.

        Defaults to no access if no access constraints are set.
        Sets public access if a single unrestricted access constraint is set.
        Sets intentionally ambiguous 'BAS_SOME' access if a single restricted constraint is set without permissions.
        May set other options based on any permissions set in constraints.
        """
        if len(constraints) == 0:
            return AccessType.NONE

        if len(constraints) == 1 and constraints[0].restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
            return AccessType.PUBLIC

        if (
            len(constraints) == 1
            and constraints[0].restriction_code == ConstraintRestrictionCode.RESTRICTED
            and constraints[0].href is None
        ):
            return AccessType.BAS_SOME

        permissions = [perm for constraint in constraints for perm in ItemBase._parse_permissions(constraint.href)]
        if AccessType.BAS_ALL in permissions:
            return AccessType.BAS_ALL

        # fail-safe
        return AccessType.NONE

    @property
    def abstract_raw(self) -> str:
        """Raw Abstract."""
        return self._record.identification.abstract

    @property
    def abstract_md(self) -> str:
        """Abstract with Markdown formatting if present."""
        return self.abstract_raw

    @property
    def abstract_html(self) -> str:
        """Abstract with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.abstract_md)

    @property
    def access_type(self) -> AccessType:
        """Resource access."""
        return self._parse_access(self.constraints.filter(types=ConstraintTypeCode.ACCESS))

    @property
    def aggregations(self) -> Aggregations:
        """Aggregations."""
        return self._record.identification.aggregations

    @property
    def bounding_extent(self) -> Extent | None:
        """Bounding extent."""
        try:
            return self.extents.filter(identifier="bounding")[0]
        except IndexError:
            return None

    @property
    def citation_raw(self) -> str | None:
        """Optional raw citation."""
        _citation = self._record.identification.other_citation_details
        return None if _citation is None else _citation

    @property
    def citation_md(self) -> str | None:
        """Optional citation with Markdown formatting if present."""
        return self.citation_raw

    @property
    def citation_html(self) -> str | None:
        """Optional citation with Markdown formatting, if present, encoded as HTML."""
        _citation = self.citation_md
        return None if _citation is None else md_as_html(_citation)

    @property
    def collections(self) -> list[Aggregation]:
        """
        Collections.

        Limited to collections the item states it is part of (child -> parent), which is non-typical.
        """
        return self.aggregations.filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )

    @property
    def contacts(self) -> Contacts:
        """
        Contacts.

        Casts copies of Record Contact items as Item Contact items, to leverage Item specific functionality.
        Cast items are contained in a Record Contacts container subclass, to reflect correct types.
        """
        return Contacts([Contact(contact) for contact in self._record.identification.contacts])

    @property
    def constraints(self) -> Constraints:
        """Constraints."""
        return self._record.identification.constraints

    @property
    def distributions(self) -> list[Distribution]:
        """Distributions."""
        return self._record.distribution

    @property
    def edition(self) -> str | None:
        """Edition."""
        return self._record.identification.edition

    @property
    def extents(self) -> Extents:
        """
        Extents.

        Casts copies of Record Extent items as Item Extent items, to leverage Item specific functionality.
        Cast items are contained in a Record Extents container subclass, to reflect correct types.
        """
        return Extents([Extent(extent) for extent in self._record.identification.extents])

    @property
    def graphics(self) -> GraphicOverviews:
        """Graphic overviews."""
        return self._record.identification.graphic_overviews

    @property
    def identifiers(self) -> Identifiers:
        """Identifiers."""
        return self._record.identification.identifiers

    @property
    def kv(self) -> dict:
        """
        Optional supplemental information as key values.

        ISO records cannot easily hold information that doesn't fit within the ISO information model (arguably rightly).
        To avoid (mis)using keywords or adding complex metadata extensions, we use the freetext supplemental
        information element to hold a set of key-value pairs encoded as a JSON string.

        In Items, we pre-decode any values if possible. If the value cannot be decoded as JSON (perhaps because it's an
        external record that uses this element another way), an empty dict is returned.

        Known (but optional) keys:
        - width: width of resource when printed in mm
        - height: height of resource when printed in mm

        This is not intended to be portable/interoperable across other systems, and is used only within the BAS
        metadata ecosystem of tools but is human-readable to an extent so could be shown elsewhere.
        """
        try:
            return json.loads(self._record.identification.supplemental_information)
        except TypeError:
            return {}
        except JSONDecodeError:
            return {}

    @property
    def licence(self) -> Constraint | None:
        """Licence constraint."""
        licences = self.constraints.filter(
            types=ConstraintTypeCode.USAGE, restrictions=ConstraintRestrictionCode.LICENSE
        )
        try:
            return licences[0]
        except IndexError:
            return None

    @property
    def lineage_raw(self) -> str | None:
        """Optional raw lineage statement."""
        if self._record.data_quality is None or self._record.data_quality.lineage is None:
            return None
        return self._record.data_quality.lineage.statement

    @property
    def lineage_md(self) -> str | None:
        """Optional lineage statement with Markdown formatting if present."""
        return self.lineage_raw

    @property
    def lineage_html(self) -> str | None:
        """Optional lineage statement with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.lineage_md) if self.lineage_md is not None else None

    @property
    def projection(self) -> Identifier | None:
        """
        Optional projection identifier.

        Limited to EPSG projections so we can predictably handle them.
        """
        ref = self._record.reference_system_info
        if ref is None or "urn:ogc:def:crs:EPSG" not in ref.code.value:
            return None
        code = ref.code.value.replace("urn:ogc:def:crs:EPSG::", "EPSG:")
        return Identifier(identifier=code, href=ref.code.href, namespace="epsg")

    @property
    def resource_id(self) -> str:
        """
        Resource identifier.

        AKA resource/record/item/file identifier.
        """
        return self._record.file_identifier

    @property
    def resource_type(self) -> HierarchyLevelCode:
        """
        Resource type.

        AKA hierarchy-level/scope-code.
        """
        return self._record.hierarchy_level

    @property
    def series_descriptive(self) -> Series:
        """
        Optional descriptive series.

        Typically used for published maps.

        Due to a bug in V4 BAS ISO JSON Schema the 'page' (sheet number) property cannot be set. As a workaround, this
        class supports loading an optional 'sheet_number' from KV properties.
        """
        series = self._record.identification.series
        sheet_number = self.kv.get("sheet_number", None)
        if sheet_number is not None:
            series.page = sheet_number
        return series

    @property
    def summary_raw(self) -> str | None:
        """Optional raw Summary (purpose)."""
        return self._record.identification.purpose

    @property
    def summary_md(self) -> str | None:
        """Optional summary (purpose) with Markdown formatting if present."""
        return self.summary_raw

    @property
    def summary_html(self) -> str | None:
        """Optional summary (purpose) with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.summary_md) if self.summary_md is not None else None

    @property
    def summary_plain(self) -> str | None:
        """Optional summary (purpose) without Markdown formatting."""
        return None if self.summary_md is None else md_as_plain(self.summary_md)

    @property
    def title_raw(self) -> str:
        """Raw Title."""
        return self._record.identification.title

    @property
    def title_md(self) -> str:
        """Title with Markdown formatting."""
        return self.title_raw

    @property
    def title_html(self) -> str | None:
        """Title with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.title_md)

    @property
    def title_plain(self) -> str:
        """Title without Markdown formatting."""
        return md_as_plain(self.title_md)


class ItemSummaryBase:
    """
    Base summary of a resource within the BAS Data Catalogue / Metadata ecosystem.

    ItemSummaries are a high-level, read-only, and non-standards specific view of a resource via an underlying
    RecordSummary instance, as a counterpart to Item classes.

    Note that ItemSummaries must include a file_identifier.

    Multiple ItemSummaries classes may be used for different contexts and systems. This base representation contains
    core/common properties and methods shared between all summary classes. It is not expected to be used directly.
    """

    def __init__(self, record_summary: RecordSummary) -> None:
        self._record_summary = record_summary

        if self.resource_id is None:
            msg = "Item Summaries require a file_identifier."
            raise ValueError(msg)

    @property
    def access(self) -> AccessType:
        """Resource access."""
        # noinspection PyProtectedMember
        return ItemBase._parse_access(self._record_summary.constraints.filter(types=ConstraintTypeCode.ACCESS))

    @property
    def date(self) -> Date | None:
        """Item publication date if available."""
        return self._record_summary.publication

    @property
    def edition(self) -> str | None:
        """Edition."""
        return self._record_summary.edition

    @property
    def href(self) -> str:
        """Item catalogue URL."""
        return f"/items/{self.resource_id}/"

    @property
    def href_graphic(self) -> str | None:
        """Graphic URL."""
        for graphic in self._record_summary.graphic_overviews:
            if graphic.identifier == "overview":
                return graphic.href
        return None

    @property
    def resource_id(self) -> str:
        """
        Resource identifier.

        AKA resource/record/item/file identifier.
        """
        return self._record_summary.file_identifier

    @property
    def resource_type(self) -> HierarchyLevelCode:
        """
        Resource type.

        AKA hierarchy-level/scope-code.
        """
        return self._record_summary.hierarchy_level

    @property
    def summary_raw(self) -> str | None:
        """Raw Summary, if present."""
        return self._record_summary.purpose

    @property
    def summary_md(self) -> str | None:
        """Summary with Markdown formatting, if present."""
        return self.summary_raw

    @property
    def summary_html(self) -> str | None:
        """Summary with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.summary_md) if self.summary_md is not None else None

    @property
    def summary_plain(self) -> str | None:
        """Summary without Markdown formatting, if present."""
        return md_as_plain(self.summary_md) if self.summary_md is not None else None

    @property
    def title_raw(self) -> str:
        """Raw Title."""
        return self._record_summary.title

    @property
    def title_md(self) -> str:
        """Title with Markdown formatting."""
        return self.title_raw

    @property
    def title_plain(self) -> str:
        """Title without Markdown formatting."""
        return md_as_plain(self.title_md)
