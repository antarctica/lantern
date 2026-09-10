import contextlib
from functools import cached_property
from http import HTTPMethod, HTTPStatus
from typing import Any, cast

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from lantern.lib.magic_distribution.models.artefact import (
    ArtefactFile,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.models.metadata import ArtefactMetadata, ResourceMetadata


class SiteNotFoundError(Exception):
    """
    Raised when a requested SharePoint / Microsoft Graph 'Site' resource cannot be found.

    Because the site identifier is wrong, the site does not exist or the configured app registration cannot access it.
    """


class DriveNotFoundError(Exception):
    """
    Raised when a requested SharePoint Document Library / Microsoft Graph 'Drive' resource cannot be found.

    Because the drive identifier is wrong, the drive does not exist or the configured app registration cannot access it.
    """


class DriveItemNotFoundError(Exception):
    """
    Raised when a requested SharePoint file / Microsoft Graph 'DriveItem' resource cannot be found.

    Because the drive item identifier is wrong, the drive item does not exist or the configured app registration cannot
    access it.
    """


class ArtefactHashMismatchError(Exception):
    """Raised when the file hash differs between an artefact's local source and remote (uploaded) version."""


class ArtefactPermissionsNotSupportedError(Exception):
    """Raised when trying to deposit an artefact with unsupported permissions."""


class MagicResourceDistributionClient:
    """
    Client to deposit resource distribution artefacts in the MAGIC Resource Distribution SharePoint Online site.

    Supports creating directories, uploading files (via an upload session if needed) and setting required list metadata
    using the Microsoft Graph API. Does not support updating or removing existing artefacts.

    List metadata is specific to MAGIC Resource Distribution libraries (as per the MagicDistributionMetadata typed dict).

    Requires an Entra app registration with the `Sites.Selected` permission configured for the relevant SharePoint site.
    """

    def __init__(
        self,
        tenant_id: str,
        app_client_id: str,
        app_client_secret: str,
        site_id: str,
        library_name: str,
        proxy_url: str | None = None,
    ) -> None:
        self._timeout = 10
        self._scopes = ["https://graph.microsoft.com/.default"]
        self._graph_base = "https://graph.microsoft.com/v1.0"

        self._max_simple_upload_size = 250 * 1024 * 1024  # 250MB max size for small uploads
        self._upload_chunk_size = 50 * 1024 * 1024  # 50MB per chunk for large uploads

        self._tenant_id = tenant_id
        self._client_id = app_client_id
        self._client_secret = app_client_secret
        self._site_id = site_id
        self._library_name = library_name
        self._proxy_base = proxy_url

        self._session = Session()
        retries = Retry(
            total=0,
            backoff_factor=0.2,
            status_forcelist=[400],
            allowed_methods={"POST", "PATCH", "PUT", "GET"},
            raise_on_status=False,
        )
        self._session.mount(prefix=self._graph_base, adapter=HTTPAdapter(max_retries=retries))

    @cached_property
    def _graph_token(self) -> str:
        """Get Microsoft Graph access token."""
        response = requests.post(
            f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": " ".join(self._scopes),
                "grant_type": "client_credentials",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    @cached_property
    def _drive_id(self) -> str:
        """Get Microsoft Graph Drive ID."""
        return self._get_drive_id(site_id=self._site_id, library_name=self._library_name)

    def _request(
        self,
        method: HTTPMethod,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Make HTTP request with default timeout, header for bearer token and retry logic via session."""
        timeout = kwargs.pop("timeout", self._timeout)
        headers = kwargs.pop("headers", {"Accept": "application/json", "Authorization": f"Bearer {self._graph_token}"})
        return self._session.request(method.value, url, headers=headers, timeout=timeout, **kwargs)

    def _get_drive_id(self, site_id: str, library_name: str) -> str:
        """
        Get Microsoft Graph Drive ID for a SharePoint document library.

        Returns an MS Graph `drive` [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/drive
        """
        resp = self._request(HTTPMethod.GET, url=f"{self._graph_base}/sites/{site_id}/drives")
        if resp.status_code == HTTPStatus.FORBIDDEN:
            raise SiteNotFoundError() from None
        resp.raise_for_status()

        drive_id = next(
            (d.get("id") for d in resp.json().get("value", []) if d.get("name") == library_name),
            None,
        )
        if not drive_id:
            raise DriveNotFoundError() from None
        return drive_id

    def _get_drive_item(self, drive_path: str) -> dict:
        """
        Get Drive Item at file path if it exists.

        E.g. to get a file at https://example.sharepoint.com/sites/example/library/folder/sub-folder/file.txt, use
        `drive_path='folder/sub-folder/file.txt'`.

        Returns an MS Graph `driveItem` [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/driveitem
        """
        file_url = f"{self._graph_base}/drives/{self._drive_id}/root:/{drive_path}"
        resp = self._request(HTTPMethod.GET, url=file_url)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise DriveItemNotFoundError() from None
        return resp.json()

    def _get_metadata(self, item_id: str) -> ResourceMetadata | ArtefactMetadata:
        """
        Get list fields for a Drive Item.

        Expected to be specific to the MAGIC Resource Distribution service SharePoint libraries as per the
        `lantern.lib.magic_distribution.models.metadata.ResourceMetadata` or `ArtefactMetadata` typed dicts.

        Returns an MS Graph `fieldValueSet` [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/fieldvalueset
        """
        resp = self._request(
            HTTPMethod.GET, url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/listItem/fields"
        )
        resp.raise_for_status()
        data = resp.json()
        if "artefact_id" in data:
            return cast("ArtefactMetadata", data)
        return cast("ResourceMetadata", data)

    def _set_metadata(self, item_id: str, metadata: ResourceMetadata | ArtefactMetadata) -> None:
        """
        Set required list fields on a Drive item.

        Expected to be specific to the MAGIC Resource Distribution service SharePoint libraries as per the
        `lantern.lib.magic_distribution.models.metadata.ResourceMetadata` or `ArtefactMetadata` typed dicts.
        """
        self._request(
            HTTPMethod.PATCH,
            url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/listItem/fields",
            json=metadata,
        ).raise_for_status()

    def _get_permissions(self, item_id: str) -> list:
        """
        Get current permission applied to a Drive item.

        This includes permissions set by default, including the SharePoint site owners/members/visitors groups and
        site collection admins.

        Returns a list of MS Graph `permission`s [1].

        To check permissions set using `set_permissions()`, look for the optional 'group' property (an `identity` [2])
        inside the Permission.grantedToIdentitiesV2 member (a `sharepointidentityset` [3]). The `id` property of these
        identities should correspond to groups passed to `set_permissions()`.

        [1] https://learn.microsoft.com/en-us/graph/api/resources/permission
        [2] https://learn.microsoft.com/en-us/graph/api/resources/identity
        [3] https://learn.microsoft.com/en-us/graph/api/resources/sharepointidentityset
        """
        resp = self._request(
            HTTPMethod.GET, url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/permissions"
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def _set_permissions(self, item_id: str, groups: set[str]) -> None:
        """
        Grant selected groups read access to a Drive item.

        Checks existing_groups permissions first. Where the item is a folder, access applies to its contents by default.

        Requires a list of group IDs as identifiers [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/identity
        """
        if not groups:
            # Catch when no permissions to assign (SharePoint returns an error if no recipients are provided)
            return

        existing_permissions = self._get_permissions(item_id)
        existing_groups = {
            p["grantedToV2"]["group"]["id"] for p in existing_permissions if "group" in p.get("grantedToV2", {})
        }
        if groups.issubset(existing_groups):
            # All requested groups already have permissions, skip
            return

        self._request(
            HTTPMethod.POST,
            url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/invite",
            json={
                "recipients": [{"objectId": group} for group in groups],
                "requireSignIn": True,
                "sendInvitation": False,
                "roles": ["read"],
            },
        ).raise_for_status()

    def _create_resource_folder(self, resource_id: str, access_groups: set[str], unrestricted: bool) -> None:
        """
        Ensure folder for a resource exists in the Drive (library) root, with required metadata and permissions.

        Where the folder already exists, permissions and metadata are NOT updated (the folder will need recreating).
        """
        check_resp = self._request(
            HTTPMethod.GET, url=f"{self._graph_base}/drives/{self._drive_id}/root:/{resource_id}"
        )
        if check_resp.status_code == HTTPStatus.OK:
            # Already exists
            return

        create_resp = self._request(
            HTTPMethod.POST,
            url=f"{self._graph_base}/drives/{self._drive_id}/root/children",
            json={
                "name": resource_id,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail",
            },
        )
        create_resp.raise_for_status()

        item_id = create_resp.json()["id"]
        metadata = ResourceMetadata(resource_id=resource_id, unrestricted=unrestricted)
        self._set_metadata(item_id=item_id, metadata=metadata)
        self._set_permissions(item_id=item_id, groups=access_groups)

    def _create_sharepoint_artefact(self, drive_item: dict) -> ArtefactSharePointFile:
        """Create SharePoint Artefact from a Drive item and associated list metadata."""
        metadata = cast("ArtefactMetadata", self._get_metadata(drive_item["id"]))
        return ArtefactSharePointFile(drive_item=drive_item, list_metadata=metadata, proxy_base=self._proxy_base)

    def _upload_small_file(self, artefact: ArtefactFile, drive_path: str) -> dict:
        """
        Upload small file using simple upload (for files <= 250MB).

        Returns the uploaded drive item.
        """
        file_url = f"{self._graph_base}/drives/{self._drive_id}/root:/{drive_path}"
        upload_resp = self._request(HTTPMethod.PUT, url=f"{file_url}:/content", timeout=300, data=artefact.data)
        upload_resp.raise_for_status()
        return upload_resp.json()

    def _upload_large_file(self, artefact: ArtefactFile, drive_path: str) -> dict:
        """
        Upload large file using upload session (for files > 250MB).

        Returns the uploaded drive item.
        """
        file_url = f"{self._graph_base}/drives/{self._drive_id}/root:/{drive_path}"

        # Create upload session
        session_resp = self._request(
            HTTPMethod.POST,
            url=f"{file_url}:/createUploadSession",
            json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
        )
        session_resp.raise_for_status()
        upload_url = session_resp.json()["uploadUrl"]

        # Upload file in chunks
        file_size = artefact.size_bytes
        chunk_size = self._upload_chunk_size
        bytes_uploaded = 0

        while bytes_uploaded < file_size:
            chunk_end = min(bytes_uploaded + chunk_size, file_size)
            chunk_data = artefact.data[bytes_uploaded:chunk_end]

            headers = {
                "Content-Length": str(len(chunk_data)),
                "Content-Range": f"bytes {bytes_uploaded}-{chunk_end - 1}/{file_size}",
            }
            chunk_resp = self._request(HTTPMethod.PUT, url=upload_url, headers=headers, timeout=300, data=chunk_data)
            chunk_resp.raise_for_status()
            bytes_uploaded = chunk_end

            # Final chunk returns the drive item
            if bytes_uploaded == file_size:
                return chunk_resp.json()

        msg = "Upload session completed but no drive item was returned"
        raise RuntimeError(msg)

    def _upload_artefact(self, artefact: ArtefactFile, unrestricted: bool) -> ArtefactSharePointFile:
        """
        Upload a file artefact to an existing resource folder within Drive and set required metadata.

        Uses simple upload for files <= 250MB, upload sessions for larger files.

        Returns the uploaded artefact with an access URL.

        Will crash where the resource directory does not exist. Call `_create_resource_folder()` first or ideally
        `deosit_artefact()` for an e2e upload.
        """
        drive_path = f"{artefact.resource_id}/{artefact.name}"

        # Check if file already exists with matching hash
        with contextlib.suppress(DriveItemNotFoundError):
            existing_item = self._get_drive_item(drive_path)
            if existing_item and existing_item["file"]["hashes"]["quickXorHash"] == artefact.quickxor:
                # File already exists with matching hash, skip upload
                return self._create_sharepoint_artefact(drive_item=existing_item)

        # Choose upload method based on file size
        if artefact.size_bytes <= self._max_simple_upload_size:
            drive_item = self._upload_small_file(artefact=artefact, drive_path=drive_path)
        else:
            drive_item = self._upload_large_file(artefact=artefact, drive_path=drive_path)

        # Verify hash
        if drive_item["file"]["hashes"]["quickXorHash"] != artefact.quickxor:
            raise ArtefactHashMismatchError() from None

        # Set metadata
        item_id = drive_item["id"]
        self._set_metadata(
            item_id=item_id,
            metadata={**artefact.deposit_metadata, "unrestricted": unrestricted},
        )

        return self._create_sharepoint_artefact(drive_item=drive_item)

    def deposit_artefact(
        self, artefact: ArtefactFile, access_groups: set[str], unrestricted: bool
    ) -> ArtefactSharePointFile:
        """Upload a file artefact within a resource folder."""
        if not unrestricted and not access_groups:
            msg = "Access groups may not be empty unless unrestricted (to avoid artefacts with no permissions)."
            raise ArtefactPermissionsNotSupportedError(msg) from None

        self._create_resource_folder(
            resource_id=artefact.resource_id, access_groups=access_groups, unrestricted=unrestricted
        )
        return self._upload_artefact(artefact=artefact, unrestricted=unrestricted)
