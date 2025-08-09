import locale
from abc import ABC, abstractmethod
from datetime import date
from urllib.parse import parse_qs, urlparse

from jinja2 import Environment

from lantern.lib.metadata_library.models.record.elements.common import Date, Identifier, Series
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution as RecordDistribution
from lantern.lib.metadata_library.models.record.elements.identification import Constraint
from lantern.lib.metadata_library.models.record.elements.metadata import MetadataStandard
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from lantern.models.item.base import AccessType
from lantern.models.item.base.elements import Contact, Link
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.enums import ResourceTypeLabel
from lantern.models.item.catalogue.distributions import (
    ArcGisFeatureLayer,
    ArcGisOgcApiFeatures,
    ArcGisVectorTileLayer,
    BasPublishedMap,
    Distribution,
    GeoJson,
    GeoPackage,
    Jpeg,
    Pdf,
    Png,
    Shapefile,
)
from lantern.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    FormattedDate,
    Identifiers,
    ItemSummaryCatalogue,
    Maintenance,
)
from lantern.models.item.catalogue.enums import Licence, ResourceTypeIcon


class Tab(ABC):
    """Abstract item/page tab."""

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        ...

    @property
    @abstractmethod
    def anchor(self) -> str:
        """HTML anchor for tab."""
        ...

    @property
    @abstractmethod
    def title(self) -> str:
        """Tab title."""
        ...

    @property
    @abstractmethod
    def icon(self) -> str:
        """Tab icon class."""
        ...


class ItemsTab(Tab):
    """Items tab."""

    def __init__(self, aggregations: Aggregations) -> None:
        self._aggregations = aggregations
        self._items = self._aggregations.child_items

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return len(self._items) > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "items"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Items"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-grip-horizontal"

    @property
    def items(self) -> list[ItemSummaryCatalogue]:
        """Items that form the current item."""
        return self._items


class DataTab(Tab):
    """Data tab."""

    def __init__(self, access_type: AccessType, distributions: list[RecordDistribution]) -> None:
        self._access = access_type
        self._resource_distributions = distributions
        self._supported_distributions = [
            ArcGisFeatureLayer,
            ArcGisOgcApiFeatures,
            ArcGisVectorTileLayer,
            BasPublishedMap,
            GeoPackage,
            GeoJson,
            Jpeg,
            Pdf,
            Png,
            Shapefile,
        ]
        self._processed_distributions = self._process_distributions()

    def _process_distributions(self) -> list[Distribution]:
        """
        Determine supported distribution options.

        Checks each (unprocessed) resource distribution against supported catalogue distribution types.
        """
        processed = []
        for dist_option in self._resource_distributions:
            for dist_type in self._supported_distributions:
                if dist_type.matches(option=dist_option, other_options=self._resource_distributions):
                    # noinspection PyTypeChecker
                    processed.append(
                        dist_type(
                            option=dist_option, other_options=self._resource_distributions, access_type=self._access
                        )
                    )
        return processed

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return len(self._processed_distributions) > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "data"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Data"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-cube"

    @property
    def access(self) -> AccessType:
        """Access restrictions for item."""
        return self._access

    @property
    def items(self) -> list[Distribution]:
        """Processed distribution options."""
        return self._processed_distributions


class ExtentTab(Tab):
    """Extent tab."""

    def __init__(self, extent: ItemExtent | None = None) -> None:
        self._extent = extent

    def __getattribute__(self, name: str) -> str | None:
        """Proxy calls to self._extent if applicable."""
        extent = object.__getattribute__(self, "_extent")
        if extent is not None and hasattr(extent, name):
            return getattr(extent, name)

        # pass-through
        return object.__getattribute__(self, name)

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return self._extent is not None

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "extent"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Extent"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-expand-arrows"


class AuthorsTab(Tab):
    """Authors tab."""

    def __init__(self, item_type: HierarchyLevelCode, authors: list[Contact]) -> None:
        self._item_type = item_type
        self._authors = authors

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return False
        return len(self._authors) > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "authors"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Authors"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-user-friends"

    @property
    def items(self) -> list[Contact]:
        """Authors."""
        return self._authors


class LicenceTab(Tab):
    """Licence tab."""

    def __init__(self, jinja: Environment, item_type: HierarchyLevelCode, licence: Constraint | None) -> None:
        self._jinja = jinja
        self._item_type = item_type
        self._licence = licence

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_type == HierarchyLevelCode.COLLECTION:
            return False
        return self._licence is not None

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "licence"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Licence"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-file-certificate"

    @property
    def slug(self) -> Licence | None:
        """Licence reference."""
        return Licence(self._licence.href) if self._licence is not None else None


