import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from lantern.lib.arcgis.gis.enums import ItemType, MetadataFormat, SharingLevel


@dataclass
class ItemProperties:
    """
    Item parameters corresponding to properties of an item that are available to update using the
    :meth:`~arcgis.gis.ContentManager.add` and :meth:`~arcgis.gis.Item.update` operations.

    Original import: `arcgis.gis._impl._dataclasses._contentds.ItemProperties`

    Modifications:
    - ItemTypeEnum replaced with vendored lantern.lib.arcgis.gis.enums.ItemType
    - MetadataFormatEnum replaced with vendored lantern.lib.arcgis.gis.enums.MetadataFormat
    - datetime import changed
    -`Return types added to `__str__`, `__repr__` and `__iter__` methods
    - `__iter__` body changed to Ruff recommended pattern
    - `arcgis.gis._impl._dataclasses._contentds._parse_enum` method refactored into class
    - `__post_init__` and `to_dict` methods refactored to remove duplication
    - `fromitem` method dropped as not applicable
    - 'str' removed as a type for 'item_type'
    - None removed as a type for 'metadata'
    """  # noqa: D205

    title: str
    item_type: ItemType
    metadata: str
    tags: list[str] | str | None = None
    thumbnail: str | None = None
    thumbnail_url: str | None = None
    metadata_editable: bool | None = None
    metadata_formats: MetadataFormat | str | None = MetadataFormat.ISO19139
    type_keywords: list[str] | None = None
    description: str | None = None
    snippet: str | None = None
    extent: str | list | None = None
    spatial_reference: str | None = None
    access_information: str | None = None
    license_info: str | None = None
    culture: str | None = None
    properties: dict | str | None = None
    app_categories: list[str] | None = None
    industries: list[str] | None = None
    listing_properties: dict | None = None
    service_username: str | None = None
    service_password: str | None = None
    service_proxy: dict | None = None
    categories: list[str] | None = None
    text: dict | str | None = None
    extension: str | None = None
    overwrite: bool | None = None  # Support for this parameter will be removed in 2.4.3+.
    file_name: str | None = None
    classification: dict | None = None
    api_token1_expiration: datetime | None = None
    api_token2_expiration: datetime | None = None
    is_personal_api_token: bool | None = None
    subscription_type: str | None = None
    _dict_data: dict | None = field(init=False)

    def __str__(self) -> str:
        """Str representation."""
        return f"<ItemProperties: title={self.title}, type={self.item_type}>"

    def __repr__(self) -> str:
        """Class representation."""
        return self.__str__()

    def __iter__(self) -> Iterator:
        """Iterator."""
        yield from self.to_dict().items()

    @staticmethod
    def _parse_enum(value: Enum | Any | None) -> Any | None:  # noqa: ANN401
        """Returns the Enum's value or the current value."""
        if isinstance(value, Enum):
            return value.value
        return value

    def __post_init__(self) -> None:
        """Post initialisation."""
        self._dict_data = self.to_dict()

    def to_dict(self) -> dict:
        """Dump as plain dict and align with ArcGIS item JSON."""
        data = {
            "title": self.title,
            "type": self._parse_enum(self.item_type),
            "tags": (",".join(self.tags or []) if isinstance(self.tags, list) else self.tags),
            "thumbnail": self.thumbnail,
            "thumbnailurl": self.thumbnail_url,
            "metadata": self.metadata,
            "metadataEditable": self.metadata_editable,
            "metadataFormats": self._parse_enum(self.metadata_formats),
            "typeKeywords": ",".join(self.type_keywords or []),
            "description": self.description or "",
            "snippet": self.snippet,
            "extent": self.extent,
            "spatialReference": self.spatial_reference or "",
            "accessInformation": self.access_information,
            "licenseInfo": self.license_info,
            "culture": self.culture,
            "appCategories": ",".join(self.app_categories or []),
            "industries": ",".join(self.industries or []),
            "listingProperties": self.listing_properties,
            "serviceUsername": self.service_username,
            "servicePassword": self.service_password,
            "serviceProxyFilter": self.service_proxy,
            "categories": self.categories or [],
            "text": self.text or None,
            "extension": self.extension or None,
            "overwrite": self.overwrite or None,
            "fileName": self.file_name or None,
            "classification": self.classification or None,
        }

        if isinstance(self.properties, dict):
            data["properties"] = json.dumps(self.properties)
        elif isinstance(self.properties, str):
            data["properties"] = self.properties
        else:
            data["properties"] = None
        if isinstance(self.api_token1_expiration, datetime):
            data["apiToken1ExpirationDate"] = int(self.api_token1_expiration.timestamp() * 1000)
        if isinstance(self.api_token2_expiration, datetime):
            data["apiToken2ExpirationDate"] = int(self.api_token2_expiration.timestamp() * 1000)
        if isinstance(self.is_personal_api_token, bool):
            data["isPersonalAPIToken"] = self.is_personal_api_token
        if isinstance(self.subscription_type, str):
            data["subscriptionType"] = self.subscription_type

        return data


@dataclass
class Item:
    """
    A unit of ArcGIS content.

    Original import: `arcgis.gis.Item`

    This is a simplified and partial version of the original import but which represents the same concept.
    See docs/libraries.md#arcgis-item-json-properties for (un)supported item properties.
    """

    id: str
    owner: str
    org_id: str
    url: str
    properties: ItemProperties
    sharing_level: SharingLevel
    raw_item: dict | None = None

    def __str__(self) -> str:
        """Str representation."""
        return f"<Item: id={self.id}, owner={self.owner}>"

    def __repr__(self) -> str:
        """Class representation."""
        return self.__str__()

    def __eq__(self, o: object) -> bool:
        """Equality check ignoring raw_item."""
        if not isinstance(o, Item):
            return NotImplemented
        self_attrs = {k: v for k, v in vars(self).items() if k != "raw_item"}
        other_attrs = {k: v for k, v in vars(o).items() if k != "raw_item"}
        return self_attrs == other_attrs

    @classmethod
    def from_item_json(cls, data: dict, metadata: str) -> "Item":
        """Create instance from JSON data returned by `.../content/items/{item_id}` API endpoint."""
        try:
            sharing_level = SharingLevel[data["access"].upper()]
        except KeyError as e:
            if data["access"] != "public":
                raise e from e
            sharing_level = SharingLevel.EVERYONE
        item_props = ItemProperties(
            title=data["title"],
            item_type=ItemType(data["type"]),
            metadata=metadata,
            snippet=data.get("snippet"),
            description=data.get("description"),
            access_information=data.get("accessInformation"),
            license_info=data.get("licenseInfo"),
        )
        return Item(
            id=data["id"],
            owner=data["owner"],
            org_id=data["orgId"],
            url=data["url"],
            properties=item_props,
            sharing_level=sharing_level,
            raw_item=data,
        )
