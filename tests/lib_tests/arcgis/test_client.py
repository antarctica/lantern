from __future__ import annotations

from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

import pytest
from pytest_httpserver import HTTPServer, RequestMatcher
from werkzeug import Response

from lantern.lib.arcgis.client import ArcGisClient
from lantern.lib.arcgis.gis.dataclasses import Item
from lantern.lib.magic_distribution.models.artefact import ArtefactArcGisService

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
    def test_get_item_id_for_service(self, fx_lib_arcgis_client: ArcGisClient):
        """Can get Portal item ID for a Server service."""
        assert (
            fx_lib_arcgis_client._get_item_id_for_service(
                service_endpoint="https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
            )
            == "x"
        )

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_item_info(self, fx_lib_arcgis_client: ArcGisClient):
        """Can get info for a Portal item."""
        result = fx_lib_arcgis_client._get_item_info(item_id="x")
        assert isinstance(result, dict)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_item_metadata(self, fx_lib_arcgis_client: ArcGisClient):
        """
        Can get additional metadata for a Portal item.

        I.e. external information stored as a related file for the item in one of Arc's supported metadata standards.
        """
        result = fx_lib_arcgis_client._get_item_metadata(item_id="x")
        assert "<metadata>" in result

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("with_custom", [False, True])
    @pytest.mark.parametrize("with_info", [False, True])
    def test_get_item_thumbnail(self, fx_lib_arcgis_client: ArcGisClient, with_custom: bool, with_info: bool):
        """Can get thumbnail for a Portal item if set, with or without pre-fetched item info."""
        thumbnail = "thumbnail/thumbnail123.png" if with_custom else "thumbnail/ago_downloaded.gif"
        info = {"id": "x", "thumbnail": thumbnail} if with_info else None
        item_id = "x" if with_custom else "y"  # 7 (with custom thumbnail) = x

        result = fx_lib_arcgis_client._get_item_thumbnail(item_id=item_id, item_info=info)
        assert len(result) == 2  # noqa: PLR2004
        assert result[0] == thumbnail

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_item(self, fx_lib_arcgis_client: ArcGisClient):
        """Can get a Portal item with info, metadata and thumbnail as an ArcGIS item dataclass."""
        item_id = "x"
        result = fx_lib_arcgis_client._get_item(item_id=item_id)
        assert isinstance(result, Item)
        assert result.id == item_id

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
        """Can create an ArcGIS service artefact from an ArcGIS Item."""
        metadata = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><metadata><mdFileID>x</mdFileID></metadata>'
        fx_lib_arcgis_item.properties.metadata = metadata if with_metadata_id else None
        mocker.patch.object(fx_lib_arcgis_client, "_get_item", return_value=fx_lib_arcgis_item)

        if not item_ref:
            with pytest.raises(ValueError, match=r"Either ArcGIS item ID or item URL required."):
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
