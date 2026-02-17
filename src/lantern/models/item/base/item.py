from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission

from lantern.lib.metadata_library.models.record.elements.common import (
    Constraint,
    Constraints,
    Identifier,
    Identifiers,
    Series,
)
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregations,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys as AdminMetadataKeys
from lantern.lib.metadata_library.models.record.utils.admin import get_admin
from lantern.lib.metadata_library.models.record.utils.kv import get_kv
from lantern.models.item.base.elements import Contact, Contacts, Extent, Extents
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.base.utils import md_as_html, md_as_plain
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision


class ItemBase:
    """
    Base representation of a resource within the BAS Data Catalogue.

    Items are a high-level, read-only, and non-standards specific view of a resource via an underlying catalogue Record,
    to make it easier and less cumbersome to use through various filtering, processing and formatting methods.

    Items provide access to administrative metadata if defined and encryption and signing keys are set via the
    `admin_keys` argument.

    Item subclasses are used for different contexts and systems. This base class contains core/common properties and
    methods and is not expected to be used directly. Base items are compatible with catalogue Records or RecordRevisions,
    depending on available context. Subclasses MAY require RecordRevisions and/or impose other requirements.

    It is expected, and acceptable, to access information from the underlying record via the `record` property,
    especially for properties this class would simply pass through from the record.

    Properties for administrative metadata elements can be accessed from the `admin_metadata` property, which is cached
    on first access unless the underlying record changes. As admin metadata is optional, all `admin_` properties are
    return `None` or a suitable equivalent where admin metadata is not included, or keys are not provided to access it.
    """

    def __init__(self, record: Record | RecordRevision, admin_keys: AdminMetadataKeys | None = None) -> None:
        self._record = record
        self._admin_keys = admin_keys
        self._admin_metadata: AdministrationMetadata | None = None

    @staticmethod
    def _compute_access_level(permissions: list[Permission]) -> AccessLevel:
        if len(permissions) == 0:
            return AccessLevel.NONE
        if permissions == [BAS_STAFF]:
            return AccessLevel.BAS_STAFF
        if permissions == [OPEN_ACCESS]:
            return AccessLevel.PUBLIC
        return AccessLevel.UNKNOWN

    @property
    def record(self) -> Record | RecordRevision:
        """Get underlying Record(Revision)."""
        return self._record

    @record.setter
    def record(self, value: Record | RecordRevision) -> None:
        """
        Update underlying Record(Revision).

        Clears cached admin metadata to ensure it reflects the new record.
        """
        self._record = value
        self._admin_metadata = None

    @property
    def admin_metadata(self) -> AdministrationMetadata | None:
        """
        Optional administrative metadata.

        If present, value is decrypted and verified on first access.
        """
        if self._admin_keys is None:
            return None
        if self._admin_metadata is None:
            self._admin_metadata = get_admin(keys=self._admin_keys, record=self.record)
        return self._admin_metadata

    @property
    def admin_metadata_access(self) -> AccessLevel:
        """
        Metadata access.

        Determined by admin access permissions. Defaults to no access if no access permissions are set.
        """
        if self.admin_metadata is None:
            return AccessLevel.NONE
        return self._compute_access_level(permissions=self.admin_metadata.metadata_permissions)

    @property
    def admin_resource_access(self) -> AccessLevel:
        """
        Resource access.

        Determined by admin access permissions. Defaults to no access if no access permissions are set.
        """
        if self.admin_metadata is None:
            return AccessLevel.NONE
        return self._compute_access_level(permissions=self.admin_metadata.resource_permissions)

    @property
    def admin_gitlab_issues(self) -> list[str]:
        """Optional list of associated GitLab issues."""
        if self.admin_metadata is None:
            return []
        return self.admin_metadata.gitlab_issues

    @property
    def aggregations(self) -> Aggregations:
        """Aggregations."""
        return self.record.identification.aggregations

    @property
    def bounding_extent(self) -> Extent | None:
        """Bounding extent."""
        try:
            return self.extents.filter(identifier="bounding")[0]  # ty: ignore[invalid-return-type]
        except IndexError:
            return None

    @property
    def citation_raw(self) -> str | None:
        """Optional raw citation."""
        _citation = self.record.identification.other_citation_details
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
    def contacts(self) -> Contacts:
        """
        Contacts.

        Casts copies of Record Contact items as Item Contact items, to leverage Item specific functionality.
        Cast items are contained in a Record Contacts container subclass, to reflect correct types.
        """
        return Contacts([Contact(contact) for contact in self.record.identification.contacts])

    @property
    def constraints(self) -> Constraints:
        """Resource Constraints."""
        return self.record.identification.constraints

    @property
    def description_raw(self) -> str:
        """Raw Abstract."""
        return self.record.identification.abstract

    @property
    def description_md(self) -> str:
        """Abstract with Markdown formatting if present."""
        return self.description_raw

    @property
    def description_html(self) -> str:
        """Abstract with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.description_md)

    @property
    def distributions(self) -> list[Distribution]:
        """Distributions."""
        return self.record.distribution

    @property
    def edition(self) -> str | None:
        """Edition."""
        return self.record.identification.edition

    @property
    def extents(self) -> Extents:
        """
        Extents.

        Casts copies of Record Extent items as Item Extent items, to leverage Item specific functionality.
        Cast items are contained in a Record Extents container subclass, to reflect correct types.
        """
        return Extents([Extent(extent) for extent in self.record.identification.extents])

    @property
    def graphics(self) -> GraphicOverviews:
        """
        Graphic overviews (thumbnails).

        See `overview_graphic` for accessing primary/default overview.
        """
        return self.record.identification.graphic_overviews

    @property
    def href(self) -> str:
        """Item catalogue URL."""
        return f"/items/{self.resource_id}/"

    @property
    def identifiers(self) -> Identifiers:
        """Identifiers."""
        return self.record.identification.identifiers

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
        - administrative_metadata: see `admin_metadata` property
        - width: width of resource when printed in mm
        - height: height of resource when printed in mm
        - sheet_number: series page/sheet number (due to an oversight in the BAS ISO JSON Schema)

        This is not intended to be portable/interoperable across other systems, and is used only within the BAS
        metadata ecosystem of tools but is human-readable to an extent so could be shown elsewhere.
        """
        try:
            return get_kv(self.record)
        except (ValueError, TypeError):
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
        if self.record.data_quality is None or self.record.data_quality.lineage is None:
            return None
        return self.record.data_quality.lineage.statement

    @property
    def lineage_md(self) -> str | None:
        """Optional lineage statement with Markdown formatting if present."""
        return self.lineage_raw

    @property
    def lineage_html(self) -> str | None:
        """Optional lineage statement with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.lineage_md) if self.lineage_md is not None else None

    @property
    def overview_graphic(self) -> GraphicOverview | None:
        """
        Optional primary/default graphic overview.

        I.e. Item thumbnail.

        For convenience. Where 'overview' is a conventional and presumed unique identifier.
        """
        return next((graphic for graphic in self.graphics.filter(identifier="overview")), None)

    @property
    def projection(self) -> Identifier | None:
        """
        Optional projection identifier.

        Limited to EPSG projections so we can predictably handle them.
        """
        ref = self.record.reference_system_info
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
        return self.record.file_identifier

    @property
    def resource_revision(self) -> str | None:
        """
        Optional resource revision (commit).

        If item relates to a RecordRevision.
        """
        if isinstance(self.record, RecordRevision):
            return self.record.file_revision
        return None

    @property
    def resource_type(self) -> HierarchyLevelCode:
        """
        Resource type.

        AKA hierarchy-level/scope-code.
        """
        return self.record.hierarchy_level

    @property
    def series_descriptive(self) -> Series:
        """
        Optional descriptive series.

        Typically used for published maps.

        Due to a bug in early revisions of the V4 BAS ISO JSON Schema, the 'page' (sheet number) property could not be
        set. This class supports loading an optional 'sheet_number' from KV properties if not set in the series element.
        """
        series = self.record.identification.series
        if series and series.page:
            return series

        sheet_number = self.kv.get("sheet_number", None)
        if sheet_number:
            series.page = sheet_number
        return series

    @property
    def summary_raw(self) -> str | None:
        """Optional raw Summary (purpose)."""
        return self.record.identification.purpose

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
        return self.record.identification.title

    @property
    def title_md(self) -> str:
        """Title with Markdown formatting."""
        return self.title_raw

    @property
    def title_html(self) -> str:
        """Title with Markdown formatting, if present, encoded as HTML."""
        return md_as_html(self.title_md)

    @property
    def title_plain(self) -> str:
        """Title without Markdown formatting."""
        return md_as_plain(self.title_md)
