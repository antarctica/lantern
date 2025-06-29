import json
from collections.abc import Callable
from typing import Any

from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.config import Config
from lantern.models.item.base import ItemBase
from lantern.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    Extent,
    Identifiers,
    Maintenance,
    PageHeader,
    PageSummary,
)
from lantern.models.item.catalogue.tabs import (
    AdditionalInfoTab,
    AuthorsTab,
    ContactTab,
    DataTab,
    ExtentTab,
    ItemsTab,
    LicenceTab,
    LineageTab,
    RelatedTab,
    Tab,
)
from lantern.models.record import Record
from lantern.models.record.elements.identification import GraphicOverview
from lantern.models.record.enums import ContactRoleCode
from lantern.models.record.summary import RecordSummary
from lantern.models.templates import PageMetadata


class ItemInvalidError(Exception):
    """Raised when an item is based on an invalid record."""

    def __init__(self, validation_error: Exception) -> None:
        self.validation_error = validation_error


class ItemCatalogue(ItemBase):
    """
    Representation of a resource within the BAS Data Catalogue.

    Catalogue items structure a base item into the (HTML) page structure used in the BAS Data Catalogue website using
    Jinja2 templates and classes representing the various tabs and other sections that form these pages.

    In addition to a catalogue Record instance, this Item implementation requires:
    - endpoints for external services used in this template, such as the item contact form and extent map
    - a callable to get a RecordSummary for a given identifier (used for related items from aggregations)

    Note: This class is an incomplete rendering of Record properties (which is itself an incomplete mapping of the
    ISO 19115:2003 / 19115-2:2009 standards). The list below is a work in progress.

    Supported properties:
    - file_identifier
    - hierarchy_level
    - reference_system_info
    - identification.citation.title
    - identification.citation.dates
    - identification.citation.edition
    - identification.citation.contacts ('author' roles and a single 'point of contact' role only, and except `contact.position`)
    - identification.citation.series
    - identification.citation.identifiers[namespace='doi']
    - identification.citation.identifiers[namespace='isbn']
    - identification.citation.identifiers[namespace='gitlab.data.bas.ac.uk'] (as references only)
    - identification.abstract
    - identification.aggregations ('collections' and 'items' only)
    - identification.constraints ('licence' only)
    - identification.maintenance
    - identification.extent (single bounding temporal and geographic bounding box extent only)
    - identification.other_citation_details
    - identification.graphic_overviews
    - identification.spatial_resolution
    - identification.supplemental_information (for physical dimensions only)
    - data_quality.lineage.statement
    - data_quality.domain_consistency
    - distributor.format (`format` and `href` only)
    - distributor.transfer_option (except `online_resource.protocol`)

    Unsupported properties:
    - identification.purpose (except as used in ItemSummaries)

    Intentionally omitted properties:
    - *.character_set (not useful to end-users, present in underlying record)
    - *.language (not useful to end-users, present in underlying record)
    - *.online_resource.protocol (not useful to end-users, present in underlying record)
    - identification.citation.identifiers[namespace='data.bas.ac.uk'] (maybe shown in citation, otherwise intended for external use)
    - identification.citation.identifiers[namespace='alias.data.bas.ac.uk'] (maybe shown in citation, otherwise consumed internally)
    - distribution.distributor
    """

    def __init__(
        self, config: Config, record: Record, get_record_summary: Callable[[str], RecordSummary], **kwargs: Any
    ) -> None:
        super().__init__(record)
        self._config = config
        self._get_summary = get_record_summary
        _loader = PackageLoader("lantern", "resources/templates")
        self._jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)

        self.validate(record)

    @staticmethod
    def validate(record: Record) -> None:
        """
        Validate underlying record against Data Catalogue requirements.

        Validation based on [1]. Failed validation will raise a `RecordInvalidError` exception.

        Note: The requirement for a file_identifier is already checked in ItemBase.

        [1] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/v0.7.5/docs/implementation.md#minimum-record-requirements
        """
        record.validate()

        self_identifiers = record.identification.identifiers.filter(namespace="data.bas.ac.uk")
        if not self_identifiers:
            msg = "Record must include an identification identifier with the 'data.bas.ac.uk' namespace."
            exp = ValueError(msg)
            raise ItemInvalidError(validation_error=exp)
        if self_identifiers[0].identifier != record.file_identifier:
            msg = "Record 'data.bas.ac.uk' identifier must match file identifier."
            exp = ValueError(msg)
            raise ItemInvalidError(validation_error=exp)

        pocs = record.identification.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)
        if not pocs:
            msg = "Record must include an identification contact with the Point of Contact role."
            exp = ValueError(msg)
            raise ItemInvalidError(validation_error=exp)

    @staticmethod
    def _prettify_html(html: str) -> str:
        """
        Prettify HTML string, removing any empty lines.

        Without very careful whitespace control, Jinja templates quickly look messy where conditionals and other logic
        is used. Whilst this doesn't strictly matter, it is nicer if output looks well-formed by removing empty lines.

        This gives a 'flat' structure when viewed as source. Browser dev tools will reformat this into a tree structure.
        The `prettify()` method is not used as it splits all elements onto new lines, which causes layout/spacing bugs.
        """
        return str(BeautifulSoup(html, parser="html.parser", features="lxml"))

    @property
    def _aggregations(self) -> Aggregations:
        """Aggregations."""
        return Aggregations(aggregations=self.aggregations, get_summary=self._get_summary)

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

    @property
    def _items(self) -> ItemsTab:
        """Items tab."""
        return ItemsTab(aggregations=self._aggregations)

    @property
    def _data(self) -> DataTab:
        """Data tab."""
        return DataTab(access_type=self.access_type, distributions=self.distributions)

    @property
    def _authors(self) -> AuthorsTab:
        """Authors tab."""
        return AuthorsTab(item_type=self.resource_type, authors=self.contacts.filter(roles=ContactRoleCode.AUTHOR))

    @property
    def _licence(self) -> LicenceTab:
        """Licence tab."""
        return LicenceTab(jinja=self._jinja, item_type=self.resource_type, licence=super().licence)

    @property
    def _extent(self) -> ExtentTab:
        """Extent tab."""
        bounding_ext = self.bounding_extent
        extent = (
            Extent(bounding_ext, embedded_maps_endpoint=self._config.TEMPLATES_ITEM_MAPS_ENDPOINT)
            if bounding_ext
            else None
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
            dates=self._dates,
            series=self.series_descriptive,
            scale=self._record.identification.spatial_resolution,
            datestamp=self._record.metadata.date_stamp,
            projection=self.projection,
            maintenance=self._maintenance,
            standard=self._record.metadata.metadata_standard,
            profiles=self._record.data_quality.domain_consistency if self._record.data_quality else None,
            kv=self.kv,
        )

    @property
    def _contact(self) -> ContactTab:
        """Contact tab."""
        poc = self.contacts.filter(roles=ContactRoleCode.POINT_OF_CONTACT)[0]
        return ContactTab(
            contact=poc,
            item_id=self.resource_id,
            item_title=self.title_plain,
            form_action=self._config.TEMPLATES_ITEM_CONTACT_ENDPOINT,
        )

    @property
    def _overview_graphic(self) -> GraphicOverview | None:
        """
        Optional 'overview' graphic overview.

        I.e. a default graphic.
        """
        return next((graphic for graphic in self.graphics if graphic.identifier == "overview"), None)

    @property
    def page_metadata(self) -> PageMetadata:
        """Templates page metadata."""
        return PageMetadata(
            sentry_src=self._config.TEMPLATES_SENTRY_SRC,
            plausible_domain=self._config.TEMPLATES_PLAUSIBLE_DOMAIN,
            html_title=self._html_title,
            html_open_graph=self._html_open_graph,
            html_schema_org=self._html_schema_org,
        )

    @property
    def _html_title(self) -> str:
        """Title with without formatting with site name appended, for HTML title element."""
        return f"{self.title_plain}"

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
            "og:url": f"https://data.bas.ac.uk/items/{self.resource_id}",
        }

        if self.summary_plain:
            tags["og:description"] = self.summary_plain
        if self._dates.publication:
            # noinspection PyUnresolvedReferences
            tags["og:article:published_time"] = self._dates.publication.datetime
        if self._overview_graphic:
            tags["og:image"] = self._overview_graphic.href

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
            "url": f"https://data.bas.ac.uk/items/{self.resource_id}",
        }

        if self.summary_plain:
            doc["description"] = self.summary_plain

        if self._overview_graphic:
            doc["image"] = self._overview_graphic.href

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
            access_type=self.access_type,
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

    def render(self) -> str:
        """Render HTML representation of item."""
        raw = self._jinja.get_template("item.html.j2").render(item=self, meta=self.page_metadata)
        return self._prettify_html(raw)
