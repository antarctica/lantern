from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from jinja2 import TemplateNotFound
from lxml import html as lxml_html
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
    Representation of a resource within the Esri ArcGIS geospatial platform.

    Maps a catalogue / ISO 19115 resource to the information model used by ArcGIS items [1] (e.g. summary -> snippet).
    Some properties that are not present as distinct elements in the ArcGIS model are combined via Jinja templates
    (e.g. abstract, lineage, citation are mapped to the description).

    Some properties are not supported, or cannot be known, in the Catalogue/ISO model and use either fixed values or
    supplementary values (e.g. the ArcGIS item ID isn't held in the ISO 19115 model as it's not equivalent to the file_
    identifier or identification.identifier).

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
    def _arc_html(string: str, item_href: str | None) -> str:
        """
        Postprocess HTML content to fit ArcGIS Portal constraints.

        Intended for abstracts, lineage, and other long-form free-text properties.

        Processes:
        - headings
        - fragment links
        - admonitions

        For headings:
        - the description template hard-codes section headings (for abstract, lineage, etc.) as H4s
        - to avoid headings within sections appearing larger than their section header, all headings are reduced to H5.

        For fragment links:
        - links may use fragments to item tabs, which won't resolve outside item pages
        - link href's are rewritten as fully qualified URLs to work correctly
        - requires a fully qualified URL

        For admonitions
        - the admonition Markdown extension will only match valid options (note, caution, etc.)
        - this means we don't need to check for invalid options, as they won't match the xpath query
        - similarly, instances will always include a title, as a default per option is used if a custom value isn't set

        E.g.:

        ```
        <div>
            <h3>Some heading</h3>
        </div>
        ```

        Becomes:

        ```
        <div>
            <h5>Some heading</h5>
        </div>
        ```

        E.g.:

        ```
        <div>
            <a href="#tab-foo>Some link</a>
        </div>
        ```

        Becomes:

        ```
        <div>
            <a href="https://data.bas.ac.uk/items/123/#tab-foo>Some link</a>
        </div>
        ```

        E.g.:

        ```
        <div class="admonition note">
            <p class="admonition-title">Note</p>
            <p>Some text shown as a note.</p>
        </div>
        ```

        Becomes:

        ```
        <div style="border-left-style:solid;...border-color:rgb(55, 146, 69);">
            <p><strong>Note</strong></p>
            <p>Some text shown as a note.</p>
        </div>
        ```
        """
        _admonition_colours = {
            "note": "rgb(43, 140, 196)",
            "tip": "rgb(55, 146, 69)",
            "important": "rgb(111, 114, 175)",
            "warning": "rgb(255, 191, 71)",
            "caution": "rgb(177, 14, 30)",
        }
        _admonition_base_styles = [
            "border-bottom-style:none;",
            "border-left-style:solid;",
            "border-left-width:5px;",
            "border-radius:0;",
            "border-right-style:none;",
            "border-top-style:none;",
            "margin-bottom:20px;",
            "padding:2px 10px;",
        ]

        html_content = string
        root = lxml_html.fromstring(html_content)

        # headings
        for heading in root.xpath(".//h1 | .//h2 | .//h3 | .//h4"):
            heading.tag = "h5"

        # fragment links
        if item_href:
            for link in root.xpath('.//a[@href and starts-with(@href, "#")]'):
                fragment = link.get("href")
                link.set("href", f"{item_href}{fragment}")

        # admonitions
        for div in root.xpath('.//div[@class and contains(@class, "admonition")]'):
            class_attr = div.get("class", "")
            classes = class_attr.split()

            # get admonition type (e.g., "admonition note" -> "note")
            # as only valid types are processed as admonitions upstream, and only admonitions are looped in the
            # xpath, this will always match a value
            admonition_type: str = ""
            for cls in classes:  # pragma: no branch
                if cls in _admonition_colours:
                    admonition_type = cls
                    break

            colour = _admonition_colours[admonition_type]
            inline_style = "".join([*_admonition_base_styles, f"border-color:{colour};"])

            # replace class attribute with style attribute
            div.set("style", inline_style)
            div.attrib.pop("class", None)

            # Transform admonition title
            title_p = div.find('.//p[@class="admonition-title"]')
            title_text = title_p.text or ""
            # replace element with strong tag
            title_p.getparent().remove(title_p)
            new_p = Element("p")
            strong = SubElement(new_p, "strong")
            strong.text = title_text
            div.insert(0, new_p)

        return lxml_html.tostring(root, encoding="unicode", method="html")

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

        Built from:
        - base item description (abstract) (with HTML encoding and Arc specific processing)
        - base item lineage (with HTML encoding and Arc specific processing) if present
        - base item citation (with HTML encoding) if present
        - base item data catalogue identifier

        Mapped to: description (from [1])
        [1] https://developers.arcgis.com/rest/users-groups-and-items/common-parameters/#item-parameters
        """
        item_href = None
        cat_identifiers = self.identifiers.filter(namespace=CATALOGUE_NAMESPACE)
        if len(cat_identifiers) > 0 and cat_identifiers[0].href:
            item_href = cat_identifiers[0].href
        parts = {
            "abstract": self._arc_html(string=self.description_html, item_href=item_href),
            "catalogue_href": item_href,
        }
        if self.lineage_html is not None:
            parts["lineage"] = self._arc_html(string=self.lineage_html, item_href=item_href)
        if self.citation_html is not None:
            parts["citation"] = self.citation_html

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
    def _thumbnail_href(self) -> str | None:
        """
        URL to optional item thumbnail.

        Uses 'overview-agol' graphic label if available.

        This graphic MUST:
        - be hosted somewhere accessible to the ArcGIS Portal instance (Online or Enterprise)
        - It MUST include a `sha1` query parameters for the image contents

        E.g.: https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/75a43e71-f69e-4c7e-91c2-9f0b10dc4ee5/overview-agol.jpg?sha1=74abaf53f83b771ceeafdb19ff6c4bcc8ef6e2ae

        This graphic SHOULD:
        - use Esri's recommended 600x400 size

        Without the SHA1 value, item comparisons will fail in the `esri-item` dev task.
        """
        try:
            return self.graphics.filter(identifier="overview-agol")[0].href
        except IndexError:
            return None

    @property
    def item_properties(self) -> ArcGisItemProperties:
        """
        Combined ArcGIS item properties.

        Where a ArcGIS thumbnail is set, the thumbnail property is set to a fake static value ('x').
        """
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
        if self._thumbnail_href:
            props.thumbnail = "x"
            props.thumbnail_url = self._thumbnail_href
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
