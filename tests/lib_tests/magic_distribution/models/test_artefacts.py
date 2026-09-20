from base64 import urlsafe_b64decode
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest

from lantern.lib.magic_distribution.formats import (
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormats,
    ArtefactFormatUnknownError,
)
from lantern.lib.magic_distribution.models.artefact import (
    ArtefactBase,
    ArtefactLocalFile,
    ArtefactServicePlaceholder,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.models.metadata import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.distribution import Format


class FakeArtefact(ArtefactBase):
    """
    Fake artefact class for testing.

    Used to test abstract ArtefactBase.
    """

    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return "x"

    @property
    def format(self) -> ArtefactFormat:
        """Artefact format."""
        return ArtefactFormats.file_formats[0]

    @property
    def name(self) -> str:
        """Artefact name."""
        return "x"

    @property
    def size_bytes(self) -> int | None:
        """Optional artefact size in bytes."""
        return 0

    def validate_format(self) -> None:
        """Check artefact is a supported type."""
        return


class TestArtefactBase:
    """Test abstract Artefact base class via FakeArtefact."""

    def test_init(self):
        """Can create a fake artefact."""
        expected_str = "x"
        expected_dist_fmt = Format(format="CSV", href="https://www.iana.org/assignments/media-types/text/csv")

        artefact = FakeArtefact(resource_id=expected_str)
        artefact_id = UUID(artefact.artefact_id)

        assert artefact_id.version == 5  # noqa: PLR2004
        assert artefact.resource_id == expected_str
        assert artefact.format_label == ArtefactFormatLabel.CSV
        assert artefact.distribution_format == expected_dist_fmt


class TestArtefactService:
    """Test placeholder remote service Artefact class."""

    def test_init(self):
        """Can create a placeholder remote service artefact."""
        expected_str = "x"
        expected_fmt = ArtefactFormats.get_label(ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE)
        artefact = ArtefactServicePlaceholder(
            resource_id=expected_str,
            artefact_name=expected_str,
            artefact_url=expected_str,
            artefact_format=expected_fmt,
        )

        assert artefact._artefact_hash == "eA=="
        assert artefact.format == expected_fmt
        assert artefact.name == expected_str
        assert artefact.size_bytes is None

        with pytest.raises(NotImplementedError):
            artefact.validate_format()


class TestArtefactLocalFile:
    """Test local file Artefact class (and implicitly file artefact abstract class)."""

    artefacts_path = Path(__file__).parent.parent.parent.parent / "resources" / "artefacts"

    def test_init(self):
        """Can create a local file artefact."""
        expected_str = "x"
        expected_name = "sample.csv"
        expected_size = 206
        expected_fmt = ArtefactFormats.get_label(ArtefactFormatLabel.CSV)
        expected_deposit_meta = ArtefactMetadata(
            resource_id=expected_str, artefact_id=None, artefact_fmt=expected_fmt.label.name, unrestricted=False
        )
        artefact = ArtefactLocalFile(
            resource_id=expected_str, artefact_path=self.artefacts_path / "csv" / expected_name
        )
        expected_deposit_meta["artefact_id"] = artefact.artefact_id

        # from ArtefactFile
        assert artefact.quickxor == "sEya4uW4DwER4+icrInuSUYOsRI="
        assert artefact.deposit_metadata == expected_deposit_meta

        # ArtefactLocalFile
        assert repr(artefact) == f"<ArtefactLocal: {expected_name}, {expected_fmt.label.name}, {expected_size} bytes>"
        assert artefact.format == expected_fmt
        assert artefact.name == expected_name
        assert isinstance(artefact.data, bytes)
        assert artefact.size_bytes == expected_size
        assert artefact.validate_format() is None

    def test_unsupported(self):
        """Cannot create a valid local file artefact with an unsupported format."""
        expected_size = 25
        artefact = ArtefactLocalFile(resource_id="x", artefact_path=self.artefacts_path / "_unsupported" / "sample.x")

        # from ArtefactFile
        assert artefact.quickxor == "VH6vNOkIy6i6d5q1NAkZQDCHMLQ="  # not dependent on format

        # ArtefactLocalFile
        with pytest.raises(ArtefactFormatUnknownError):
            artefact.validate_format()
        with pytest.raises(ArtefactFormatUnknownError):
            repr(artefact)
        with pytest.raises(ArtefactFormatUnknownError):
            _ = artefact.format
        assert artefact.size_bytes == expected_size  # not dependent on format


class TestArtefactSharePointFile:
    """Test remote SharePoint hosted file Artefact class."""

    def test_init(self):
        """Can create a SharePoint hosted file artefact."""
        expected_str = "x"
        expected_size = 206
        expected_hash = "sEya4uW4DwER4+icrInuSUYOsRI="
        expected_fmt = ArtefactFormats.get_label(ArtefactFormatLabel.CSV)

        artefact = ArtefactSharePointFile(
            drive_item={
                "id": "123",
                "name": expected_str,
                "file": {"hashes": {"quickXorHash": expected_hash}},
                "size": expected_size,
                "webUrl": expected_str,
            },
            list_metadata=ArtefactMetadata(
                resource_id=expected_str,
                artefact_id=expected_str,
                artefact_fmt="CSV",
                unrestricted=False,
            ),
        )

        assert (
            repr(artefact) == f"<ArtefactSpFile: x (driveItem: 123), {expected_fmt.label.name}, {expected_size} bytes>"
        )
        assert artefact.resource_id == expected_str
        assert artefact.artefact_id == expected_str
        assert artefact.name == expected_str
        assert artefact.format == expected_fmt
        assert artefact.size_bytes == expected_size
        assert artefact.quickxor == expected_hash
        assert artefact.url == expected_str
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
                resource_id="x", artefact_id="x", artefact_fmt=artefact_fmt, unrestricted=False
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
        raw_url = "https://example.com/file.txt"
        encoded_url = f"{proxy_base}?url=aHR0cHM6Ly9leGFtcGxlLmNvbS9maWxlLnR4dA==" if proxy_base else None
        expected_url = encoded_url if proxy_base and unrestricted else raw_url

        artefact = ArtefactSharePointFile(
            drive_item={
                "id": "123",
                "name": "x",
                "file": {"hashes": {"quickXorHash": "x"}},
                "size": "x",
                "webUrl": raw_url,
            },
            list_metadata=ArtefactMetadata(
                resource_id="x", artefact_id="x", artefact_fmt="CSV", unrestricted=unrestricted
            ),
            proxy_base=proxy_base,
        )

        assert artefact.url == expected_url
        if proxy_base and unrestricted:
            assert urlsafe_b64decode(parse_qs(urlparse(artefact.url).query)["url"][0].encode()).decode() == raw_url
