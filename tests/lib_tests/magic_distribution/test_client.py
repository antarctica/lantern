from __future__ import annotations

import csv
from http import HTTPMethod, HTTPStatus
from json import JSONDecodeError
from typing import TYPE_CHECKING
from unittest.mock import PropertyMock

import pytest
from pytest_httpserver import HTTPServer, RequestMatcher
from requests.exceptions import HTTPError
from werkzeug import Response

from lantern.lib.magic_distribution.client import (
    ArtefactHashMismatchError,
    ArtefactPermissionsNotSupportedError,
    DriveItemNotFoundError,
    DriveNotFoundError,
    DuplicateArtefactError,
    MagicResourceDistributionClient,
    SiteNotFoundError,
)
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel
from lantern.lib.magic_distribution.models.artefact import (
    ArtefactLocalFile,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.types import ArtefactMetadata

if TYPE_CHECKING:
    import logging
    from pathlib import Path

    from pytest_mock import MockerFixture


class TestMagicResourceDistributionClient:
    """
    Test MAGIC Resource Distribution service SharePoint client.

    Tests for this class largely rely on VCR recordings made for real interactions, adapted to use fake entities.

    To test new methods:
    - configure the test to use real parameters
    - update the `fx_lib_magic_dist_client` fixture to use real credentials and disable mocks
    - record the test (see dev.md#pytest-recording)
    - review the cassette and refactor to use faked values
    - remove the first two exchanges (for getting an access token and drive ID), which are skipped in the mocked fixture
    - restore the fixture and re-run the test to confirm
    """

    def test_init(self, fx_logger: logging.Logger):
        """Can initialise client with required parameters."""
        client = MagicResourceDistributionClient(
            logger=fx_logger,
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id="x",
            library_name="x",
        )
        assert isinstance(client, MagicResourceDistributionClient)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_graph_token(self, fx_logger: logging.Logger):
        """Can get an MS Graph access token."""
        client = MagicResourceDistributionClient(
            logger=fx_logger,
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id="x",
            library_name="x",
        )
        result = client._graph_token
        assert len(result) > 0

    @pytest.mark.cov()
    def test_drive_id(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can lookup drive ID for configured library and site."""
        client = MagicResourceDistributionClient(
            logger=fx_logger,
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id="x",
            library_name="x",
        )
        mocker.patch.object(type(client), "_graph_token", new_callable=PropertyMock, return_value="x")
        mocker.patch.object(type(client), "_get_drive_id", return_value="x")

        assert client._drive_id == "x"

    @pytest.mark.cov()
    def test_request(self, fx_lib_magic_dist_client: MagicResourceDistributionClient, httpserver: HTTPServer):
        """Can attach bearer token and content-type to a request."""
        _route = "/"
        _status = HTTPStatus.ACCEPTED
        httpserver.expect_request(_route).respond_with_response(Response(status=_status))

        fx_lib_magic_dist_client._request(method=HTTPMethod.HEAD, url=httpserver.url_for(_route))

        httpserver.assert_request_made(RequestMatcher(_route))
        for request, response in httpserver.iter_matching_requests(RequestMatcher(_route)):
            assert request.headers["Authorization"] == f"Bearer {fx_lib_magic_dist_client._graph_token}"
            assert request.headers["Accept"] == "application/json"
            assert response.status_code == _status

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("site_id", ["x", "missing"])
    @pytest.mark.parametrize("library_name", ["ok", "unknown"])
    def test_get_drive_id(self, mocker: MockerFixture, fx_logger: logging.Logger, site_id: str, library_name: str):
        """Can get the MS Graph Drive ID for a SharePoint library within a site if it or the site exists."""
        client = MagicResourceDistributionClient(
            logger=fx_logger,
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id=site_id,
            library_name=library_name,
        )
        mocker.patch.object(type(client), "_graph_token", new_callable=PropertyMock, return_value="x")

        if site_id == "missing":
            with pytest.raises(SiteNotFoundError):
                client._get_drive_id(site_id=site_id, library_name=library_name)
            return

        if library_name == "unknown":
            with pytest.raises(DriveNotFoundError):
                client._get_drive_id(site_id=site_id, library_name=library_name)
            return

        drive_id = client._get_drive_id(site_id="x", library_name=library_name)
        assert len(drive_id) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("item_id", [None, "x", "unknown"])
    @pytest.mark.parametrize("item_path", [None, "path/ok", "path/unknown"])
    @pytest.mark.parametrize(
        "item_url",
        [
            None,
            "https://x.sharepoint.com/sites/x/Main/x/file.ext",
            "https://x.sharepoint.com/sites/x/Main/x/unknown",
        ],
    )
    def test_get_drive_item(
        self,
        fx_lib_magic_dist_client: MagicResourceDistributionClient,
        item_id: str | None,
        item_path: str | None,
        item_url: str | None,
    ):
        """Can get an MS Graph Drive Item within a given Drive at a given path, if it exists."""
        if sum(value is not None for value in (item_id, item_path, item_url)) > 1:
            with pytest.raises(ValueError, match=r"Only one of Drive Item ID, path or URL allowed, multiple supplied."):
                fx_lib_magic_dist_client._get_drive_item(item_id=item_id, item_path=item_path, item_url=item_url)
            return
        if not item_id and not item_path and not item_url:
            with pytest.raises(ValueError, match=r"Drive Item ID, path or URL required, none supplied."):
                fx_lib_magic_dist_client._get_drive_item(item_path=item_path, item_url=item_url)
            return

        if (
            item_id == "unknown"
            or item_path == "path/unknown"
            or item_url == "https://x.sharepoint.com/sites/x/Main/x/unknown"
        ):
            with pytest.raises(DriveItemNotFoundError):
                fx_lib_magic_dist_client._get_drive_item(item_id=item_id, item_path=item_path, item_url=item_url)
            return

        drive_id = fx_lib_magic_dist_client._get_drive_item(item_id=item_id, item_path=item_path, item_url=item_url)
        assert len(drive_id) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_delete_drive_item(self, fx_lib_magic_dist_client: MagicResourceDistributionClient):
        """Can delete an MS Graph Drive Item within a given Drive at a given path, if it exists."""
        item_id = "x"

        fx_lib_magic_dist_client._delete_drive_item(item_id=item_id)

        # check
        with pytest.raises(DriveItemNotFoundError):
            fx_lib_magic_dist_client._get_drive_item(item_id=item_id)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("entity", ["resource", "artefact"])
    def test_get_metadata(self, fx_lib_magic_dist_client: MagicResourceDistributionClient, entity: str):
        """Can get artefact metadata for a file from MS Graph list columns associated with a Drive Item."""
        metadata = fx_lib_magic_dist_client._get_metadata(item_id="x")

        assert isinstance(metadata, dict)
        assert "resource_id" in metadata
        if entity == "artefact":
            assert "artefact_id" in metadata
        else:
            assert "artefact_id" not in metadata

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_metadata(self, fx_lib_magic_dist_client: MagicResourceDistributionClient):
        """
        Can set artefact metadata for a file as MS Graph list columns associated with a Drive Item.

        Note: conflict handling (for the artefact_id unique constraint) is tested in `test_upload_artefact` (conflict).
        """
        expected = ArtefactMetadata(
            resource_id="x",
            artefact_id="x",
            artefact_fmt=ArtefactFormatLabel.CSV.name,
            artefact_sha256="x",
            unrestricted=False,
        )
        fx_lib_magic_dist_client._set_metadata(item_id="x", metadata=expected)

        check = fx_lib_magic_dist_client._get_metadata(item_id="x")
        assert check["artefact_fmt"] == expected["artefact_fmt"]

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_metadata_invalid_error(self, fx_lib_magic_dist_client: MagicResourceDistributionClient):
        """Cannot detect unique constraint error if error is not JSON encoded."""
        with pytest.raises(JSONDecodeError):
            fx_lib_magic_dist_client._set_metadata(item_id="x", metadata={})

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_set_metadata_other_error(self, fx_lib_magic_dist_client: MagicResourceDistributionClient):
        """Can pass through non-constraint errors."""
        with pytest.raises(HTTPError):
            fx_lib_magic_dist_client._set_metadata(item_id="x", metadata={})

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_permissions(self, fx_lib_magic_dist_client: MagicResourceDistributionClient):
        """Can get permissions applied to a file from MS Graph for a drive item."""
        permissions = fx_lib_magic_dist_client._get_permissions(item_id="x")
        assert isinstance(permissions, list)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("state", ["none", "existing", "set"])
    def test_set_permissions(self, fx_lib_magic_dist_client: MagicResourceDistributionClient, state: str):
        """Can set permissions to a file using the MS Graph through a drive item."""
        expected = {"y"} if state != "none" else set()
        fx_lib_magic_dist_client._set_permissions(item_id="x", groups=expected)

        if state == "none":
            return
        check = fx_lib_magic_dist_client._get_permissions(item_id="x")
        results = {p["grantedToV2"]["group"]["id"] for p in check if "group" in p.get("grantedToV2", {})}
        assert expected.issubset(results)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("state", ["new", "existing"])
    def test_create_resource_folder(self, fx_lib_magic_dist_client: MagicResourceDistributionClient, state: str):
        """Can ensure a folder exists with required permissions using the MS Graph."""
        fx_lib_magic_dist_client._create_resource_folder(resource_id="x", access_groups={"y"}, unrestricted=False)

    def test_create_sharepoint_artefact(
        self, mocker: MockerFixture, fx_lib_magic_dist_client: MagicResourceDistributionClient
    ):
        """Can create a SharePoint file artefact from a drive item and fetched related list metadata from MS Graph."""
        metadata = ArtefactMetadata(
            resource_id="x", artefact_id="x", artefact_fmt="CSV", artefact_sha256="x", unrestricted=False
        )
        mocker.patch.object(fx_lib_magic_dist_client, "_get_metadata", return_value=metadata)
        drive_item = {
            "id": "123",
            "name": "x",
            "file": {"hashes": {"quickXorHash": "x"}},
            "size": 206,
            "webUrl": "x",
        }

        artefact = fx_lib_magic_dist_client._create_sharepoint_artefact(drive_item=drive_item)
        assert isinstance(artefact, ArtefactSharePointFile)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("state", ["new", "existing", "updated", "hash-miss", "broken-large", "conflict"])
    def test_upload_artefact(
        self,
        tmp_path: Path,
        fx_lib_magic_dist_client: MagicResourceDistributionClient,
        fx_lib_artefact_file: ArtefactLocalFile,
        state: str,
    ):
        """
        Can upload big and small files as Drive Items where they don't exist or match hash value.

        Implicitly tests:
        - `_upload_small_file()` and `_upload_big_file()` ['updated' case] methods
        - `_set_metadata()` where duplicate artefact IDs are encountered ['conflict' case]

        Tests these edge cases:
        - 'hash_miss' where the remote file has a different hash to the original (see cassette)
        - 'broken-large' where a chunked large upload fails to upload an empty file
        - 'conflict' where an artefact with the same hash but different name is uploaded (duplicate artefact ID)
        """
        if state == "updated":
            with fx_lib_artefact_file._artefact.open(mode="a") as f:
                writer = csv.writer(f)
                writer.writerow([11, 18])  # to trigger a different hash

            fx_lib_magic_dist_client._max_simple_upload_size = 40  # to trigger use of upload_big_file()
            fx_lib_magic_dist_client._upload_chunk_size = 40  # to trigger at least two chunks within upload session

        if state == "broken-large":
            fx_lib_artefact_file._artefact.unlink()
            fx_lib_artefact_file._artefact.touch()  # to clear file contents
            fx_lib_magic_dist_client._max_simple_upload_size = -1  # to trigger use of upload_big_file()

            with pytest.raises(RuntimeError):
                _ = fx_lib_magic_dist_client._upload_artefact(artefact=fx_lib_artefact_file, unrestricted=False)
            return

        if state == "hash-miss":
            with pytest.raises(ArtefactHashMismatchError):
                _ = fx_lib_magic_dist_client._upload_artefact(artefact=fx_lib_artefact_file, unrestricted=False)
            return

        if state == "conflict":
            fx_lib_artefact_file._artefact = fx_lib_artefact_file._artefact.rename(
                fx_lib_artefact_file._artefact.with_stem("file-alt")
            )
            with pytest.raises(DuplicateArtefactError):
                _ = fx_lib_magic_dist_client._upload_artefact(artefact=fx_lib_artefact_file, unrestricted=False)
            return

        result = fx_lib_magic_dist_client._upload_artefact(artefact=fx_lib_artefact_file, unrestricted=False)
        # upload includes verifying hash value so no need to check fetching the file.
        assert isinstance(result, ArtefactSharePointFile)

    @pytest.mark.parametrize("groups", [set(), {"x"}])
    @pytest.mark.parametrize("unrestricted", [False, True])
    def test_deposit_artefact(
        self,
        mocker: MockerFixture,
        fx_lib_artefact_file: ArtefactLocalFile,
        fx_lib_artefact_sharepoint: ArtefactSharePointFile,
        fx_lib_magic_dist_client: MagicResourceDistributionClient,
        groups: set[str],
        unrestricted: bool,
    ):
        """Can deposit a file to SharePoint."""
        mocker.patch.object(fx_lib_magic_dist_client, "_create_resource_folder", return_value=None)
        mocker.patch.object(fx_lib_magic_dist_client, "_upload_artefact", return_value=fx_lib_artefact_sharepoint)

        if not unrestricted and not groups:
            with pytest.raises(ArtefactPermissionsNotSupportedError):
                _ = fx_lib_magic_dist_client.deposit_artefact(
                    artefact=fx_lib_artefact_file, access_groups=groups, unrestricted=unrestricted
                )
            return

        result = fx_lib_magic_dist_client.deposit_artefact(
            artefact=fx_lib_artefact_file, access_groups=groups, unrestricted=unrestricted
        )
        assert isinstance(result, ArtefactSharePointFile)

    @pytest.mark.cov()
    def test_lookup_artefact(
        self,
        mocker: MockerFixture,
        fx_lib_artefact_sharepoint: ArtefactSharePointFile,
        fx_lib_magic_dist_client: MagicResourceDistributionClient,
    ):
        """Can get previously deposited artefact by unproxied access URL."""
        mocker.patch.object(
            fx_lib_magic_dist_client, "_create_sharepoint_artefact", return_value=fx_lib_artefact_sharepoint
        )
        mocker.patch.object(fx_lib_magic_dist_client, "_get_drive_item", return_value=None)

        assert fx_lib_magic_dist_client.lookup_artefact(url="x") == fx_lib_artefact_sharepoint

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.cov()
    def test_get_resource_artefacts(self, fx_lib_magic_dist_client: MagicResourceDistributionClient):
        """Can get all artefacts associated with a resource ID."""
        results = fx_lib_magic_dist_client.get_resource_artefacts(resource_id="x")
        assert len(results) > 0
        assert all(isinstance(r, ArtefactSharePointFile) for r in results)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.cov()
    def test_download_artefact(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        fx_lib_artefact_sharepoint: ArtefactSharePointFile,
        fx_lib_magic_dist_client: MagicResourceDistributionClient,
    ):
        """Can get file for a previously deposited artefact."""
        mocker.patch.object(
            type(fx_lib_artefact_sharepoint),
            "presigned_url",
            new_callable=PropertyMock,
            return_value="https://data.bas.ac.uk/static/txt/heartbeat.txt",
        )
        file_path = tmp_path / "file.txt"

        result = fx_lib_magic_dist_client.download_artefact(artefact=fx_lib_artefact_sharepoint, path=file_path)
        assert isinstance(result, ArtefactLocalFile)
        assert result.data == b"badump, badump"