class LineageTab(Tab):
    """Lineage tab."""

    def __init__(self, statement: str | None) -> None:
        self._statement = statement

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return self._statement is not None

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "lineage"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Lineage"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-scroll-old"

    @property
    def statement(self) -> str | None:
        """Lineage statement."""
        return self._statement


class RelatedTab(Tab):
    """Related tab."""

    def __init__(self, item_type: HierarchyLevelCode, aggregations: Aggregations) -> None:
        self._item_type = item_type
        self._aggregations = aggregations

    def __getattribute__(self, name: str) -> str | int | None:
        """Proxy calls to self._aggregations if applicable."""
        aggregation = object.__getattribute__(self, "_aggregations")
        if hasattr(aggregation, name):
            return getattr(aggregation, name)

        # pass-through
        return object.__getattribute__(self, name)

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        all_agg = len(self._aggregations)
        if self._item_type == HierarchyLevelCode.COLLECTION:
            # if all aggregations are a collections items, disable tab as these are shown in item tab
            return len(self.child_items) != all_agg
        return all_agg > 0

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "related"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Related"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-project-diagram"


class AdditionalInfoTab(Tab):
    """Additional Information tab."""

    def __init__(
        self,
        item_id: str,
        item_type: HierarchyLevelCode,
        identifiers: Identifiers,
        dates: Dates,
        datestamp: date,
        kv: dict[str, str],
        series: Series | None = None,
        scale: str | None = None,
        projection: Identifier | None = None,
        maintenance: Maintenance | None = None,
        standard: MetadataStandard | None = None,
        profiles: list[DomainConsistency] | None = None,
    ) -> None:
        self._item_id = item_id
        self._item_type = item_type
        self._series = series
        self._scale = scale
        self._projection = projection
        self._identifiers = identifiers
        self._dates = dates
        self._datestamp = datestamp
        self._maintenance = maintenance
        self._standard = standard
        self._profiles = profiles if profiles is not None else []
        self._kv = kv

    @staticmethod
    def _format_scale(value: int | None) -> str | None:
        """Format scale value."""
        if value is None:
            return None
        locale.setlocale(locale.LC_ALL, "en_GB.UTF-8")
        return f"1:{locale.format_string('%d', value, grouping=True)}"

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return True

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "info"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Additional Information"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-info-square"

    @property
    def item_id(self) -> str:
        """Item ID."""
        return self._item_id

    @property
    def item_type(self) -> str:
        """Item type."""
        return ResourceTypeLabel[self._item_type.name].value

    @property
    def item_type_icon(self) -> str:
        """Item type icon."""
        return ResourceTypeIcon[self._item_type.name].value

    @property
    def series_name(self) -> str | None:
        """Descriptive series name if set."""
        return self._series.name

    @property
    def sheet_number(self) -> str | None:
        """Descriptive series sheet number if set."""
        return self._series.page

    @property
    def scale(self) -> str | None:
        """Formatted scale if set."""
        return self._format_scale(self._scale)

    @property
    def projection(self) -> Link | None:
        """Projection if set, formatted with more practical href."""
        if self._projection is None:
            return None

        code = self._projection.identifier.split(":")[-1]
        href = f"https://spatialreference.org/ref/epsg/{code}/"
        return Link(value=self._projection.identifier, href=href, external=True)

    @property
    def page_size(self) -> str | None:
        """
        Page size / physical dimensions.

        From supplementary information key-values, if set.
        """
        mapping = {
            "210_297": "A4 Portrait",
            "297_210": "A4 Landscape",
            "420_594": "A3 Portrait",
            "594_420": "A3 Landscape",
        }

        width = self._kv.get("physical_size_width_mm", None)
        height = self._kv.get("physical_size_height_mm", None)
        if width and height:
            key = f"{width}_{height}"
            value = f"{width} x {height} mm (width x height)"
            return mapping[f"{width}_{height}"] if key in mapping else value
        return None

    @property
    def doi(self) -> list[Link]:
        """DOI identifiers if set."""
        return self._identifiers.doi

    @property
    def isbn(self) -> list[str]:
        """ISBN identifiers if set."""
        return self._identifiers.isbn

    @property
    def gitlab_issues(self) -> list[str]:
        """GitLab issue references if set."""
        return self._identifiers.gitlab_issues

    @property
    def dates(self) -> dict[str, FormattedDate]:
        """Dates."""
        return self._dates.as_dict_labeled()

    @property
    def status(self) -> str | None:
        """Maintenance status (progress) if set."""
        if self._maintenance is None:
            return None
        return self._maintenance.status

    @property
    def frequency(self) -> str | None:
        """Maintenance frequency (update frequency) if set."""
        if self._maintenance is None:
            return None
        return self._maintenance.frequency

    @property
    def datestamp(self) -> FormattedDate:
        """Metadata datestamp."""
        return FormattedDate.from_rec_date(Date(date=self._datestamp))

    @property
    def standard(self) -> str | None:
        """Metadata standard if set."""
        if self._standard is None:
            return None
        return self._standard.name

    @property
    def standard_version(self) -> str | None:
        """Metadata standard version if set."""
        if self._standard is None:
            return None
        return self._standard.version

    @property
    def profiles(self) -> list[Link]:
        """Metadata profiles if set."""
        return [
            Link(value=profile.specification.title, href=profile.specification.href, external=True)
            for profile in self._profiles
        ]

    @property
    def record_link_xml(self) -> Link:
        """Record link (raw XML)."""
        record = self.item_id
        return Link(value="View record as ISO 19115 XML", href=f"/records/{record}.xml")

    @property
    def record_link_html(self) -> Link:
        """Record link (XML HTML)."""
        record = self.item_id
        return Link(value="View record as ISO 19115 HTML", href=f"/records/{record}.html")

    @property
    def record_link_json(self) -> Link:
        """Record JSON (BAS ISO)."""
        record = self.item_id
        return Link(value="View record as ISO 19115 JSON (BAS schema)", href=f"/records/{record}.json")

    @property
    def record_links(self) -> list[Link]:
        """Record links."""
        return [self.record_link_xml, self.record_link_html, self.record_link_json]


