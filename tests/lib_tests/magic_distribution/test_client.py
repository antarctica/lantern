import csv
from typing import TYPE_CHECKING
from unittest.mock import PropertyMock

import pytest

from lantern.lib.magic_distribution.client import (
    ArtefactHashMismatchError,
    ArtefactPermissionsNotSupportedError,
    DriveItemNotFoundError,
    DriveNotFoundError,
    MagicResourceDistributionClient,
    SiteNotFoundError,
)
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel
from lantern.lib.magic_distribution.models.artefact import (
    ArtefactLocalFile,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.models.metadata import ArtefactMetadata

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


class TestMagicResourceDistributionClient:
    """Test MAGIC Resource Distribution service SharePoint client."""

    def test_init(self):
        """Can initialise client with required parameters."""
        client = MagicResourceDistributionClient(
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id="x",
            library_name="x",
        )
        assert isinstance(client, MagicResourceDistributionClient)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_graph_token(self):
        """Can get an MS Graph access token."""
        client = MagicResourceDistributionClient(
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id="x",
            library_name="x",
        )

        token = client._graph_token
        assert len(token) > 0

    @pytest.mark.cov()
    def test_drive_id(self, mocker: MockerFixture):
        """Can lookup drive ID for configured library and site."""
        client = MagicResourceDistributionClient(
            tenant_id="x",
            app_client_id="x",
            app_client_secret="x",  # noqa: S106
            site_id="x",
            library_name="x",
        )
        mocker.patch.object(type(client), "_graph_token", new_callable=PropertyMock, return_value="x")
        mocker.patch.object(type(client), "_get_drive_id", return_value="x")

        assert client._drive_id == "x"

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("site_id", ["x", "missing"])
    @pytest.mark.parametrize("library_name", ["ok", "unknown"])
    def test_get_drive_id(self, mocker: MockerFixture, site_id: str, library_name: str):
        """Can get the MS Graph Drive ID for a SharePoint library within a site if it or the site exists."""
        client = MagicResourceDistributionClient(
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
    @pytest.mark.parametrize("drive_path", [None, "path/ok", "path/unknown"])
    @pytest.mark.parametrize(
        "drive_url",
        [
            None,
            "https://x.sharepoint.com/sites/x/Main/x/file.ext",
            "https://x.sharepoint.com/sites/x/Main/x/unknown",
        ],
    )
    def test_get_drive_item(
        self, fx_lib_magic_dist_client: MagicResourceDistributionClient, drive_path: str | None, drive_url: str | None
    ):
        """Can get an MS Graph Drive Item within a given Drive at a given path, if it exists."""
        if drive_path and drive_url:
            with pytest.raises(ValueError, match=r"Drive path or URL required, both supplied."):
                fx_lib_magic_dist_client._get_drive_item(drive_path=drive_path, drive_url=drive_url)
            return
        if not drive_path and not drive_url:
            with pytest.raises(ValueError, match=r"Drive path or URL required, neither supplied."):
                fx_lib_magic_dist_client._get_drive_item(drive_path=drive_path, drive_url=drive_url)
            return

        if drive_path == "path/unknown" or drive_url == "https://x.sharepoint.com/sites/x/Main/x/unknown":
            with pytest.raises(DriveItemNotFoundError):
                fx_lib_magic_dist_client._get_drive_item(drive_path=drive_path, drive_url=drive_url)
            return

        drive_id = fx_lib_magic_dist_client._get_drive_item(drive_path=drive_path, drive_url=drive_url)
        assert len(drive_id) > 0

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
        """Can set artefact metadata for a file as MS Graph list columns associated with a Drive Item."""
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
    @pytest.mark.parametrize("state", ["new", "existing", "updated", "hash-miss", "broken-large"])
    def test_upload_artefact(
        self,
        tmp_path: Path,
        fx_lib_magic_dist_client: MagicResourceDistributionClient,
        fx_lib_artefact_file: ArtefactLocalFile,
        state: str,
    ):
        """
        Can upload big and small files as Drive Items where they don't exist or match hash value.

        Implicitly tests `_upload_small_file()` and `_upload_big_file()` ('updated') methods.

        'hash_miss' checks an edge case where the remote file has a different hash to the original (see cassette).
        'broken-large' checks an edge case where a chunked large upload fails to upload an empty file.
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

        assert fx_lib_magic_dist_client.lookup_artefact(url="x") == fx_lib_artefact_sharepoint

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
