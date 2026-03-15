from datetime import UTC, datetime
from typing import Final

import pytest

from lantern.lib.arcgis.gis.dataclasses import Item, ItemProperties
from lantern.lib.arcgis.gis.enums import ItemType, MetadataFormat, SharingLevel
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestItemProperties:
    """
    Test ArcGIS item properties.

    This class is not comprehensively tested in terms of all properties, including datetime handling.
    """

    def test_init(self):
        """Can create a minimal item properties instance from directly assigned properties."""
        value = "x"
        type_ = ItemType.FEATURE_SERVICE

        props = ItemProperties(title=value, item_type=type_, metadata=value)

        assert isinstance(props, ItemProperties)
        assert props.title == value
        assert props.item_type == type_
        assert props.metadata == value
        assert isinstance(props._dict_data, dict)

        assert props.tags is None
        assert props.thumbnail is None
        assert props.thumbnail_url is None
        assert props.metadata_editable is None
        assert props.metadata_formats == MetadataFormat.ISO19139
        assert props.type_keywords is None
        assert props.description is None
        assert props.snippet is None
        assert props.extent is None
        assert props.spatial_reference is None
        assert props.access_information is None
        assert props.license_info is None
        assert props.culture is None
        assert props.properties is None
        assert props.app_categories is None
        assert props.industries is None
        assert props.listing_properties is None
        assert props.service_username is None
        assert props.service_password is None
        assert props.service_proxy is None
        assert props.categories is None
        assert props.text is None
        assert props.extension is None
        assert props.overwrite is None
        assert props.file_name is None
        assert props.classification is None
        assert props.api_token1_expiration is None
        assert props.api_token2_expiration is None
        assert props.is_personal_api_token is None
        assert props.subscription_type is None

    @pytest.mark.cov()
    def test_str_repr(self, fx_lib_arcgis_item_properties: ItemProperties):
        """Can get string and class representation."""
        props = fx_lib_arcgis_item_properties
        expected = f"<ItemProperties: title={props.title}, type={props.item_type}>"
        assert str(props) == expected
        assert repr(props) == expected

    @pytest.mark.cov()
    def test_iter(self, fx_lib_arcgis_item_properties: ItemProperties):
        """Can iterate over properties as dict items."""
        for k, v in fx_lib_arcgis_item_properties:
            assert k is not None
            assert v is not None
            break

    @pytest.mark.cov()
    def test_eq(self):
        """Can compare item properties instances."""
        a = ItemProperties(title="x", item_type=ItemType.FEATURE_SERVICE, metadata="x")
        b = ItemProperties(title="x", item_type=ItemType.FEATURE_SERVICE, metadata="x")
        assert a == b

    @pytest.mark.cov()
    @pytest.mark.parametrize("value", ["Feature Service", ItemType.FEATURE_SERVICE])
    def test_parse_enum(self, value: str | ItemType):
        """Can parse enum values."""
        assert ItemProperties._parse_enum(value) == ItemType.FEATURE_SERVICE.value

    test_to_dict_expected: Final[dict] = {
        "title": "x",
        "type": ItemType.FEATURE_SERVICE.value,
        "metadata": "x",
        "metadataFormats": "iso19139",
    }
    test_to_dict_dt = datetime(2014, 6, 30, tzinfo=UTC)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (ItemProperties(title="x", item_type=ItemType.FEATURE_SERVICE, metadata="x"), test_to_dict_expected),
            (
                ItemProperties(title="x", item_type=ItemType.FEATURE_SERVICE, metadata="x", properties={"x": "x"}),
                {**test_to_dict_expected, "properties": '{"x": "x"}'},
            ),
            (
                ItemProperties(title="x", item_type=ItemType.FEATURE_SERVICE, metadata="x", properties='{"x": "x"}'),
                {**test_to_dict_expected, "properties": '{"x": "x"}'},
            ),
            (
                ItemProperties(
                    title="x",
                    item_type=ItemType.FEATURE_SERVICE,
                    metadata="x",
                    api_token1_expiration=test_to_dict_dt,
                    api_token2_expiration=test_to_dict_dt,
                ),
                {
                    **test_to_dict_expected,
                    "apiToken1ExpirationDate": test_to_dict_dt.timestamp() * 1000,
                    "apiToken2ExpirationDate": test_to_dict_dt.timestamp() * 1000,
                },
            ),
            (
                ItemProperties(
                    title="x",
                    item_type=ItemType.FEATURE_SERVICE,
                    metadata="x",
                    is_personal_api_token=True,
                    subscription_type="x",
                ),
                {**test_to_dict_expected, "isPersonalAPIToken": True, "subscriptionType": "x"},
            ),
        ],
    )
    def test_to_dict(self, value: ItemProperties, expected: dict):
        """Can encode a minimal item properties instance to a dict."""
        result = clean_dict(value.to_dict(), strip_empty_str=True)
        assert result == expected


