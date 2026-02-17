import json
import locale
from abc import ABC, abstractmethod
from datetime import date, datetime

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission

from lantern.lib.metadata_library.models.record.elements.common import Constraint, Date, Identifier, Series
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution as RecordDistribution
from lantern.lib.metadata_library.models.record.elements.metadata import MetadataStandard
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from lantern.models.item.base.elements import Contact, Link
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.enums import AccessLevel, ResourceTypeLabel
from lantern.models.item.catalogue.distributions import (
    ArcGisFeatureLayer,
    ArcGisOgcApiFeatures,
    ArcGisRasterTileLayer,
    ArcGisVectorTileLayer,
    BasPublishedMap,
    BasSan,
    Csv,
    Distribution,
    Fpl,
    GeoJson,
    GeoPackage,
    Gpx,
    Jpeg,
    MapboxVectorTiles,
    Pdf,
    Png,
    Shapefile,
)
from lantern.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    FormattedDate,
    Identifiers,
    ItemCatalogueSummary,
    Maintenance,
)
from lantern.models.item.catalogue.enums import ItemSuperType, Licence, ResourceTypeIcon


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
        return "fa-regular fa-grid-2"

    @property
    def items(self) -> list[ItemCatalogueSummary]:
        """Items that form the current item."""
        return self._items


