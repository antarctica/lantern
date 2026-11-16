from __future__ import annotations

from base64 import urlsafe_b64decode
from urllib.parse import parse_qs, urlparse

import pytest

from lantern.lib.magic_distribution.formats import ArtefactFormatLabel, ArtefactFormats, ArtefactFormatUnknownError
from lantern.lib.magic_distribution.sharepoint.models.artefact import ArtefactSharePointFile
from lantern.lib.magic_distribution.sharepoint.models.types import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.common import Contact
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode


class TestArtefactSharePointFile:
    """Test remote SharePoint hosted file Artefact class."""

    def test_init(self):
        """Can create a SharePoint hosted file artefact."""
        expected_str = "x"
        expected_size = 206
        expected_quickxor = "sEya4uW4DwER4+icrInuSUYOsRI="
        expected_sha256 = "49e6612e97cf7156b6a14577f06857d4450ac1a024fa3e3ed4a35bcc2982a320"
        expected_fmt = ArtefactFormats.get_by_label(ArtefactFormatLabel.CSV)
        expected_url = f"{expected_str}?sha256={expected_sha256}&quickxor={expected_quickxor.replace('=', '%3D').replace('+', '%2B')}"

        artefact = ArtefactSharePointFile(
            drive_item={
                "id": "123",
                "name": expected_str,
                "file": {"hashes": {"quickXorHash": expected_quickxor}},
                "size": expected_size,
                "webUrl": expected_str,
                "@microsoft.graph.downloadUrl": expected_str,
            },
            list_metadata=ArtefactMetadata(
                resource_id=expected_str,
                artefact_id=expected_str,
                artefact_fmt="CSV",
                artefact_sha256=expected_sha256,
                unrestricted=False,
            ),
        )

        assert (
            repr(artefact)
            == f"<ArtefactSpFile: x (driveItem: 123), {expected_fmt.label.name}, {expected_size} bytes, sha256: {expected_sha256}>"
        )
        assert artefact.resource_id == expected_str
        assert artefact.artefact_id == expected_str
        assert artefact.name == expected_str
        assert artefact.format == expected_fmt
        assert artefact.size_bytes == expected_size
        assert artefact.quickxor == expected_quickxor
        assert artefact.sha256 == expected_sha256
        assert artefact.presigned_url == expected_str
        assert artefact.url == expected_url
        assert artefact.validate_format() is None

        # getting data isn't supported
        with pytest.raises(NotImplementedError):
            _ = artefact.data

    @pytest.mark.cov()
    def test_invalid_list_meta(self):
        """Cannot create artefact without required user list metadata."""
        with pytest.raises(KeyError):
            # noinspection argument-list
            _ = ArtefactSharePointFile(
                drive_item={
                    "id": "123",
                    "name": "x",
                    "file": {"hashes": {"quickXorHash": "x"}},
                    "size": "x",
                    "webUrl": "x",
                },
                list_metadata=ArtefactMetadata(
                    resource_id="x",
                    # no artefact_id
                    artefact_fmt="CSV",
                    artefact_sha256="x",
                    unrestricted=False,
                ),
            )

    @pytest.mark.parametrize("artefact_fmt", ["INVALID", "", None])
    def test_unsupported(self, artefact_fmt: str | None):
        """Cannot create a valid SharePoint hosted file artefact for an unsupported or missing format."""
        artefact = ArtefactSharePointFile(
            drive_item={
                "id": "123",
                "name": "x",
                "file": {"hashes": {"quickXorHash": "x"}},
                "size": "x",
                "webUrl": "x",
            },
            list_metadata=ArtefactMetadata(
                resource_id="x", artefact_id="x", artefact_fmt=artefact_fmt, artefact_sha256="x", unrestricted=False
            ),
        )

        with pytest.raises(ArtefactFormatUnknownError):
            artefact.validate_format()
        with pytest.raises(ArtefactFormatUnknownError):
            _ = artefact.format

    @pytest.mark.parametrize("proxy_base", [None, "https://example.com"])
    @pytest.mark.parametrize("unrestricted", [False, True])
    def test_url(self, proxy_base: str, unrestricted: bool):
        """Can use access proxy for URL if the resource is unrestricted."""
        raw_url = "https://example.com/file.txt?x=x"  # query string included to check values are preserved
        common_query = "sha256=y&quickxor=x"
        expected_url = (
            f"{proxy_base}?{common_query}&url=aHR0cHM6Ly9leGFtcGxlLmNvbS9maWxlLnR4dD94PXg%3D&name=x"
            if proxy_base and unrestricted
            else f"{raw_url}&{common_query}"
        )

        artefact = ArtefactSharePointFile(
            drive_item={
                "id": "123",
                "name": "x",
                "file": {"hashes": {"quickXorHash": "x"}},
                "size": "x",
                "webUrl": raw_url,
            },
            list_metadata=ArtefactMetadata(
                resource_id="x", artefact_id="x", artefact_fmt="CSV", artefact_sha256="y", unrestricted=unrestricted
            ),
            proxy_base=proxy_base,
        )

        assert artefact.url == expected_url
        qs = {k: v[0] for k, v in parse_qs(urlparse(artefact.url).query).items()}
        if proxy_base and unrestricted:
            assert urlsafe_b64decode(qs["url"].encode()).decode() == raw_url

    def test_distribution(self):
        """Can get ISO distribution and component elements based on artefact for item and service if applicable."""
        _format = ArtefactFormats.get_by_label(ArtefactFormatLabel.CSV)
        artefact = ArtefactSharePointFile(
            drive_item={
                "id": "123",
                "name": "x",
                "file": {"hashes": {"quickXorHash": "x"}},
                "size": "x",
                "webUrl": "x",
            },
            list_metadata=ArtefactMetadata(
                resource_id="x",
                artefact_id="x",
                artefact_fmt=_format.label.name,
                artefact_sha256="x",
                unrestricted=False,
            ),
        )

        assert isinstance(artefact.distribution_option, Distribution)
        assert isinstance(artefact.distributor, Contact)
        # distribution_format is part of ArtefactBase
        assert isinstance(artefact.distribution_transfer_opt, TransferOption)

        _online_resource = artefact.distribution_transfer_opt.online_resource
        assert _online_resource.title == _format.label.name
        assert _online_resource.description == _format.description
        assert _online_resource.href == artefact.url
        assert _online_resource.function == OnlineResourceFunctionCode.DOWNLOAD
