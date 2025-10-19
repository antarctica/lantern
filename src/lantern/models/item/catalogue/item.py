import json
from collections.abc import Callable
from typing import Any

from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.base.item import ItemBase
from lantern.models.item.catalogue.elements import Dates, Extent, PageHeader, PageSummary
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
from lantern.models.record.revision import RecordRevision
from lantern.models.site import SiteMeta


class ItemCatalogue(ItemBase):
    """
    Representation of a resource within the BAS Data Catalogue.

    Catalogue items structure a base item into the (HTML) page structure used in the BAS Data Catalogue website using
    Jinja2 templates and classes representing the various tabs and other sections that form these pages.

    In addition to a catalogue Record instance, this Item variant requires:
    - endpoints for external services used in this template, such as the item contact form and extent map, via site_meta
    - keys to decrypt and verify administrative metadata for reading the record's administrative metadata
    - a callable to get a RecordSummary for a given identifier (used for related items from aggregations)

    Note: This class is an incomplete rendering of Record properties (which is itself an incomplete mapping of the
    ISO 19115:2003 / 19115-2:2009 standards). See `docs/data_model.md#catalogue-item-limitations` for more information.
    """

    def __init__(
        self,
        site_meta: SiteMeta,
        record: RecordRevision,
        admin_meta_keys: AdministrationKeys | None,
        trusted_context: bool,
        get_record: Callable[[str], RecordRevision],
        **kwargs: Any,
    ) -> None:
        super().__init__(record=record, admin_keys=admin_meta_keys)
        self._meta = site_meta
        self._trusted_context = trusted_context
        self._get_record = get_record

        if not isinstance(self._record, RecordRevision):
            msg = "record must be a RecordRevision instance"
            raise TypeError(msg) from None
        self._record: RecordRevision

    @property
    def _aggregations(self) -> Aggregations:
        """Aggregations."""
        return Aggregations(aggregations=self.aggregations, get_record=self._get_record)

    @property
    def _dates(self) -> Dates:
        """Formatted dates."""
        return Dates(self._record.identification.dates)

    @property
    def _identifiers(self) -> Identifiers:
        """Identifiers."""
        return Identifiers(self._record.identification.identifiers)

    @property
    def _maintenance(self) -> Maintenance | None:
        """Formatted dates."""
        return Maintenance(self._record.identification.maintenance)

    # noinspection PyUnresolvedReferences
    @property
    def _revision(self) -> Link:
        """Link to the record revision."""
        path = f"records/{self.resource_id[:2]}/{self.resource_id[2:4]}/{self.resource_id}.json"
        href = f"{self._meta.build_repo_base_url}/-/blob/{self._record.file_revision}/{path}"
        short_ref = self._record.file_revision[:8]
        return Link(value=short_ref, href=href, external=True)

    @property
    def _restricted(self) -> bool:
        """Whether the item is restricted."""
        return self.admin_access_level != AccessLevel.PUBLIC

    @property
    def _items(self) -> ItemsTab:
        """Items tab."""
        return ItemsTab(aggregations=self._aggregations)

    @property
    def _data(self) -> DataTab:
        """Data tab."""
        return DataTab(restricted=self._restricted, distributions=self.distributions)

    @property
    def _authors(self) -> AuthorsTab:
        """Authors tab."""
        return AuthorsTab(item_type=self.resource_type, authors=self.contacts.filter(roles=ContactRoleCode.AUTHOR))

    @property
    def _licence(self) -> LicenceTab:
        """Licence tab."""
        return LicenceTab(
            item_type=self.resource_type,
            licence=super().licence,
            rights_holders=self.contacts.filter(roles=ContactRoleCode.RIGHTS_HOLDER),
        )

    @property
    def _extent(self) -> ExtentTab:
        """Extent tab."""
        bounding_ext = self.bounding_extent
        extent = (
            Extent(bounding_ext, embedded_maps_endpoint=self._meta.embedded_maps_endpoint) if bounding_ext else None
        )
        return ExtentTab(extent=extent)

    @property
    def _lineage(self) -> LineageTab:
        """Lineage tab."""
        return LineageTab(statement=self.lineage_html)

    @property
    def _related(self) -> RelatedTab:
        """Related tab."""
        return RelatedTab(item_type=self.resource_type, aggregations=self._aggregations)

    @property
    def _additional_info(self) -> AdditionalInfoTab:
        """Additional Information tab."""
        return AdditionalInfoTab(
            item_id=self.resource_id,
            item_type=self.resource_type,
            identifiers=self._identifiers,
            gitlab_issues=self.admin_gitlab_issues,
            dates=self._dates,
            series=self.series_descriptive,
            scale=self._record.identification.spatial_resolution,
            datestamp=self._record.metadata.date_stamp,
            projection=self.projection,
            maintenance=self._maintenance,
            standard=self._record.metadata.metadata_standard,
            profiles=self._record.data_quality.domain_consistency if self._record.data_quality else None,
            kv=self.kv,
            build_time=self._meta.build_time,
        )

    @property
    def _contact(self) -> ContactTab:
        """Contact tab."""
        poc = self.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)[0]
        return ContactTab(
            contact=poc,
            item_id=self.resource_id,
            item_title=self.title_plain,
            form_action=self._meta.items_enquires_endpoint,
            turnstile_key=self._meta.items_enquires_turnstile_key,
        )

    @property
    def _admin(self) -> AdminTab:
        """Admin tab (secure contexts only)."""
        return AdminTab(
            trusted=self._trusted_context,
            item_id=self.resource_id,
            revision=self._revision,
            gitlab_issues=self.admin_gitlab_issues,
            restricted=self._restricted,
            access_level=self.admin_access_level,
            access_permissions=self._admin_metadata.access_permissions,
        )

    @property
    def site_metadata(self) -> SiteMeta:
        """Site metadata for item."""
        self._meta.html_title = self.title_plain
        self._meta.html_description = self.summary_plain
        self._meta.html_open_graph = self._html_open_graph
        self._meta.html_schema_org = self._html_schema_org
        return self._meta

    @property
    def _html_open_graph(self) -> dict[str, str]:
        """
        Open Graph meta tags.

        For item link previews and unfurling in social media sites, chat clients, etc.
        See https://ogp.me/ for details.
        See `self.schema_org` for more specific Microsoft Teams support.
        """
        tags = {
            "og:locale": "en_GB",
            "og:site_name": "BAS Data Catalogue",
            "og:type": "article",
            "og:title": self.title_plain,
            "og:url": f"{self._meta.base_url}/items/{self.resource_id}",
        }

        if self.summary_plain:
            tags["og:description"] = self.summary_plain
        if self._dates.publication:
            # noinspection PyUnresolvedReferences
            tags["og:article:published_time"] = self._dates.publication.datetime
        if self.overview_graphic:
            tags["og:image"] = self.overview_graphic.href

        return tags

    @property
    def _html_schema_org(self) -> str:
        """
        Schema.org metadata.

        Support is limited to item link unfurling in Microsoft Teams.
        See https://learn.microsoft.com/en-us/microsoftteams/platform/messaging-extensions/how-to/micro-capabilities-for-website-links?tabs=article

        Other Schema.org use-cases may work but are not tested.
        """
        doc = {
            "@context": "http://schema.org/",
            "@type": "Article",
            "name": "BAS Data Catalogue",
            "headline": self.title_plain,
            "url": f"{self._meta.base_url}/items/{self.resource_id}",
        }

        if self.summary_plain:
            doc["description"] = self.summary_plain

        if self.overview_graphic:
            doc["image"] = self.overview_graphic.href

        author_names = []
        for author in self.contacts.filter(roles=ContactRoleCode.AUTHOR):
            if author.individual is not None:
                author_names.append(author.individual.name)
                continue
            author_names.append(author.organisation.name)
        if len(author_names) > 0:
            # set as comma separated list of names, except last element which uses '&'
            doc["creator"] = (
                ", ".join(author_names[:-1]) + " & " + author_names[-1] if len(author_names) > 1 else author_names[0]
            )

        return json.dumps(doc, indent=2)

    @property
    def page_header(self) -> PageHeader:
        """Page header."""
        return PageHeader(title=self.title_html, item_type=self.resource_type)

    @property
    def summary(self) -> PageSummary:
        """Item summary."""
        return PageSummary(
            item_type=self.resource_type,
            edition=self.edition,
            published_date=self._dates.publication,
            revision_date=self._dates.revision,
            aggregations=self._aggregations,
            restricted=self._restricted,
            citation=self.citation_html,
            abstract=self.abstract_html,
        )

    @property
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

    @property
    def default_tab_anchor(self) -> str:
        """Anchor of first enabled tab."""
        for tab in [
            self._items,
            self._data,
            self._authors,
            self._licence,
            self._extent,
            self._lineage,
            self._related,
        ]:
            if tab.enabled:
                return tab.anchor
        return self._additional_info.anchor
