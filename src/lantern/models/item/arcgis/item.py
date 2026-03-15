from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from jinja2 import TemplateNotFound
from lxml.etree import Element, SubElement
from lxml.etree import tostring as etree_tostring

from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.dataclasses import ItemProperties as ArcGisItemProperties
from lantern.lib.arcgis.gis.enums import ItemType as ArcGisItemType
from lantern.lib.arcgis.gis.enums import SharingLevel as ArcGisSharingLevel
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.base.item import ItemBase
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.record import Record
from lantern.utils import get_jinja_env


class ArcGisItemLicenceHrefUnsupportedError(Exception):
    """Raised when the licence href value is not mapped to a licence template."""

    pass


class ItemArcGis(ItemBase):
    """
    ArcGIS representation of a resource within the BAS Data Catalogue / Metadata ecosystem.

    Maps a catalogue / ISO 19115 resource to the information model used by ArcGIS items [1] (e.g. summary -> snippet).
    Some properties that are not present as distinct elements in the ArcGIS model are combined via Jinja templates
    (e.g. abstract, lineage, citation are mapped to the description). Some properties are not supported, or cannot be
    known, in the Catalogue/ISO model and use either fixed values or supplementary values (e.g. the ArcGIS item ID
    isn't held in the ISO 19115 model as it's not equivalent to the file_identifier or identification.identifier).

    Typically, there is a one-to-many relationship between Catalogue and ArcGIS items, where ArcGIS items represent
    some or all of the distribution options for a Catalogue item. (E.g. a vector dataset with a feature and vector
    tile layer will have a single Catalogue item for the dataset and separate ArcGIS items for each layer).

    Note: The terms such as 'item' are used in both the BAS Data Catalogue / Metadata ecosystem and ArcGIS. For clarity
    when importing classes from both platforms, it's recommended to alias this class as `CatItemArcGIS` or similar and
    the ArcGIS item class as `ArcGisItem` or similar.

    [1] https://developers.arcgis.com/documentation/glossary/item/
    """

    def __init__(
        self, record: Record, arcgis_item: ArcGisItem, admin_meta_keys: AdministrationKeys | None = None
    ) -> None:
        self._arcgis_item = arcgis_item
        self._validate_record(record)
        super().__init__(record=record, admin_keys=admin_meta_keys)

        self._jinja = get_jinja_env()

    @staticmethod
    def _render_arcgis_metadata(file_identifier: str) -> str:
        """
        Generate minimal metadata using the ArcGIS metadata storage format.

        See https://doc.arcgis.com/en/arcgis-online/manage-data/metadata.htm#ESRI_SECTION1_A1309B89E2FA42A89DE1ADA1249CA6D8
        for general information about this format.

        Used to store the ISO file identifier only, to allow ArcGIS items to be unambiguously related to an ISO
        resource.

        The wider ISO record is not included to avoid:
        - information getting out of sync
        - encoding differences between the BAS Metadata Library and ArcGIS (e.g. gmx:Anchor elements)

        This minimal use is not considered valid by ArcGIS, and so cannot (and must not) be edited through AGOL or
        ArcPro to avoid losing the ArcGIS - ISO association.
        """
        root = Element("metadata")
        md_file_id_e = SubElement(root, "mdFileID")
        md_file_id_e.text = file_identifier
        SubElement(root, "dataIdInfo")  # empty element added by ArcGIS needed for comparison
        return etree_tostring(root, encoding="unicode")

    @staticmethod
    def _validate_record(record: Record) -> None:
        """Check record for ArcGIS specific constraints."""
        if record.identification.purpose is not None and len(record.identification.purpose) >= 250:
            msg = "ArcGIS snippet (summary/purpose) is limited to 250 characters."
            raise ValueError(msg) from None

    @property
    def _title(self) -> str:
        """
        Item title.

        Mapped from: base item title (without formatting)
        Mapped to: title (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return self.title_plain  # pragma: no cover (see `.item_properties()`)

    @property
    def _snippet(self) -> str | None:
        """
        Item snippet (summary).

        Mapped from: base item summary (without formatting)
        Mapped to: snippet (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return self.summary_plain

    @property
    def _description(self) -> str:
        """
        Item description rendered from a template.

        Mapped from:
            - base item description (abstract) (with HTML encoding)
            - base item lineage (with HTML encoding) if present
            - base item citation (with HTML encoding) if present
            - base item data catalogue identifier

        Mapped to: description (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        parts = {"abstract": self.description_html}
        if self.lineage_html is not None:
            parts["lineage"] = self.lineage_html
        if self.citation_html is not None:
            parts["citation"] = self.citation_html
        parts["catalogue_href"] = self.identifiers.filter(namespace=CATALOGUE_NAMESPACE)[0].href

        return self._jinja.get_template("_arcgis/description.html.j2").render(**parts)

    @property
    def _attribution(self) -> str:
        """
        Item attribution (credit).

        Always "BAS".

        Mapped to: accessInformation (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return "BAS"

    @property
    def _terms_of_use(self) -> str | None:
        """
        Item terms of use rendered from a template.

        Mapped from: base item licence type if present
        Mapped to: licenseInfo (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        if self.licence is None or self.licence_enum is None:
            return None

        try:
            template_name = f"_arcgis/licences/{self.licence_enum.name.lower()}.html.j2"
            return self._jinja.get_template(template_name).render()
        except TemplateNotFound as e:
            msg = f"Unknown licence href: '{getattr(self.licence, 'href', '')}'."
            raise ArcGisItemLicenceHrefUnsupportedError(msg) from e

    @property
    def item_id(self) -> str:
        """
        Item ID assigned by ArcGIS.

        Can uniquely identify an item within the ArcGIS platform, and distinguish representations of a resource.

        Value not held in the ISO model.

        Mapped to: id (from [1])
        [1] https://developers.arcgis.com/documentation/glossary/item-id/
        """
        return self._arcgis_item.id

    @property
    def item_type(self) -> ArcGisItemType:
        """
        Item type/resource within ArcGIS.

        Can typically distinguish different representations of a resource within the ArcGIS platform.

        E.g.:
        - a vector dataset may be represented as a GeoJSON, feature layer and vector tile layer item.
        - a product may be represented as a PDF, JPEG and web map item.

        Valid values defined by [1] and `arcgis.gis.ItemTypeEnum` enum.

        Value not held in the ISO model.

        Mapped to: type (from [2])

        [1] https://developers.arcgis.com/rest/users-groups-and-items/items-and-item-types/
        [2] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        return self._arcgis_item.properties.item_type

    @property
    def sharing_level(self) -> ArcGisSharingLevel:
        """ArcGIS sharing level based on item access level."""
        access_level = super().admin_resource_access
        if access_level == AccessLevel.PUBLIC:
            return ArcGisSharingLevel.EVERYONE
        if access_level == AccessLevel.BAS_STAFF:
            return ArcGisSharingLevel.ORG

        # fail-safe
        return ArcGisSharingLevel.PRIVATE

    @property
    def _metadata(self) -> str:
        """
        ArcGIS item metadata.

        Encoded using the ArcGIS metadata storage format.
        """
        return self._render_arcgis_metadata(self.resource_id)

    @property
    def thumbnail_href(self) -> str | None:
        """
        URL to optional item thumbnail.

        Uses 'overview-agol' graphic label if available. This graphic must be hosted somewhere accessible to the
        ArcGIS instance (Online or Enterprise). It should be sized as per Esri's recommendations.
        """
        try:
            return self.graphics.filter(identifier="overview-agol")[0].href
        except IndexError:
            return None

    @property
    def item_properties(self) -> ArcGisItemProperties:
        """Combined ArcGIS item properties."""
        props = ArcGisItemProperties(
            title=self._title,
            item_type=self.item_type,
            description=self._description,
            access_information=self._attribution,
            license_info=self._terms_of_use,
            metadata=self._metadata,
        )
        if self._snippet is not None:
            props.snippet = self._snippet
        return props

    @property
    def item(self) -> ArcGisItem:
        """Combined ArcGIS item."""
        return ArcGisItem(
            id=self.item_id,
            owner=self._arcgis_item.owner,
            org_id=self._arcgis_item.org_id,
            url=self._arcgis_item.url,
            properties=self.item_properties,
            sharing_level=self.sharing_level,
        )