class TestItem:
    """Test ArcGIS content items."""

    test_type = ItemType.FEATURE_SERVICE
    test_sharing_level = SharingLevel.PRIVATE

    def test_init(self):
        """Can create a minimal item instance from directly assigned properties."""
        value = "x"

        item = Item(
            id=value,
            owner=value,
            org_id=value,
            url=value,
            properties=ItemProperties(
                title=value,
                item_type=self.test_type,
                metadata="x",
            ),
            sharing_level=self.test_sharing_level,
        )

        assert isinstance(item, Item)
        assert item.id == value
        assert item.owner == value
        assert item.org_id == value
        assert item.url == value
        assert isinstance(item.properties, ItemProperties)
        assert item.raw_item is None

    @pytest.mark.cov()
    def test_str_repr(self, fx_lib_arcgis_item: Item):
        """Can get string and class representation."""
        item = fx_lib_arcgis_item
        expected = f"<Item: id={item.id}, owner={item.owner}>"
        assert str(item) == expected
        assert repr(item) == expected

    @pytest.mark.cov()
    def test_eq(self):
        """Can compare item instances."""
        values = {
            "id": "x",
            "owner": "x",
            "org_id": "x",
            "url": "x",
            "properties": ItemProperties(
                title="x",
                item_type=ItemType.FEATURE_SERVICE,
                metadata="x",
            ),
            "sharing_level": SharingLevel.PRIVATE,
        }
        a = Item(**values)
        b = Item(**values)
        b.raw_item = {"x": "x"}

        assert a == b

    @pytest.mark.cov()
    def test_eq_invalid(self, fx_lib_arcgis_item: Item):
        """Cannot compare item instances with other types."""
        assert fx_lib_arcgis_item != "x"

    @pytest.mark.parametrize(
        ("data", "metadata"),
        [
            (
                {
                    "id": "x",
                    "owner": "x",
                    "orgId": "x",
                    "title": "x",
                    "type": "Feature Service",
                    "url": "x",
                    "access": "private",
                },
                "<metadata><mdFileID>x</mdFileID><dataIdInfo/></metadata>",
            ),
            (
                {
                    "id": "x",
                    "owner": "x",
                    "orgId": "x",
                    "title": "x",
                    "type": "Feature Service",
                    "description": "x",
                    "snippet": "x",
                    "thumbnail": "thumbnail/ago_downloaded.png",
                    "accessInformation": "x",
                    "licenseInfo": "x",
                    "url": "x",
                    "access": "private",
                },
                "<metadata><mdFileID>x</mdFileID><dataIdInfo/></metadata>",
            ),
            (
                {
                    "id": "x",
                    "owner": "x",
                    "orgId": "x",
                    "created": 1773355682000,
                    "isOrgItem": True,
                    "modified": 1773406060000,
                    "guid": None,
                    "name": "x",
                    "title": "x",
                    "type": "Feature Service",
                    "typeKeywords": [
                        "ArcGIS Server",
                        "Data",
                        "Feature Access",
                        "Feature Service",
                        "Service",
                        "Singlelayer",
                        "Hosted Service",
                    ],
                    "description": "x",
                    "tags": [],
                    "snippet": "x",
                    "thumbnail": "thumbnail/ago_downloaded.png",
                    "documentation": None,
                    "extent": [[-180, -89.99], [180, -50]],
                    "categories": [],
                    "spatialReference": "102100",
                    "accessInformation": "x",
                    "classification": None,
                    "licenseInfo": "x",
                    "culture": "english",
                    "properties": None,
                    "advancedSettings": None,
                    "url": "x",
                    "proxyFilter": None,
                    "access": "private",
                    "size": 1,
                    "subInfo": 0,
                    "appCategories": [],
                    "industries": [],
                    "languages": [],
                    "largeThumbnail": None,
                    "banner": None,
                    "screenshots": [],
                    "listed": False,
                    "ownerFolder": "x",
                    "protected": False,
                    "numComments": 0,
                    "numRatings": 0,
                    "avgRating": 0,
                    "numViews": 1,
                    "itemControl": "update",
                    "scoreCompleteness": 1,
                    "groupDesignations": None,
                    "apiToken1ExpirationDate": -1,
                    "apiToken2ExpirationDate": -1,
                    "lastViewed": 1,
                },
                "<metadata><mdFileID>x</mdFileID><dataIdInfo/></metadata>",
            ),
        ],
    )
    def test_from_item_json(self, data: dict, metadata: str):
        """
        Can create an item instance for supported properties from ArcGIS item JSON and metadata.

        I.e. unsupported JSON properties are ignored but held in raw_item.
        """
        expected = Item(
            id="x",
            owner="x",
            org_id="x",
            url="x",
            sharing_level=self.test_sharing_level,
            properties=ItemProperties(
                title="x",
                item_type=self.test_type,
                snippet="x" if "snippet" in data else None,
                description="x" if "description" in data else None,
                access_information="x" if "accessInformation" in data else None,
                license_info="x" if "licenseInfo" in data else None,
                metadata=metadata,
            ),
        )

        item = Item.from_item_json(data=data, metadata=metadata)

        assert isinstance(item, Item)
        assert item == expected
        assert item.raw_item == data
        assert item.properties.metadata == metadata

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("access", "sharing_level"),
        [("private", SharingLevel.PRIVATE), ("org", SharingLevel.ORG), ("public", SharingLevel.EVERYONE)],
    )
    def test_from_item_json_public_access(self, fx_lib_arcgis_item: Item, access: str, sharing_level: SharingLevel):
        """Can map access property to SharingLevel enum (inc. 'public' to SharingLevel.EVERYONE)."""
        fx_lib_arcgis_item.sharing_level = sharing_level
        data = {
            "id": "x",
            "owner": "x",
            "orgId": "x",
            "title": "x",
            "type": "Feature Service",
            "url": "x",
            "access": access,
        }

        item = Item.from_item_json(data=data, metadata="x")
        assert item.sharing_level == sharing_level

    @pytest.mark.cov()
    def test_from_item_json_invalid_access(self, fx_lib_arcgis_item: Item):
        """Cannot use non SharingLevel value."""
        with pytest.raises(KeyError):
            Item.from_item_json(
                data={
                    "id": "x",
                    "owner": "x",
                    "orgId": "x",
                    "title": "x",
                    "type": "Feature Service",
                    "url": "x",
                    "access": "x",
                },
                metadata="x",
            )