class InvalidItemContactError(Exception):
    """Raised when the contact for the Item Contact tab is unsuitable."""

    pass


class ContactTab(Tab):
    """Content tab."""

    def __init__(self, contact: Contact, item_id: str, item_title: str, form_action: str) -> None:
        self._contact = contact
        self._id = item_id
        self._title = item_title
        self._form_action, self._form_required_params = self._parse_form_action(form_action)

    @staticmethod
    def _parse_form_action(form_action: str) -> tuple[str, dict[str, str]]:
        """
        Parse form action into base URL and required parameters.

        The item contact form uses Power Automate which uses an endpoint with required query parameters. When submitted
        the form fields are appended to the URL as query parameters, replacing Power Automates.

        To work around this, required parameters are converted to form parameters (as hidden inputs), which will then
        be included as query parameters when the form is submitted.
        """
        parsed_url = urlparse(form_action)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        query_params = parse_qs(parsed_url.query)
        # parse_qs returns dict[str, list[str]] so convert to single values
        params = {k: v[0] for k, v in query_params.items()}

        return base_url, params

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        return True

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "contact"

    @property
    def title(self) -> str:
        """Tab title."""
        return "Contact"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "far fa-comment-alt-lines"

    @property
    def form_action(self) -> str:
        """Contact form action URL."""
        return self._form_action

    @property
    def form_params(self) -> dict[str, str]:
        """Contact form required parameters."""
        return {"item-id": self._id, "item-poc": self._contact.email, **self._form_required_params}

    @property
    def subject_default(self) -> str:
        """Item title."""
        return f"Message about '{self._title}'"

    @property
    def team(self) -> str:
        """Team."""
        if self._contact.organisation is None:
            msg = "Item contact must have an organisation."
            raise InvalidItemContactError(msg)

        return self._contact.organisation.name

    @property
    def email(self) -> str:
        """Email."""
        if self._contact.email is None:
            msg = "Item contact must have an email."
            raise InvalidItemContactError(msg)

        return self._contact.email

    @property
    def phone(self) -> str | None:
        """Phone number."""
        return self._contact.phone

    @property
    def address(self) -> str | None:
        """Address."""
        if self._contact.address is None:
            return None

        address = self._contact.address
        parts = [
            *address.delivery_point.split(", "),
            address.city,
            address.administrative_area,
            address.postal_code,
            address.country,
        ]
        return "<br/>".join([part for part in parts if part is not None])
