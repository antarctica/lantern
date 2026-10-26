from __future__ import annotations

import hashlib
from functools import cached_property
from http import HTTPMethod
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7523 import ClientSecretJWT
from lxml import etree

from lantern.lib.arcgis.gis.dataclasses import Item
from lantern.lib.arcgis.utils import HTTPArcGISTokenAuth, check_arcgis_error, ensure_query_param
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel, ArtefactFormats
from lantern.lib.magic_distribution.models.artefact import ArtefactArcGisService

if TYPE_CHECKING:
    import logging


class ArcGisClient:
    """
    Lightweight client to manage content in ArcGIS Online.

    Supports:
    - ...

    Does not support ...

    Uses the ArcGIS APIs directly to avoid the complexity and overhead of the unwieldy ArcGIS Python SDK.

    Requires an ArcGIS OAuth credentials (developer credentials, application item) with appropriate permissions.
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

    def _get_item_id_for_service(self, service_endpoint: str) -> str:
        """Get ArcGIS Portal item ID corresponding to an ArcGIS Server service."""
        self._logger.info("Getting item for service endpoint: %s", service_endpoint)

        req = self._request(method=HTTPMethod.GET, url=service_endpoint)
        data = req.json()
        return data["serviceItemId"]

    def _get_item_info(self, item_id: str) -> dict:
        """
        Get raw information for an ArcGIS Portal item.

        I.e. the contents of the item.json file used to populate Arc item pages.

        Source:
        - https://developers.arcgis.com/rest/users-groups-and-items/item
        """
        self._logger.info("Fetching info for item: %s", item_id)
        res = self._request(method=HTTPMethod.GET, url=f"{self._base_url}/content/items/{item_id}")
        return res.json()

    def _get_item_metadata(self, item_id: str) -> str:
        """
        Get optional additional metadata for an ArcGIS Portal item.

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

    def _get_item_thumbnail(self, item_id: str, item_info: dict | None = None) -> tuple[str, str]:
        """
        Get optional thumbnail for an ArcGIS Portal item.

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
        item_info = item_info or self._get_item_info(item_id=item_id)
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

    def _get_item(self, item_id: str) -> Item:
        """
        Get ArcGIS Portal item by item ID.

        Combines item info, external/additional metadata and thumbnail.

        Returned as native ArcGIS item dataclass.
        """
        self._logger.info("Fetching item: %s", item_id)
        info = self._get_item_info(item_id=item_id)
        meta = self._get_item_metadata(item_id=item_id)
        thumbnail = self._get_item_thumbnail(item_id=item_id, item_info=info)

        return Item.from_item_json(data=info, metadata=meta, thumbnail=thumbnail)

    @staticmethod
    def _get_item_file_identifier(item: Item) -> str | None:
        """Attempt to get catalogue resource associated with ArcGIS item based on optionally attached metadata."""
        if not item.properties.metadata:
            return None
        root = etree.fromstring(item.properties.metadata.encode())
        md_file_id_elem = root.find("mdFileID")
        return md_file_id_elem.text if md_file_id_elem is not None else None

    @staticmethod
    def _get_item_artefact_format(item: Item) -> ArtefactFormatLabel:
        """Determine artefact format based on item type and item type keywords."""
        return ArtefactFormats.get_arcgis_item_format(
            item_type=item.properties.item_type.value, item_type_keywords=set(item.properties.type_keywords or [])
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
            msg = "Either ArcGIS item ID or item URL required."
            raise ValueError(msg)

        item = self._get_item(item_id=item_id)
        format_label = self._get_item_artefact_format(item=item)
        resource_id = resource_id or self._get_item_file_identifier(item)
        if not resource_id:
            msg = "Item must relate to a catalogue resource, no identifier found in item additional metadata."
            raise ValueError(msg) from None

        return ArtefactArcGisService(resource_id=resource_id, format_label=format_label, item=item)
