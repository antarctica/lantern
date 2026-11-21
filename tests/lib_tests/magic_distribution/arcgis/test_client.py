from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

import pytest
from pytest_httpserver import HTTPServer, RequestMatcher
from werkzeug import Response

from lantern.lib.magic_distribution.arcgis.client import (
    ArcGisClient,
    SharingChangeNotAuthorisedError,
    SpatialExtent,
)
from lantern.lib.magic_distribution.arcgis.gis.dataclasses import Item, ItemProperties
from lantern.lib.magic_distribution.arcgis.gis.enums import ItemType, SharingLevel
from lantern.lib.magic_distribution.arcgis.models.artefact import ArtefactArcGisService
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel, ArtefactFormats

if TYPE_CHECKING:
    import logging

    from pytest_mock import MockerFixture


class TestArcGisClient:
    """
    Test lightweight ArcGIS client.

    Tests for this class largely rely on VCR recordings made for real interactions, adapted to use fake entities.

    To test new methods:
    - configure the test to use real parameters
    - update the `fx_lib_arcgis_client` fixture to use real credentials and disable mocks
    - record the test (see dev.md#pytest-recording)
    - review the cassette and refactor to use faked values
    - remove the first exchange (for getting an access token), which is skipped in the mocked fixture
    - restore the fixture and re-run the test to confirm
    """

    def test_init(self, fx_logger: logging.Logger):
        """Can initialise client with required parameters."""
        client = ArcGisClient(
            logger=fx_logger,
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
        )
        assert isinstance(client, ArcGisClient)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.filterwarnings("ignore:Key size should be >= 112 bits:Warning")
    def test_access_token(self, fx_logger: logging.Logger):
        """Can get an ArcGIS access token."""
        client = ArcGisClient(
            logger=fx_logger,
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
        )
        result = client._access_token
        assert len(result) > 0

    @pytest.mark.cov()
    @pytest.mark.parametrize("format_", [None, "json"])
    def test_request(self, fx_lib_arcgis_client: ArcGisClient, httpserver: HTTPServer, format_: str | None):
        """Can attach bearer token and format to a request."""
        _route = "/"
        _status = HTTPStatus.ACCEPTED
        httpserver.expect_request(_route).respond_with_response(Response(status=_status))

        fx_lib_arcgis_client._request(method=HTTPMethod.HEAD, url=httpserver.url_for(_route), format_=format_)

        httpserver.assert_request_made(RequestMatcher(_route))
        for request, response in httpserver.iter_matching_requests(RequestMatcher(_route)):
            # query string parameters may be repeated so select the first instance of each
            query_params = parse_qs(request.query_string.decode(), keep_blank_values=True)
            assert query_params["token"][0] == "x"
            if format_:
                assert query_params["f"][0] == format_
            else:
                assert "f" not in query_params
            assert response.status_code == _status

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_fs_info(self, fx_lib_arcgis_client: ArcGisClient):
        """Can fetch information about a Server feature service."""
        result = fx_lib_arcgis_client._fetch_fs_info(
            service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
        )
        assert isinstance(result, dict)
        assert result["serviceItemId"] == "123"
        assert isinstance(result["layers"], list)
        assert len(result["layers"]) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_fs_layer_info(self, fx_lib_arcgis_client: ArcGisClient):
        """Can fetch information about a layer within a Server feature service."""
        expected = 0
        result = fx_lib_arcgis_client._fetch_fs_layer_info(
            service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer",
            layer_id=expected,
        )
        assert isinstance(result, dict)
        assert result["id"] == expected
        assert result["serviceItemId"] == "123"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_item_id_for_service(self, fx_lib_arcgis_client: ArcGisClient):
        """Can fetch Portal item ID for a Server service."""
        assert (
            fx_lib_arcgis_client._fetch_item_id_for_service(
                service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
            )
            == "x"
        )

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_fs_layer_last_data_update(self, fx_lib_arcgis_client: ArcGisClient):
        """Can get the last time features were updated in a layer within a Server feature service."""
        result = fx_lib_arcgis_client.get_fs_layer_last_data_update(
            service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
        )
        assert result == datetime(2024, 7, 30, 8, 37, 3, 961000, tzinfo=UTC)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_fs_layer_features_geojson(self, fx_lib_arcgis_client: ArcGisClient):
        """Can get features in a layer within a Server feature service as a GeoJSON feature collection."""
        result = fx_lib_arcgis_client.fetch_fs_layer_features_geojson(
            service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
        )
        assert isinstance(result, dict)
        assert isinstance(result["features"], list)
        assert len(result["features"]) > 0

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("variant", ["missing_key", "invalid_feature"])
    def test_fetch_fs_layer_features_geojson_invalid(self, fx_lib_arcgis_client: ArcGisClient, variant: str):
        """
        Cannot get features in a layer where GeoJSON feature collection is invalid.

        See VCR cassettes for invalid data variants.
        """
        with pytest.raises(ValueError, match=r"GeoJSON parse error"):
            fx_lib_arcgis_client.fetch_fs_layer_features_geojson(
                service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
            )

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("with_org_id", [False, True])
    def test_fetch_item_info(self, fx_lib_arcgis_client: ArcGisClient, with_org_id: bool):
        """
        Can fetch info for a Portal item.

        Includes coverage check for missing `orgId` property.
        """
        expected = "x"
        result = fx_lib_arcgis_client._fetch_item_info(item_id=expected)
        assert isinstance(result, dict)
        assert result["id"] == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_item_info(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Can update properties within a Portal item."""
        expected = "Foo"
        original = ItemProperties(
            title=fx_lib_arcgis_item.properties.title,
            item_type=fx_lib_arcgis_item.properties.item_type,
            metadata=fx_lib_arcgis_item.properties.metadata,
        )
        update = deepcopy(original)
        update.title = expected

        fx_lib_arcgis_client._set_item_info(
            owner_id=fx_lib_arcgis_item.owner, item_id=fx_lib_arcgis_item.id, properties=update
        )

        result = fx_lib_arcgis_client._fetch_item_info(fx_lib_arcgis_item.id)
        assert result["title"] == expected
        assert result["title"] != original.title

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_item_metadata(self, fx_lib_arcgis_client: ArcGisClient):
        """
        Can fetch additional metadata for a Portal item.

        I.e. external information stored as a related file for the item in one of Arc's supported metadata standards.
        """
        result = fx_lib_arcgis_client._fetch_item_metadata(item_id="x")
        assert "<metadata>" in result

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_item_metadata(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Can update metadata associated with a Portal item."""
        expected = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><metadata><mdFileID>y</mdFileID></metadata>'

        fx_lib_arcgis_client._set_item_metadata(
            owner_id=fx_lib_arcgis_item.owner, item_id=fx_lib_arcgis_item.id, metadata=expected
        )

        result = fx_lib_arcgis_client._fetch_item_metadata(fx_lib_arcgis_item.id)
        assert result == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("with_custom", [False, True])
    @pytest.mark.parametrize("with_info", [False, True])
    def test_fetch_item_thumbnail(self, fx_lib_arcgis_client: ArcGisClient, with_custom: bool, with_info: bool):
        """Can fetch thumbnail for a Portal item if set, with or without pre-fetched item info."""
        thumbnail = "thumbnail/thumbnail123.png" if with_custom else "thumbnail/ago_downloaded.gif"
        info = {"id": "x", "thumbnail": thumbnail} if with_info else None
        item_id = "x" if with_custom else "y"  # 7 (with custom thumbnail) = x

        result = fx_lib_arcgis_client._fetch_item_thumbnail(item_id=item_id, item_info=info)
        assert len(result) == 2  # noqa: PLR2004
        assert result[0] == thumbnail

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_item_thumbnail(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Can update metadata associated with a Portal item."""
        expected = "https://www.arcgis.com/sharing/rest/content/items/x/info/thumbnail/ago_downloaded.png?sha1=11f6ad8ec52a2984abaafd7c3b516503785c2072&w=400"

        fx_lib_arcgis_client._set_item_thumbnail(
            owner_id=fx_lib_arcgis_item.owner, item_id=fx_lib_arcgis_item.id, url="https://example.com/overview.png"
        )

        result = fx_lib_arcgis_client._fetch_item_thumbnail(fx_lib_arcgis_item.id)
        assert result[1] == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_item_sharing(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Can update metadata associated with a Portal item."""
        expected = SharingLevel.ORG
        fx_lib_arcgis_client._set_item_sharing(
            owner_id=fx_lib_arcgis_item.owner, item_id=fx_lib_arcgis_item.id, sharing_level=expected
        )

        result = fx_lib_arcgis_client._fetch_item_info(fx_lib_arcgis_item.id)
        assert SharingLevel[result["access"].upper()] == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_item(self, fx_lib_arcgis_client: ArcGisClient):
        """Can get a Portal item with info, metadata and thumbnail as an ArcGIS item dataclass."""
        item_id = "x"
        result = fx_lib_arcgis_client.get_item(item_id=item_id)
        assert isinstance(result, Item)
        assert result.id == item_id

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        "properties", [None, ItemProperties(title="x", item_type=ItemType.FEATURE_SERVICE, metadata="")]
    )
    @pytest.mark.parametrize("metadata", [None, "x"])
    @pytest.mark.parametrize("sharing_level", [None, SharingLevel.ORG])
    @pytest.mark.parametrize("thumbnail_url", [None, "x"])
    def test_set_item(
        self,
        mocker: MockerFixture,
        fx_lib_arcgis_client: ArcGisClient,
        fx_lib_arcgis_item: Item,
        properties: ItemProperties | None,
        metadata: str | None,
        sharing_level: SharingLevel | None,
        thumbnail_url: str | None,
    ):
        """Can set supported parts of a Portal item."""
        mocker.patch.object(fx_lib_arcgis_client, "_set_item_info", return_value=None)
        mocker.patch.object(fx_lib_arcgis_client, "_set_item_metadata", return_value=None)
        mocker.patch.object(fx_lib_arcgis_client, "_set_item_thumbnail", return_value=None)
        mocker.patch.object(fx_lib_arcgis_client, "_set_item_sharing", return_value=None)

        fx_lib_arcgis_client.set_item(
            item=fx_lib_arcgis_item,
            info_properties=properties,
            metadata=metadata,
            sharing_level=sharing_level,
            thumbnail_url=thumbnail_url,
        )

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_reassign_item(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Can move an item to another owner and optional folder."""
        expected = "y"

        fx_lib_arcgis_client.reassign_item(
            owner_id=fx_lib_arcgis_item.owner, item_id=fx_lib_arcgis_item.id, new_owner_id=expected
        )

        result = fx_lib_arcgis_client._fetch_item_info(fx_lib_arcgis_item.id)
        assert result["owner"] == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize("with_value", [False, True])
    def test_get_item_file_identifier(
        self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item, with_value: bool
    ):
        """Can get associated catalogue/record/resource file identifier from additional item metadata if set."""
        expected = "x" if with_value else None
        metadata = f'<?xml version="1.0" encoding="UTF-8" standalone="no"?><metadata><mdFileID>{expected}</mdFileID></metadata>'
        fx_lib_arcgis_item.properties.metadata = metadata if with_value else None

        result = fx_lib_arcgis_client._get_item_file_identifier(fx_lib_arcgis_item)
        assert result == expected

    @pytest.mark.cov()
    def test_get_item_file_identifier_invalid(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Cannot get file identifier from invalid or malformed."""
        fx_lib_arcgis_item.properties.metadata = "x"
        result = fx_lib_arcgis_client._get_item_file_identifier(fx_lib_arcgis_item)
        assert result is None

    @pytest.mark.cov()
    @pytest.mark.parametrize("is_service", [False, True])
    def test_fetch_service_endpoint_for_item(
        self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item, is_service: bool
    ):
        """Can get Server service endpoint from Portal item if applicable (i.e. not a web map)."""
        expected = "x" if is_service else None
        fx_lib_arcgis_item.url = "x" if is_service else ""

        result = fx_lib_arcgis_client.get_service_endpoint_for_item(fx_lib_arcgis_item)
        assert result == expected

    @pytest.mark.parametrize("with_extent", [False, True])
    def test_get_item_geo_extent(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item, with_extent: bool):
        """
        Can get bounding box spatial extent from Portal item if set.

        In theory this should always be set for the item types we support (i.e. not PowerPoint documents, etc.).
        """
        raw_extent = [[1.0, 2.0], [3.0, 4.0]]
        fx_lib_arcgis_item.properties.extent = raw_extent if with_extent else []
        expected = SpatialExtent(1.0, 3.0, 2.0, 4.0) if with_extent else None

        result = fx_lib_arcgis_client.get_item_geo_extent(fx_lib_arcgis_item)
        assert result == expected

    @pytest.mark.cov()
    def test_get_item_geo_extent_invalid(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Cannot get bounding box spatial extent from Portal item if set to an invalid value."""
        fx_lib_arcgis_item.properties.extent = "x"

        with pytest.raises(TypeError, match=r"Invalid item bounding geographic extent."):
            fx_lib_arcgis_client.get_item_geo_extent(fx_lib_arcgis_item)

    @pytest.mark.parametrize("endpoint", [None, "https://example.com"])
    def test_get_service_artefact_format(
        self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient, endpoint: str | None
    ):
        """Can optionally determine ArcGIS service format."""
        expected = ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE
        service_format = ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE)
        mocker.patch.object(ArtefactFormats, "get_service_format", return_value=service_format)

        result = fx_lib_arcgis_client._get_service_artefact_format(endpoint)
        if endpoint:
            assert result == expected
        else:
            assert result is None

    def test_diff_items(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """
        Can identify changes to supported ArcGIS item properties.

        With all optional (supported) properties set, and all different to the comparison.
        """
        item = deepcopy(fx_lib_arcgis_item)
        item.properties.snippet = "x"
        item.properties.access_information = "x"
        item.properties.metadata = "<metadata><mdFileID>x</mdFileID></metadata>"  # to support value parsing
        item.properties.description = "<div>x</div>"  # to account for HTML normalisation
        item.properties.license_info = "<div>x</div>"  # to account for HTML normalisation
        item.properties.thumbnail_url = "https://example.com/thumbnail.png?sha1=123&sha1Agol=231"

        # All different
        other = deepcopy(fx_lib_arcgis_item)
        other.sharing_level = SharingLevel.ORG  # vs. private
        other.properties.metadata = "<metadata><mdFileID>y</mdFileID></metadata>"  # to support value parsing
        other.properties.title = "y"
        other.properties.snippet = "y"
        other.properties.access_information = "y"
        other.properties.description = "<div>y</div>"  # to account for HTML normalisation
        other.properties.license_info = "<div>y</div>"  # to account for HTML normalisation
        other.properties.thumbnail_url = "https://example.com/thumbnail.png?sha1=999"

        expected = {
            "sharing_level": item.sharing_level,
            "metadata": item.properties.metadata,
            "title": item.properties.title,
            "snippet": item.properties.snippet,
            "accessInformation": item.properties.access_information,
            "description": item.properties.description,
            "licenseInfo": item.properties.license_info,
            "thumbnail_url": item.properties.thumbnail_url,
        }

        result = fx_lib_arcgis_client.diff_items(item, other)
        assert result == expected

    @pytest.mark.cov()
    def test_diff_items_missing_optional(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Does not include supported properties that are missing from the source item."""
        item = deepcopy(fx_lib_arcgis_item)

        other = deepcopy(fx_lib_arcgis_item)
        other.properties.snippet = "y"
        other.properties.access_information = "y"
        other.properties.description = "<div>y</div>"  # to account for HTML normalisation
        other.properties.license_info = "<div>y</div>"  # to account for HTML normalisation

        assert fx_lib_arcgis_client.diff_items(item, other) == {}

    @pytest.mark.parametrize("allow_sharing_change", [False, True])
    def test_sync_item_no_changes(
        self,
        mocker: MockerFixture,
        fx_lib_arcgis_client: ArcGisClient,
        fx_lib_arcgis_item: Item,
        allow_sharing_change: bool,
    ):
        """Can not update a target where there are no differences with the source."""
        mocker.patch.object(fx_lib_arcgis_client, "diff_items", return_value={})
        mocker.patch.object(fx_lib_arcgis_client, "set_item")

        result = fx_lib_arcgis_client.sync_item(
            source=fx_lib_arcgis_item, target=fx_lib_arcgis_item, allow_sharing_change=allow_sharing_change
        )
        assert result is False

    @pytest.mark.parametrize(
        "diff",
        [
            {"title": "updated"},
            {"snippet": "summary"},
            {"metadata": "updated metadata"},
            {"thumbnail_url": "https://example.com/updated.png?sha1=updated"},
            {"sharing_level": SharingLevel.EVERYONE},
            {
                "title": "updated",
                "snippet": "summary",
                "description": "<div>description</div>",
                "accessInformation": "attribution",
                "licenseInfo": "<div>licence</div>",
                "metadata": "updated metadata",
                "thumbnail_url": "https://example.com/updated.png?sha1=updated",
                "sharing_level": SharingLevel.ORG,
            },
        ],
    )
    def test_sync_item(
        self, mocker: MockerFixture, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item, diff: dict
    ):
        """Can update a target item based on differences with the source."""
        mocker.patch.object(fx_lib_arcgis_client, "diff_items", return_value=deepcopy(diff))
        set_item = mocker.patch.object(fx_lib_arcgis_client, "set_item")

        source = deepcopy(fx_lib_arcgis_item)
        target = deepcopy(fx_lib_arcgis_item)
        target.properties.title = "target title"
        target.properties.item_type = ItemType.FEATURE_SERVICE
        target.properties.metadata = "target metadata"
        metadata = diff.get("metadata", "target metadata")
        expected = ItemProperties(
            title=diff.get("title", "target title"),
            item_type=ItemType.FEATURE_SERVICE,
            metadata=metadata,
            snippet=diff.get("snippet"),
            description=diff.get("description"),
            access_information=diff.get("accessInformation"),
            license_info=diff.get("licenseInfo"),
        )

        result = fx_lib_arcgis_client.sync_item(source=source, target=target, allow_sharing_change=True)
        assert result is True
        set_item.assert_called_once_with(
            item=target,
            info_properties=expected,
            metadata=metadata,
            sharing_level=diff.get("sharing_level"),
            thumbnail_url=diff.get("thumbnail_url"),
        )

    @pytest.mark.cov()
    def test_sync_item_sharing_not_authorised(
        self,
        mocker: MockerFixture,
        fx_lib_arcgis_client: ArcGisClient,
        fx_lib_arcgis_item: Item,
    ):
        """Cannot change the sharing level of an item unless authorised."""
        mocker.patch.object(fx_lib_arcgis_client, "diff_items", return_value={"sharing_level": SharingLevel.PRIVATE})
        mocker.patch.object(fx_lib_arcgis_client, "set_item")
        target = deepcopy(fx_lib_arcgis_item)
        fx_lib_arcgis_item.sharing_level = SharingLevel.EVERYONE

        with pytest.raises(SharingChangeNotAuthorisedError):
            fx_lib_arcgis_client.sync_item(source=fx_lib_arcgis_item, target=target)

    @pytest.mark.parametrize("item_ref", [None, "x", "https://example.com?id=x"])
    @pytest.mark.parametrize("resource_id", [None, "x"])
    @pytest.mark.parametrize("with_metadata_id", [False, True])
    def test_get_artefact(
        self,
        mocker: MockerFixture,
        fx_lib_arcgis_client: ArcGisClient,
        fx_lib_arcgis_item: Item,
        item_ref: str,
        resource_id: bool,
        with_metadata_id: bool,
    ):
        """
        Can create an ArcGIS service artefact from an ArcGIS Item.

        Implicitly tests `_get_item_artefact_format`.
        """
        metadata = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><metadata><mdFileID>x</mdFileID></metadata>'
        fx_lib_arcgis_item.properties.metadata = metadata if with_metadata_id else None
        mocker.patch.object(fx_lib_arcgis_client, "get_item", return_value=fx_lib_arcgis_item)
        mocker.patch.object(fx_lib_arcgis_client, "_get_service_artefact_format", return_value=None)

        if not item_ref:
            with pytest.raises(ValueError, match=r"Either ArcGIS Portal item ID or item URL required."):
                fx_lib_arcgis_client.get_artefact(item_ref=item_ref, resource_id=resource_id)
            return

        if not resource_id and not with_metadata_id:
            with pytest.raises(
                ValueError,
                match=r"Item must relate to a catalogue resource, no identifier found in item additional metadata.",
            ):
                fx_lib_arcgis_client.get_artefact(item_ref=item_ref, resource_id=resource_id)
            return

        result = fx_lib_arcgis_client.get_artefact(item_ref=item_ref, resource_id=resource_id)
        assert isinstance(result, ArtefactArcGisService)
        assert (
            repr(result) == "<ArtefactArcGiS: x, ArcGIS Feature Layer, https://www.maps.arcgis.com/home/item.html?id=x>"
        )

    def test_get_artefact_invalid_url(self, fx_lib_arcgis_client: ArcGisClient, fx_lib_arcgis_item: Item):
        """Cannot create an ArcGIS service artefact with an invalid ArcGIS item URL."""
        with pytest.raises(ValueError, match=r"Unable to extract item ID from URL: https://example.com"):
            fx_lib_arcgis_client.get_artefact(item_ref="https://example.com")
