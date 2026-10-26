from __future__ import annotations

import contextlib
from base64 import urlsafe_b64encode
from functools import cached_property
from http import HTTPMethod, HTTPStatus
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, cast, overload

import requests
from requests.exceptions import HTTPError

from lantern.lib.magic_distribution.models.artefact import (
    ArtefactFile,
    ArtefactLocalFile,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.types import ArtefactMetadata, ResourceMetadata
from lantern.lib.magic_distribution.utils import HTTPBearerTokenAuth

if TYPE_CHECKING:
    import logging
    from pathlib import Path


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


class DuplicateArtefactError(Exception):
    """
    Raised when an artefact ID is already in use.

    Based on artefact ID violating unique metadata constraint.
    """

    def __init__(self, artefact_id: str) -> None:
        self.artefact_id = artefact_id
        super().__init__(f"Artefact with {artefact_id!r} already exists.")


class MagicResourceDistributionClient:
    """
    Lightweight client to deposit and manage artefacts in the MAGIC Resource Distribution SharePoint Online site.

    Supports:
    - creating directories
    - uploading files (via an upload session if needed)
    - setting required list metadata and permissions
    - fetching file information and contents

    Does not support updating existing artefacts (see `docs/libraries.md` for other limitations).

    Uses the MS Graph API directly to avoid the complexity and overhead of a full MS Graph SDK.

    List metadata is specific to MAGIC Resource Distribution libraries (as per the MagicDistributionMetadata typed dict).

    Requires an Entra app registration with the `Sites.Selected` permission configured for the relevant SharePoint site.
    """

    def __init__(
        self,
        logger: logging.Logger,
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

        self._logger = logger
        self._tenant_id = tenant_id
        self._client_id = app_client_id
        self._client_secret = app_client_secret
        self._site_id = site_id
        self._library_name = library_name
        self._proxy_base = proxy_url

    @cached_property
    def _graph_token(self) -> str:
        """
        Get Microsoft Graph access token.

        Using OAuth client credentials flow via AuthLib. Access token is cached for the lifetime of the client.
        """
        self._logger.info("Acquiring token for Entra app registration %s", self._client_id)

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
        self._logger.info("Token acquired")
        return response.json()["access_token"]

    @cached_property
    def _drive_id(self) -> str:
        """Get Microsoft Graph Drive ID."""
        self._logger.info("Getting drive ID for library '%s' in site %s", self._library_name, self._site_id)
        drive_id = self._get_drive_id(site_id=self._site_id, library_name=self._library_name)
        self._logger.info("Drive ID: %s", drive_id)
        return drive_id

    def _request(self, method: HTTPMethod, url: str, **kwargs: Any) -> requests.Response:
        """Make HTTP request with default timeout, header for bearer token and retry logic via session."""
        timeout = kwargs.pop("timeout", self._timeout)
        headers = kwargs.pop("headers", {"Accept": "application/json"})
        self._logger.debug("Calling [%s] %s", method.value, url)
        return requests.request(
            method.value,
            url,
            headers=headers,
            timeout=timeout,
            auth=HTTPBearerTokenAuth(token=self._graph_token),
            **kwargs,
        )

    def _get_drive_id(self, site_id: str, library_name: str) -> str:
        """
        Get Microsoft Graph Drive ID for a SharePoint document library.

        Returns an MS Graph `drive` [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/site#relationships
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

    @overload
    def _get_drive_item(self, *, item_id: str, item_path: None = None, item_url: None = None) -> dict: ...

    @overload
    def _get_drive_item(self, *, item_id: None = None, item_path: str, item_url: None = None) -> dict: ...

    @overload
    def _get_drive_item(self, *, item_id: None = None, item_path: None = None, item_url: str) -> dict: ...

    def _get_drive_item(
        self, *, item_id: str | None = None, item_path: str | None = None, item_url: str | None = None
    ) -> dict:
        """
        Get Drive Item by ID, file path or access URL if it exists.

        E.g. for a known drive item, use `item_id='x'`

        E.g. for https://example.sharepoint.com/sites/example/library/folder/sub-folder/file.txt, use either:
        - `item_path='folder/sub-folder/file.txt'`
        - `item_url='https://example.sharepoint.com/sites/example/library/folder/sub-folder/file.txt'`

        The Graph `/shares` endpoint [2] is used where a `drive_url` is used. This supports both sharing
        ('https://x.sharepoint.com/:b:/r/sites/...') and direct ('https://x.sharepoint.com/sites/...') links.

        Returns an MS Graph `driveItem` [1].

        Note: Though the `/shares/` endpoint is not tied to a specific Drive, the `_get_metadata()` method is.

        [1] https://learn.microsoft.com/en-us/graph/api/resources/driveitem
        [2] https://learn.microsoft.com/en-us/graph/api/shares-get
        """
        if sum(value is not None for value in (item_id, item_path, item_url)) > 1:
            msg = "Only one of Drive Item ID, path or URL allowed, multiple supplied."
            raise ValueError(msg) from None

        if item_id:
            graph_url = f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}"
            self._logger.info("Fetching drive item info by ID %s", item_id)
        elif item_path:
            graph_url = f"{self._graph_base}/drives/{self._drive_id}/root:/{item_path}"
            self._logger.info("Fetching drive item info by path %s", item_path)
        elif item_url:
            share_url = "u!" + urlsafe_b64encode(item_url.encode("utf-8")).decode().rstrip("=")
            graph_url = f"{self._graph_base}/shares/{share_url}/driveItem"
            self._logger.info("Fetching drive item info by URL %s", item_url)
            self._logger.debug("Encoded sharing URL: %s", share_url)
        else:
            msg = "Drive Item ID, path or URL required, none supplied."
            raise ValueError(msg) from None

        resp = self._request(HTTPMethod.GET, url=graph_url)
        if resp.status_code == HTTPStatus.NOT_FOUND or (item_url and resp.status_code == HTTPStatus.FORBIDDEN):
            raise DriveItemNotFoundError() from None
        return resp.json()

    def _delete_drive_item(self, item_id: str) -> None:
        """
        Delete Microsoft Graph Drive Item by ID.

        Skips recycling bin soft delete.

        [1] https://learn.microsoft.com/en-us/graph/api/driveitem-permanentdelete
        """
        self._logger.info("Permanently deleting drive item: %s", item_id)
        resp = self._request(
            HTTPMethod.POST, url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/permanentDelete"
        )
        resp.raise_for_status()

    def _get_metadata(self, item_id: str) -> ResourceMetadata | ArtefactMetadata:
        """
        Get list fields for a Drive Item.

        Limited to configured Drive, which is expected to be a MAGIC Resource Distribution service SharePoint library,
        and include associated list fields as per the `lantern.lib.magic_distribution.models.metadata.ResourceMetadata`
        or `ArtefactMetadata` typed dicts.

        Returns an MS Graph `fieldValueSet` [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/fieldvalueset
        """
        self._logger.info("Fetching metadata for drive item: %s", item_id)
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
        Set required list fields on a Drive Item.

        Values are expected to be specific to the MAGIC Resource Distribution service SharePoint libraries, as per the
        `lantern.lib.magic_distribution.types.ResourceMetadata` or `ArtefactMetadata` typed dicts.

        Raises a `DuplicateArtefactError` where the `artefact_id` field value is already in use.
        """
        self._logger.info("Setting metadata for drive item: %s", item_id)
        self._logger.debug(metadata)
        try:
            self._request(
                HTTPMethod.PATCH,
                url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/listItem/fields",
                json=metadata,
            ).raise_for_status()
        except HTTPError as e:
            try:
                body = e.response.json() if e.response is not None else {}
            except JSONDecodeError as e2:
                raise e2 from e

            error = body.get("error") if isinstance(body, dict) else None
            message = error.get("message") if isinstance(error, dict) else None
            if message == "One or more fields with unique constraints already has the provided value.":
                # Artefact ID is the only unique constraint, so metadata is assumed to be ArtefactMetadata.
                self._logger.warning("Duplicate artefact ID: %s", metadata.get("artefact_id"))
                raise DuplicateArtefactError(artefact_id=metadata["artefact_id"]) from e  # ty: ignore[invalid-key]
            raise

    def _get_permissions(self, item_id: str) -> list:
        """
        Get permissions currently applied to a Drive Item.

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
        self._logger.info("Getting permissions for drive item: %s", item_id)
        resp = self._request(
            HTTPMethod.GET, url=f"{self._graph_base}/drives/{self._drive_id}/items/{item_id}/permissions"
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def _set_permissions(self, item_id: str, groups: set[str]) -> None:
        """
        Grant selected groups read access to a Drive Item.

        Checks existing group permissions first. Where the item is a folder, access applies to its contents by default.

        Requires a list of group IDs as identifiers [1].

        [1] https://learn.microsoft.com/en-us/graph/api/resources/identity
        """
        self._logger.info("Setting group permissions for drive item: %s", item_id)
        self._logger.debug(groups)
        if not groups:
            # catch when no permissions to assign (SharePoint returns an error if no recipients are provided)
            self._logger.error("Empty groups set provided which would trigger a SharePoint error.")
            return

        existing_permissions = self._get_permissions(item_id)
        existing_groups = {
            p["grantedToV2"]["group"]["id"] for p in existing_permissions if "group" in p.get("grantedToV2", {})
        }
        if groups.issubset(existing_groups):
            # all requested groups already have permission, skip
            self._logger.info("Existing permissions include target groups, no changes needed.")
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
        self._logger.info("Ensuring a folder exists for resource ID: %s", resource_id)
        check_resp = self._request(
            HTTPMethod.GET, url=f"{self._graph_base}/drives/{self._drive_id}/root:/{resource_id}"
        )
        if check_resp.status_code == HTTPStatus.OK:
            # Already exists
            self._logger.info("Folder exists for resource ID: %s", resource_id)
            return

        self._logger.info("Creating folder for resource ID: %s", resource_id)
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
        """Create SharePoint Artefact from a Drive Item and associated List Fields."""
        self._logger.info("Constructing artefact for Drive Item: %s", drive_item)
        metadata = cast("ArtefactMetadata", self._get_metadata(drive_item["id"]))
        return ArtefactSharePointFile(drive_item=drive_item, list_metadata=metadata, proxy_base=self._proxy_base)

    def _upload_small_file(self, artefact: ArtefactFile, drive_path: str) -> dict:
        """
        Upload small file using simple upload (for files <= 250MB).

        Returns the uploaded drive item.
        """
        self._logger.info("Uploading artefact file '%s' directly", artefact.name)
        file_url = f"{self._graph_base}/drives/{self._drive_id}/root:/{drive_path}"
        upload_resp = self._request(HTTPMethod.PUT, url=f"{file_url}:/content", timeout=300, data=artefact.data)
        upload_resp.raise_for_status()
        return upload_resp.json()

    def _upload_large_file(self, artefact: ArtefactFile, drive_path: str) -> dict:
        """
        Upload large file using upload session (for files > 250MB).

        Returns the uploaded drive item.
        """
        self._logger.info("Uploading artefact file '%s' via chunked session", artefact.name)
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
            self._logger.debug("Uploading chunk %s/%s", bytes_uploaded, file_size)

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
        self._logger.info("Ensuring artefact file '%s' is uploaded", artefact.name)
        drive_path = f"{artefact.resource_id}/{artefact.name}"

        # Check if file already exists with matching name and hash
        with contextlib.suppress(DriveItemNotFoundError):
            existing_item = self._get_drive_item(item_path=drive_path)
            if existing_item and existing_item["file"]["hashes"]["quickXorHash"] == artefact.quickxor:
                self._logger.info("Artefact with matching hash already exists, skipping")
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
        try:
            self._set_metadata(
                item_id=item_id,
                metadata={**artefact.deposit_metadata, "unrestricted": unrestricted},
            )
        except DuplicateArtefactError as e:
            # Rollback upload for a file with the same content (and therefore hash and therefore artefact ID) as an
            # existing file (i.e. same content different names), as this will fail the unique artefact ID constraint.
            self._logger.exception("Cannot set duplicate artefact ID metadata, rolling back upload", exc_info=e)
            self._delete_drive_item(item_id)
            raise

        return self._create_sharepoint_artefact(drive_item=drive_item)

    def deposit_artefact(
        self, artefact: ArtefactFile, access_groups: set[str], unrestricted: bool
    ) -> ArtefactSharePointFile:
        """Upload a file artefact within a resource folder."""
        self._logger.info("Depositing artefact '%s'", artefact.artefact_id)
        if not unrestricted and not access_groups:
            msg = "Access groups may not be empty unless unrestricted (to avoid artefacts with no permissions)."
            raise ArtefactPermissionsNotSupportedError(msg) from None

        self._create_resource_folder(
            resource_id=artefact.resource_id, access_groups=access_groups, unrestricted=unrestricted
        )
        return self._upload_artefact(artefact=artefact, unrestricted=unrestricted)

    def lookup_artefact(self, url: str) -> ArtefactSharePointFile:
        """Get an artefact based on a direct (non-proxied) URL."""
        self._logger.info("Finding artefact available at URL '%s'", url)
        return self._create_sharepoint_artefact(drive_item=self._get_drive_item(item_url=url))

    def get_resource_artefacts(self, resource_id: str) -> list[ArtefactSharePointFile]:
        """Get all artefacts for a resource."""
        self._logger.info("Fetching any artefacts for resource ID '%s'", resource_id)
        resp = self._request(
            HTTPMethod.GET,
            url=f"{self._graph_base}/drives/{self._drive_id}/root:/{resource_id}:/children",
        )
        resp.raise_for_status()
        return [
            self._create_sharepoint_artefact(drive_item=item) for item in resp.json().get("value", []) if "file" in item
        ]

    def download_artefact(self, artefact: ArtefactSharePointFile, path: Path) -> ArtefactLocalFile:
        """Download an artefact to a local path."""
        self._logger.info("Downloading contents of artefact '%s' to '%s'", artefact.artefact_id, path.resolve())
        with self._request(HTTPMethod.GET, url=artefact.presigned_url, stream=True) as resp:
            resp.raise_for_status()
            with path.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        return ArtefactLocalFile(resource_id=artefact.resource_id, artefact_path=path)