class DataTab(Tab):
    """Data tab."""

    def __init__(self, restricted: bool, distributions: list[RecordDistribution]) -> None:
        self._restricted = restricted
        self._resource_distributions = distributions
        self._supported_distributions = [
            ArcGisFeatureLayer,
            ArcGisOgcApiFeatures,
            ArcGisRasterTileLayer,
            ArcGisVectorTileLayer,
            BasPublishedMap,
            BasSan,
            Csv,
            Fpl,
            GeoPackage,
            GeoJson,
            Gpx,
            Jpeg,
            MapboxVectorTiles,
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
                            option=dist_option,
                            other_options=self._resource_distributions,
                            restricted=self._restricted,
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
        return "fa-regular fa-cube"

    @property
    def restricted(self) -> bool:
        """Access restrictions for item."""
        return self._restricted

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
        return "fa-regular fa-expand"


class AuthorsTab(Tab):
    """Authors tab."""

    def __init__(self, item_super_type: ItemSuperType, authors: list[Contact]) -> None:
        self._item_super_type = item_super_type
        self._authors = authors

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_super_type == ItemSuperType.CONTAINER:
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
        return "fa-regular fa-user-group-simple"

    @property
    def items(self) -> list[Contact]:
        """Authors."""
        return self._authors


class LicenceTab(Tab):
    """Licence tab."""

    def __init__(
        self,
        item_super_type: ItemSuperType,
        licence: Constraint | None,
        rights_holders: list[Contact] | None = None,
    ) -> None:
        self._item_super_type = item_super_type
        self._licence = licence
        self._copyright_holders = rights_holders if rights_holders is not None else []

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_super_type == ItemSuperType.CONTAINER:
            return False
        return self.slug is not None

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
        return "fa-regular fa-file-certificate"

    @property
    def slug(self) -> Licence | None:
        """
        Licence reference.

        Returns a licence enum value or None if not defined or recognised.

        Defensive check as records are not limited to licences supported by catalogue items and so should not fail if
        an unknown value is used. If records should be limited, a check should be added in `Record.validate()` instead.
        """
        if not (self._licence and self._licence.href):
            return None
        try:
            return Licence(self._licence.href)
        except ValueError:
            return None

    @property
    def copyright_holders(self) -> list[Link | str]:
        """
        Copyright/rights holders.

        Supports both individuals and organisations, with an optional link to a website.
        """
        holders = []
        for contact in self._copyright_holders:
            name = contact.organisation.name if contact.organisation else contact.individual.name  # ty: ignore[possibly-missing-attribute]
            if not contact.online_resource:
                holders.append(name)
                continue
            holders.append(Link(value=name, href=contact.online_resource.href, external=True))
        return holders


class LineageTab(Tab):
    """Lineage tab."""

    def __init__(self, item_super_type: ItemSuperType, statement: str | None) -> None:
        self._item_super_type = item_super_type
        self._statement = statement

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled."""
        if self._item_super_type == ItemSuperType.CONTAINER:
            return False
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
        return "fa-regular fa-scroll"

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
            # if all aggregations are a container's items, disable tab as these are shown in item tab
            return len(self.child_items) != all_agg  # ty: ignore[invalid-argument-type]
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
        return "fa-regular fa-diagram-project"


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
        build_time: datetime,
        series: Series | None = None,
        scale: int | None = None,
        projection: Identifier | None = None,
        maintenance: Maintenance | None = None,
        standard: MetadataStandard | None = None,
        profiles: list[DomainConsistency] | None = None,
        metadata_licence: Constraint | None = None,
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
        self._metadata_licence = metadata_licence
        self._kv = kv
        self._build_time = build_time

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
        return "fa-regular fa-square-info"

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
        return self._series.name if self._series is not None else None

    @property
    def sheet_number(self) -> str | None:
        """Descriptive series sheet number if set."""
        return self._series.page if self._series is not None else None

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
    def aliases(self) -> list[Link]:
        """Catalogue alias identifiers if set."""
        return self._identifiers.aliases

    @property
    def doi(self) -> list[Link]:
        """DOI identifiers if set."""
        return self._identifiers.doi

    @property
    def isbn(self) -> list[str]:
        """ISBN identifiers if set."""
        return self._identifiers.isbn

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
            Link(
                value=profile.specification.title
                + (f" (v{profile.specification.edition})" if profile.specification.edition is not None else ""),
                href=profile.specification.href,
                external=True,
            )
            for profile in self._profiles
        ]

    @property
    def metadata_licence(self) -> Link | None:
        """
        Formatted metadata licence if set.

        Licence usage constraint must include a href.
        """
        if self._metadata_licence is None or not self._metadata_licence.href:
            return None
        value = self._metadata_licence.href
        if self._metadata_licence.href == "https://creativecommons.org/licenses/by-nd/4.0/":
            value = "Creative Commons Attribution-NoDerivatives 4.0 International"
        return Link(value=value, href=self._metadata_licence.href, external=True)

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

    @property
    def build_time(self) -> FormattedDate:
        """Build time of the item."""
        return FormattedDate(
            value=self._build_time.strftime("%d %B %Y %H:%M:%S %Z"), datetime=self._build_time.isoformat()
        )


class InvalidItemContactError(Exception):
    """Raised when the contact for the Item Contact tab is unsuitable."""

    pass


class ContactTab(Tab):
    """Content tab."""

    def __init__(self, contact: Contact, item_id: str, item_title: str, form_action: str, turnstile_key: str) -> None:
        self._contact = contact
        self._id = item_id
        self._title = item_title
        self._form_action = form_action
        self._turnstile_key = turnstile_key

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
        return "fa-regular fa-comment-captions"

    @property
    def form_action(self) -> str:
        """Contact form action URL."""
        return self._form_action

    @property
    def form_params(self) -> dict[str, str | None]:
        """Contact form required parameters."""
        return {"item-id": self._id, "item-poc": self._contact.email}

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
            address.city,
            address.administrative_area,
            address.postal_code,
            address.country,
        ]
        if isinstance(address.delivery_point, str):
            delivery_parts = [part.strip() for part in address.delivery_point.split(",")]
            parts = delivery_parts + parts
        return "<br/>".join([part for part in parts if part is not None])

    @property
    def turnstile_site_key(self) -> str:
        """Cloudflare Turnstile widget site key."""
        return self._turnstile_key


class AdminTab(Tab):
    """Admin tab."""

    def __init__(
        self,
        trusted: bool,
        item_id: str,
        revision: Link,
        gitlab_issues: list[str],
        restricted: bool,
        metadata_access: AccessLevel,
        resource_access: AccessLevel,
        admin_meta: AdministrationMetadata | None,
    ) -> None:
        self._trusted = trusted
        self._item_id = item_id
        self._revision = revision
        self._gitlab_issues = gitlab_issues
        self._restricted = restricted
        self._metadata_access = metadata_access
        self._resource_access = resource_access
        self._admin_meta = admin_meta

    @staticmethod
    def _make_gitlab_issue_ref(href: str) -> str:
        """
        Create GitLab issue reference.

        E.g. https://gitlab.data.bas.ac.uk/MAGIC/foo/-/issues/123 -> MAGIC/foo#123                                                                                                                                                                              .
        """
        return f"{href.split('/')[-5]}/{href.split('/')[-4]}#{href.split('/')[-1]}"

    @staticmethod
    def _dump_permissions(permissions: list[Permission]) -> list[str]:
        return [
            json.dumps(
                {
                    "directory": permission.directory,
                    "group": permission.group,
                    "expiry": permission.expiry.isoformat(),
                    "comment": permission.comment,
                },
                indent=2,
                ensure_ascii=False,
            )
            for permission in permissions
        ]

    @property
    def enabled(self) -> bool:
        """Whether tab is enabled based on whether export destination is trusted."""
        return self._trusted

    @property
    def anchor(self) -> str:
        """HTML anchor for tab."""
        return "admin"

    @property
    def title(self) -> str:
        """Tab title."""
        return "ADMIN"

    @property
    def icon(self) -> str:
        """Tab icon class."""
        return "fa-regular fa-shield-halved"

    @property
    def item_id(self) -> str:
        """Item ID."""
        return self._item_id

    @property
    def revision_link(self) -> Link | None:
        """Link to record revision if known."""
        return self._revision

    @property
    def gitlab_issues(self) -> list[Link]:
        """GitLab issue references if set."""
        return [
            Link(value=self._make_gitlab_issue_ref(issue), href=issue, external=True) for issue in self._gitlab_issues
        ]

    @property
    def restricted(self) -> bool:
        """Catalogue item access."""
        return self._restricted

    @property
    def metadata_access(self) -> str:
        """Base item metadata access level."""
        return self._metadata_access.name

    @property
    def metadata_permissions(self) -> list[str]:
        """
        Metadata access permissions if set.

        Temporary encoding.
        """
        if self._admin_meta is None:
            return []
        return self._dump_permissions(self._admin_meta.metadata_permissions)

    @property
    def resource_access(self) -> str:
        """Base item resource access level."""
        return self._resource_access.name

    @property
    def resource_permissions(self) -> list[str]:
        """
        Resource access permissions if set.

        Temporary encoding.
        """
        if self._admin_meta is None:
            return []
        return self._dump_permissions(self._admin_meta.resource_permissions)
