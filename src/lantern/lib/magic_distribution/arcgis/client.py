from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from functools import cached_property
from http import HTTPMethod
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import parse_qs, urlparse

import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7523 import ClientSecretJWT
from geojson import FeatureCollection
from lxml import etree

from lantern.lib.magic_distribution.arcgis.gis.dataclasses import Item
from lantern.lib.magic_distribution.arcgis.models.artefact import ArtefactArcGisService
from lantern.lib.magic_distribution.arcgis.utils import HTTPArcGISTokenAuth, check_arcgis_error, ensure_query_param
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel, ArtefactFormats

if TYPE_CHECKING:
    import logging


class SpatialExtent(NamedTuple):
    """Simple geospatial bounding box."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float


class ArcGisClient:
    """
    Lightweight client to manage content in ArcGIS Online.

    Uses ArcGIS APIs directly to avoid the complexity and overhead of the unwieldy ArcGIS API for Python package.

    Requires an ArcGIS OAuth credentials (developer credentials, application item) with appropriate permissions.

    See `docs/libraries.md#arcgis` (and `#arcgis-client` specifically) for more information, including supported item
    and service types.

    Supported features:
    -------------------
    - fetching item/service metadata
      - including Portal item ID for a Service, and Service for a Portal item (where applicable)
    - for feature services:
      - getting when a layer was last updated (based on its features)
      - getting features as a GeoJSON feature collection
    - for items:
      - getting item information, including optional additional metadata (for related file identifier) and thumbnail
      - getting item as a ServiceArtefact (for use with other MAGIC distribution workflows, see Items vs Artefacts)

    Internal conventions:
    ---------------------
    - `fetch` methods make network requests to access data directly
    - `get` methods return (processed) data, and may depend on one or more `fetch` methods
    """

    def __init__(self, logger: logging.Logger, app_client_id: str, app_client_secret: str) -> None:
        self._base_url = "https://www.arcgis.com/sharing/rest"
        self._timeout = 10

        self._logger = logger
        self._app_client_id = app_client_id
        self._app_client_secret = app_client_secret

    @cached_property
    def _access_token(self) -> str:
        """
        Get ArcGIS access token for an AGOL OAuth application.

        Using OAuth client credentials flow via AuthLib. Access token is cached for the lifetime of the client.

        ArcGIS requires the client ID/secret as body parameters, not from basic auth which AuthLib does by default.

        Sources:
        - https://developers.arcgis.com/documentation/security-and-authentication/reference/rest-authentication-operations/#access-token-from-client-credentials
        - https://developers.arcgis.com/documentation/security-and-authentication/reference/access-tokens/#how-to-use-an-access-token
        """
        self._logger.info("Acquiring token for AGOL client %s ...", self._app_client_id)
        token_endpoint = f"{self._base_url}/oauth2/token"
        session = OAuth2Session(
            client_id=self._app_client_id,
            client_secret=self._app_client_secret,
            token_endpoint_auth_method=ClientSecretJWT(token_endpoint),
        )
        token = session.fetch_token(
            token_endpoint, client_id=self._app_client_id, client_secret=self._app_client_secret
        )
        self._logger.info("Token acquired")
        return token["access_token"]

    def _request(self, method: HTTPMethod, url: str, format_: str | None = "json", **kwargs: Any) -> requests.Response:
        """Make HTTP request with default content-type, authentication and error handling."""
        timeout = kwargs.pop("timeout", self._timeout)
        if format_:
            url = ensure_query_param(url=url, name="f", value=format_)
        self._logger.debug("Calling %s %s ...", method.value, url)
        res = requests.request(
            method.value, url, timeout=timeout, auth=HTTPArcGISTokenAuth(token=self._access_token), **kwargs
        )
        # check for HTTP and ArcGIS application errors
        res.raise_for_status()
        check_arcgis_error(response=res)
        return res

    def _fetch_fs_info(self, service_endpoint: str) -> dict:
        """
        Get raw information for a layer within an ArcGIS Server feature service.

        Source:
        - https://developers.arcgis.com/rest/services-reference/enterprise/layer-feature-service
        """
        self._logger.info("Fetching info for service: %s", service_endpoint)
        res = self._request(method=HTTPMethod.GET, url=service_endpoint)
        return res.json()

    def _fetch_fs_layer_info(self, service_endpoint: str, layer_id: int = 0) -> dict:
        """
        Get raw information for a layer within an ArcGIS Server feature service.

        Source:
        - https://developers.arcgis.com/rest/services-reference/enterprise/layer-feature-service
        """
        url = f"{service_endpoint}/{layer_id}"
        self._logger.info("Fetching info for service layer: %s", url)
        res = self._request(method=HTTPMethod.GET, url=url)
        return res.json()

    def _fetch_item_id_for_service(self, service_endpoint: str) -> str:
        """Fetch ArcGIS Portal item ID corresponding to an ArcGIS Server service."""
        self._logger.info("Getting item for service endpoint: %s", service_endpoint)
        data = self._fetch_fs_info(service_endpoint=service_endpoint)
        return data["serviceItemId"]

    def get_fs_layer_last_data_update(self, service_endpoint: str, layer_id: int = 0) -> datetime:
        """
        Get when features in a layer within an ArcGIS feature service were last updated.

        Feature service layers expose several 'last update' type properties:
        - `dataLastEditDate`: when the layer's data was last updated
        - `schemaLastEditDate` when the layer's schema/definition was last changed
        - `lastEditDate`: described ambitiously as the "date of last edit to the layer", could be either of the above -
           or something else?
        - `last_updated` (as part of optional editor tracking): when each feature was last updated

        This method uses `dataLastEditDate`, to ignore schema or other changes, as editor tracking may not be enabled.
        """
        data = self._fetch_fs_layer_info(service_endpoint=service_endpoint, layer_id=layer_id)
        return datetime.fromtimestamp(timestamp=int(data["editingInfo"]["dataLastEditDate"]) / 1000, tz=UTC)

    def fetch_fs_layer_features_geojson(self, service_endpoint: str, layer_id: int = 0) -> FeatureCollection:
        """Fetch all features in a layer within an ArcGIS feature service as a GeoJSON feature collection."""
        url = f"{service_endpoint}/{layer_id}/query"
        self._logger.info("Fetching features as geojson for service layer: %s", url)
        res = self._request(
            method=HTTPMethod.GET,
            url=url,
            params={"where": "1=1", "outFields": "*", "returnGeometry": "true", "returnIdsOnly": "false"},
            format_="geojson",
        )
        data = res.json()

        try:
            fc = FeatureCollection(**data)
        except TypeError as e:
            msg = "GeoJSON parse error"
            raise ValueError(msg) from e
        if not fc.is_valid:
            msg = "GeoJSON parse error"
            raise ValueError(msg) from None

        self._logger.info("Fetched %s features", len(fc["features"]))
        return fc

    def _fetch_item_info(self, item_id: str) -> dict:
        """
        Fetch raw information for an ArcGIS Portal item.

        I.e. the contents of the item.json file used to populate Arc item pages.

        Includes a workaround for a missing `orgId` property which is required by the ArcGIS Item data class but does
        not always seem to be included in API responses.

        Source:
        - https://developers.arcgis.com/rest/users-groups-and-items/item
        """
        self._logger.info("Fetching info for item: %s", item_id)
        res = self._request(method=HTTPMethod.GET, url=f"{self._base_url}/content/items/{item_id}")
        data = res.json()
        if "orgId" not in data:
            data["orgId"] = ""
        return data

    def _fetch_item_metadata(self, item_id: str) -> str:
        """
        Fetch optional additional metadata for an ArcGIS Portal item.

        Returns the raw contents of a metadata.xml in the item info folder, if defined. This metadata may use any
        supported standard / information model (e.g. ISO 19115, Dublin Core, etc.).

        Sources:
        - https://doc.arcgis.com/en/arcgis-online/manage-data/metadata.htm
        """
        self._logger.info("Fetching additional metadata for item: %s", item_id)

        res = self._request(
            method=HTTPMethod.GET,
            url=f"{self._base_url}/content/items/{item_id}/info/metadata/metadata.xml",
            format_=None,
        )
        return res.text

    def _fetch_item_thumbnail(self, item_id: str, item_info: dict | None = None) -> tuple[str, str]:
        """
        Fetch optional thumbnail for an ArcGIS Portal item.

        Returns thumbnail path (relative to item info) and a SHA1 hash of thumbnail content at a fixed 400px width (as
        ArcGIS dynamically resizes images, giving different hash values).

        Where an item does not have a user defined (or automatically generated) thumbnail, Arc and therefore this method,
        returns a system default image. In the unlikely event this isn't included in item info, None is returned.

        For example (where a custom thumbnail is set):
        > ('thumbnail/thumbnail2301741882573.png', 'https://www.arcgis.com/sharing/rest/content/items/7e7e330746e990b0d617e3ef4fbba12c/info/thumbnail/thumbnail2301741882573.png?sha1=14262ee9366ea581864d35ad0dff5078bf552147&w=400')

        For example (where the default AGOL thumbnail is used):
        > ('thumbnail/ago_downloaded.gif', 'https://www.arcgis.com/sharing/rest/content/items/123/info/thumbnail/ago_downloaded.gif?sha1=072474daf1f659a8261486063021ad187155713b&w=400')
        """
        self._logger.info("Fetching thumbnail for item: %s", item_id)
        item_info = item_info or self._fetch_item_info(item_id=item_id)
        thumbnail_path: str = item_info["thumbnail"]

        # request thumbnail info for error checking
        res = self._request(
            method=HTTPMethod.GET,
            url=f"{self._base_url}/content/items/{item_id}/info/{thumbnail_path}",
            format_=None,
            params={"w": "400"},
        )
        # a successful response will be in binary unless an error occurs (caught by standard request handling)

        thumbnail_url = urlparse(res.url)
        sha1 = hashlib.sha1(res.content).hexdigest()  # noqa: S324
        access_url = f"{thumbnail_url.scheme}://{thumbnail_url.netloc}{thumbnail_url.path}?sha1={sha1}&w=400"
        return thumbnail_path, access_url

    def get_item(self, item_id: str) -> Item:
        """
        Get ArcGIS Portal item by item ID.

        Combines item info, external/additional metadata and thumbnail.

        Returned as native ArcGIS item dataclass.
        """
        self._logger.info("Fetching item: %s", item_id)
        info = self._fetch_item_info(item_id=item_id)
        meta = self._fetch_item_metadata(item_id=item_id)
        thumbnail = self._fetch_item_thumbnail(item_id=item_id, item_info=info)

        return Item.from_item_json(info=info, metadata=meta, thumbnail=thumbnail)

    @staticmethod
    def _get_item_file_identifier(item: Item) -> str | None:
        """Attempt to get catalogue resource associated with ArcGIS Portal item based on optionally attached metadata."""
        if not item.properties.metadata:
            return None
        root = etree.fromstring(item.properties.metadata.encode())
        md_file_id_elem = root.find("mdFileID")
        return md_file_id_elem.text if md_file_id_elem is not None else None

    @staticmethod
    def get_service_endpoint_for_item(item: Item) -> str | None:
        """Attempt to get endpoint for backing service an ArcGIS Portal item ID represents if applicable."""
        if item.url == "":
            return None
        return item.url

    @staticmethod
    def get_item_geo_extent(item: Item) -> SpatialExtent | None:
        """Attempt to get bounding geographic extent from an ArcGIS Portal item."""
        extent = item.properties.extent
        if not extent:
            return None
        if not isinstance(extent, list):
            msg = "Invalid item bounding geographic extent."
            raise TypeError(msg) from None
        (x_min, y_min), (x_max, y_max) = extent
        return SpatialExtent(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)

    @staticmethod
    def _get_item_artefact_format(item: Item) -> ArtefactFormatLabel:
        """Determine artefact format based on item type and item type keywords."""
        return ArtefactFormats.get_arcgis_item_format(
            item_type=item.properties.item_type.value, item_type_keywords=set(item.properties.type_keywords or [])
        ).label

    def _get_service_artefact_format(self, endpoint: str | None) -> ArtefactFormatLabel | None:
        """Determine artefact service format if applicable from endpoint URL and fetched capabilities."""
        if endpoint is None:
            return None
        return ArtefactFormats.get_service_format(
            endpoint=endpoint, endpoint_auth=HTTPArcGISTokenAuth(token=self._access_token)
        ).label

    def get_artefact(self, item_ref: str, resource_id: str | None = None) -> ArtefactArcGisService:
        """
        Get ArcGIS Portal item as a ArcGIS service artefact for an ArcGIS Online item ID or URL.

        Artefacts require an associated resource ID, which can either be provided directly or, if not defined, taken
        from additional metadata attached to a Portal item.
        """
        item_id = item_ref
        if item_ref and item_ref.startswith("http"):
            self._logger.debug("Treating reference as an item URL: %s", item_ref)
            try:
                item_id = parse_qs(urlparse(item_ref).query)["id"][0]
            except (KeyError, IndexError) as e:
                msg = f"Unable to extract item ID from URL: {item_ref}"
                raise ValueError(msg) from e
            self._logger.debug("Item URL parsed as: %s", item_id)
        if not item_id:
            msg = "Either ArcGIS Portal item ID or item URL required."
            raise ValueError(msg)

        item = self.get_item(item_id=item_id)
        item_format_label = self._get_item_artefact_format(item=item)
        service_format_label = self._get_service_artefact_format(endpoint=item.url)

        resource_id = resource_id or self._get_item_file_identifier(item)
        if not resource_id:
            msg = "Item must relate to a catalogue resource, no identifier found in item additional metadata."
            raise ValueError(msg) from None

        return ArtefactArcGisService(
            resource_id=resource_id,
            format_label=item_format_label,
            format_service_label=service_format_label,
            item=item,
        )
