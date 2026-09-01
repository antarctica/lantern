from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
)
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.base.item import ItemBase
from lantern.models.item.catalogue.const import CONTAINER_SUPER_TYPES
from lantern.models.item.catalogue.elements import Dates, Extent, FormattedDate, PageHeader, PageSummary
from lantern.models.item.catalogue.enums import ItemSuperType
from lantern.models.item.catalogue.tabs import (
    AdditionalInfoTab,
    AdminTab,
    Aggregations,
    AuthorsTab,
    ContactTab,
    DataTab,
    ExtentTab,
    Identifiers,
    ItemsTab,
    LicenceTab,
    LineageTab,
    Maintenance,
    RelatedTab,
    Tab,
)
from lantern.models.site import OpenGraphMeta, SchemaOrgAuthor, SchemaOrgMeta, SiteMeta
from lantern.utils import is_live_record

if TYPE_CHECKING:
    from lantern.lib.metadata_library.models.record.elements.common import Constraint
    from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
    from lantern.models.record.revision import RecordRevision
    from lantern.stores.base import SelectRecordProtocol


class ItemCatalogue(ItemBase):
    """
    Representation of a resource within the BAS Data Catalogue.

    Catalogue items structure a base item into the (HTML) page structure used in the BAS Data Catalogue website using
    Jinja2 templates and classes representing the various tabs and other sections that form these pages.

    This Item subclass has stricter and additional requirements:
    - site metadata (for item contact form and extent map endpoints used in templates)
    - a catalogue RecordRevision instance with administrative metadata
    - a callable to get a Record for a given identifier (used for related items via aggregations)

    This class supports trusted contexts (e.g. internal users), where an additional ADMIN tab is included.

    Note: This class is an incomplete rendering of Record properties (which is itself an incomplete mapping of the
    ISO 19115:2003 / 19115-2:2009 standards). See `docs/data_model.md#catalogue-item-limitations` for more information.

    Note: Properties are cached as they are accessed multiple times during rendering (e.g. tabs are built for both
    navigation and content, and aggregations resolve related records via the store).
    """

    _record: RecordRevision

    def __init__(
        self,
        site_meta: SiteMeta,
        record: RecordRevision,
        admin_meta_keys: AdministrationKeys | None,
        select_record: SelectRecordProtocol,
        trusted_context: bool,
        **kwargs: Any,
    ) -> None:
        super().__init__(record=record, admin_keys=admin_meta_keys)
        self._meta = site_meta
        self._trusted_context = trusted_context
        self._select_record = select_record

    @cached_property
    def _super_type(self) -> ItemSuperType:
        """Resource type mapped to a general 'super' type."""
        if self.resource_type in CONTAINER_SUPER_TYPES:
            return ItemSuperType.CONTAINER
        return ItemSuperType.RESOURCE

    @cached_property
    def _aggregations(self) -> Aggregations:
        """Aggregations."""
        return Aggregations(
            admin_meta_keys=self._admin_keys, aggregations=self.aggregations, select_record=self._select_record
        )

    @cached_property
    def _dates(self) -> Dates:
        """Formatted dates."""
        return Dates(self.record.identification.dates)

    @cached_property
    def _identifiers(self) -> Identifiers:
        """Identifiers."""
        return Identifiers(self.record.identification.identifiers)

    @cached_property
    def _maintenance(self) -> Maintenance | None:
        """Friendly code list terms."""
        return Maintenance(self.record.identification.maintenance)

    @cached_property
    def _metadata_licence(self) -> Constraint | None:
        """Licence constraint."""
        licences = self.record.metadata.constraints.filter(
            types=ConstraintTypeCode.USAGE, restrictions=ConstraintRestrictionCode.LICENSE
        )
        try:
            return licences[0]
        except IndexError:
            return None

    @cached_property
    def _revision(self) -> Link:
        """Link to the record revision."""
        path = f"records/{self.resource_id[:2]}/{self.resource_id[2:4]}/{self.resource_id}.json"
        href = f"{self._meta.build_repo_base_url}/-/blob/{self._record.file_revision}/{path}"
        short_ref = self._record.file_revision[:8]
        return Link(value=short_ref, href=href, external=True)

    @cached_property
    def _restricted(self) -> bool:
        """
        Whether the item is restricted.

        Based on resource access only. Restricted metadata is not supported.
        """
        return self.admin_resource_access != AccessLevel.PUBLIC

    @cached_property
    def _items(self) -> ItemsTab:
        """Items tab."""
        return ItemsTab(aggregations=self._aggregations)

    @cached_property
    def _data(self) -> DataTab:
        """Data tab."""
        return DataTab(restricted=self._restricted, distributions=self.distributions)

    @cached_property
    def _authors(self) -> AuthorsTab:
        """Authors tab."""
        return AuthorsTab(item_super_type=self._super_type, authors=self.contacts.filter(roles=ContactRoleCode.AUTHOR))

    @cached_property
    def _licence(self) -> LicenceTab:
        """
        Licence tab.

        For the resource. The Metadata licence (if set) is shown in the Additional Information tab.
        """
        return LicenceTab(
            item_super_type=self._super_type,
            licence=super().licence_enum,
            rights_holders=self.contacts.filter(roles=ContactRoleCode.RIGHTS_HOLDER),
        )

    @cached_property
    def _extent(self) -> ExtentTab:
        """Extent tab."""
        bounding_ext = self.bounding_extent
        extent = (
            Extent(bounding_ext, embedded_maps_endpoint=self._meta.embedded_maps_endpoint) if bounding_ext else None
        )
        return ExtentTab(extent=extent)

    @cached_property
    def _lineage(self) -> LineageTab:
        """Lineage tab."""
        return LineageTab(item_super_type=self._super_type, statement=self.lineage_html)

    @cached_property
    def _related(self) -> RelatedTab:
        """Related tab."""
        return RelatedTab(item_type=self.resource_type, aggregations=self._aggregations)

    @cached_property
    def _additional_info(self) -> AdditionalInfoTab:
        """Additional Information tab."""
        return AdditionalInfoTab(
            item_id=self.resource_id,
            item_type=self.resource_type,
            identifiers=self._identifiers,
            edition=self.edition,
            dates=self._dates,
            series=self.series_descriptive,
            scale=self.record.identification.spatial_resolution,
            datestamp=self.record.metadata.date_stamp,
            projection=self.projection,
            maintenance=self._maintenance,
            standard=self.record.metadata.metadata_standard,
            profiles=self.record.data_quality.domain_consistency if self.record.data_quality else None,
            metadata_licence=self._metadata_licence,
            kv=self.kv,
            build_time=self._meta.build_time,
        )

    @cached_property
    def _contact(self) -> ContactTab:
        """Contact tab."""
        poc = self.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)[0]
        return ContactTab(
            contact=poc,
            item_id=self.resource_id,
            item_title=self.title_plain,
            form_action=self._meta.items_enquires_endpoint,
            turnstile_key=self._meta.turnstile_key,
        )

    @cached_property
    def _admin(self) -> AdminTab:
        """Admin tab (secure contexts only)."""
        return AdminTab(
            trusted=self._trusted_context,
            item_id=self.resource_id,
            revision=self._revision,
            gitlab_issues=self.admin_gitlab_issues,
            restricted=self._restricted,
            metadata_access=self.admin_metadata_access,
            resource_access=self.admin_resource_access,
            admin_meta=self.admin_metadata,
        )

    @property
    def site_meta(self) -> SiteMeta:
        """Site metadata for item."""
        self._meta.html_title = self.title_plain
        self._meta.html_description = self.summary_plain
        self._meta.html_open_graph = self._html_open_graph
        self._meta.html_schema_org = self._html_schema_org
        return self._meta

    @cached_property
    def _html_open_graph(self) -> OpenGraphMeta:
        """
        Open Graph metadata tags.

        See `self.schema_org` for more specific Microsoft Teams support.

        `self._dates` returns values as `FormattedDates` not `Date` so `.datetime` returns a pre-formatted value.
        """
        publication_date = cast("FormattedDate | None", self._dates.publication)
        image_href = self.overview_graphic.href if self.overview_graphic is not None else None
        return OpenGraphMeta(
            title=self.title_plain,
            url=f"{self._meta.base_url}/items/{self.resource_id}",
            description=self.summary_plain,
            image=image_href,
            published_at=publication_date.datetime if publication_date else None,
        )

    @cached_property
    def _html_schema_org(self) -> SchemaOrgMeta:
        """Schema.org metadata."""
        authors: list[SchemaOrgAuthor] = []
        for author in self.contacts.filter(roles=ContactRoleCode.AUTHOR):
            if author.individual is not None:
                authors.append(SchemaOrgAuthor(type_="Person", name=author.individual.name, url=author.individual.href))
            elif author.organisation is not None:  # pragma: no branch
                authors.append(
                    SchemaOrgAuthor(type_="Organization", name=author.organisation.name, url=author.organisation.href)
                )

        return SchemaOrgMeta(
            headline=self.title_plain,
            url=f"{self._meta.base_url}/items/{self.resource_id}",
            description=self.summary_plain,
            image=self.overview_graphic.href if self.overview_graphic else None,
            creator=authors,
        )

    @cached_property
    def page_header(self) -> PageHeader:
        """Page header."""
        return PageHeader(title=self.title_html, item_type=self.resource_type)

    @cached_property
    def live(self) -> bool:
        """Whether item is updated frequently enough to be considered 'live'."""
        return is_live_record(self._record)

    @cached_property
    def summary(self) -> PageSummary:
        """Item summary."""
        return PageSummary(
            item_super_type=self._super_type,
            edition=self.edition,
            published_date=cast("FormattedDate | None", self._dates.publication),
            revision_date=self._dates.revision_relative,
            aggregations=self._aggregations,
            live=self.live,
            restricted=self._restricted,
            citation=self.citation_html,
            description=self.description_html,
        )

    @cached_property
    def tabs(self) -> list[Tab]:
        """For generating item navigation."""
        return [
            self._items,
            self._data,
            self._authors,
            self._licence,
            self._extent,
            self._lineage,
            self._related,
            self._additional_info,
            self._contact,
            self._admin,
        ]

    @cached_property
    def default_tab_anchor(self) -> str:
        """
        Anchor of first enabled tab.

        Only tabs shown before the additional information are considered, as it is always enabled. Candidates are listed
        explicitly as building later tabs (contact, admin) requires properties that are not required for all records.
        """
        candidates = [
            self._items,
            self._data,
            self._authors,
            self._licence,
            self._extent,
            self._lineage,
            self._related,
        ]
        for tab in candidates:
            if tab.enabled:
                return tab.anchor
        return self._additional_info.anchor
