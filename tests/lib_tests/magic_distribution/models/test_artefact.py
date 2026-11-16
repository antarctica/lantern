from __future__ import annotations

from pathlib import Path
from typing import Any
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
    ArtefactFile,
    ArtefactLocalFile,
    ArtefactService,
)
from lantern.lib.magic_distribution.sharepoint.models.types import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.distribution import Format


class FakeArtefactBase(ArtefactBase):
    """
    Fake artefact class for testing.

    Used to test abstract Artefact classes.
    """

    def __init__(self, resource_id: str, format_: ArtefactFormat, **kwargs: Any) -> None:
        # noinspection argument-list
        super().__init__(resource_id=resource_id, **kwargs)
        self._format = format_

    @property
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return "x"

    @property
    def format(self) -> ArtefactFormat:
        """Artefact format."""
        return self._format

    @property
    def name(self) -> str:
        """Artefact name."""
        return "x"

    def validate_format(self) -> None:
        """Check artefact is a supported type."""
        return


class FakeFileArtefact(FakeArtefactBase, ArtefactFile):
    """
    Fake artefact class for testing.

    Used to test abstract ArtefactFile.
    """

    @property
    def data(self) -> bytes:
        """Artefact data."""
        return b"x"

    @property
    def size_bytes(self) -> int:
        """Artefact data."""
        return 0


class FakeServiceArtefact(ArtefactService):
    """
    Fake artefact class for testing.

    Used to test abstract ArtefactService.
    """

    @property
    def format(self) -> ArtefactFormat:
        """..."""
        return ArtefactFormats.service_formats[0]

    def validate_format(self) -> None:
        """..."""
        return


class TestArtefactBase:
    """Test abstract Artefact base class via FakeArtefact."""

    def test_init(self):
        """Can create a fake artefact."""
        expected_str = "x"
        expected_dist_fmt = Format(format="CSV", href="https://www.iana.org/assignments/media-types/text/csv")

        artefact = FakeArtefactBase(resource_id=expected_str, format_=ArtefactFormats.file_formats[0])
        artefact_id = UUID(artefact.artefact_id)

        assert artefact_id.version == 5  # noqa: PLR2004
        assert artefact.resource_id == expected_str
        assert artefact.format_label == ArtefactFormatLabel.CSV
        assert artefact.distribution_format == expected_dist_fmt


class TestArtefactFile:
    """Test abstract ArtefactFile base class via FakeFileArtefact."""

    def test_init(self):
        """Can create a fake artefact."""
        expected_resource_id = "x"
        expected_artefact_id = "87acf077-d25f-5307-afb9-05488629e285"
        expected_sha256 = "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"
        expected_deposit_meta = ArtefactMetadata(
            resource_id=expected_resource_id,
            artefact_id=expected_artefact_id,
            artefact_fmt=ArtefactFormats.file_formats[0].label.name,
            artefact_sha256=expected_sha256,
            unrestricted=False,
        )

        artefact = FakeFileArtefact(resource_id=expected_resource_id, format_=ArtefactFormats.file_formats[0])
        assert artefact.artefact_id == expected_artefact_id  # taken on trust
        assert artefact.quickxor == "eAAAAAAAAAAAAAAAAQAAAAAAAAA="  # taken on trust
        assert artefact.sha256 == expected_sha256  # taken on trust
        assert artefact.deposit_metadata == expected_deposit_meta


class TestArtefactLocalFile:
    """Test local file Artefact class (and implicitly file artefact abstract class)."""

    artefacts_path = Path(__file__).parent.parent.parent.parent / "resources" / "artefacts"

    def test_init(self):
        """Can create a local file artefact."""
        expected_str = "x"
        expected_name = "sample.csv"
        expected_size = 206
        expected_fmt = ArtefactFormats.get_by_label(ArtefactFormatLabel.CSV)
        expected_sha256 = "49e6612e97cf7156b6a14577f06857d4450ac1a024fa3e3ed4a35bcc2982a320"

        artefact = ArtefactLocalFile(
            resource_id=expected_str, artefact_path=self.artefacts_path / "csv" / expected_name
        )

        # from ArtefactFile (mini-integration test)
        assert artefact.quickxor == "sEya4uW4DwER4+icrInuSUYOsRI="  # taken on trust
        assert artefact.sha256 == expected_sha256  # verified against manual `sha256sum`

        # ArtefactLocalFile
        assert (
            repr(artefact)
            == f"<ArtefactLocal: {expected_name}, {expected_fmt.label.name}, {expected_size} bytes, sha256: {expected_sha256}>"
        )
        assert artefact.format == expected_fmt
        assert artefact.name == expected_name
        assert isinstance(artefact.data, bytes)
        assert artefact.size_bytes == expected_size
        assert artefact.validate_format() is None

    def test_unsupported(self):
        """Cannot create a valid local file artefact with an unsupported format."""
        expected_size = 25

        artefact = ArtefactLocalFile(resource_id="x", artefact_path=self.artefacts_path / "_unsupported" / "sample.x")
        with pytest.raises(ArtefactFormatUnknownError):
            artefact.validate_format()
        with pytest.raises(ArtefactFormatUnknownError):
            repr(artefact)
        with pytest.raises(ArtefactFormatUnknownError):
            _ = artefact.format
        assert artefact.size_bytes == expected_size  # not dependent on format


class TestArtefactService:
    """Test abstract Artefact base class via FakeServiceArtefact."""

    def test_init(self):
        """Can create a service artefact."""
        expected_str = "x"
        expected_url = "https://x.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
        expected_fmt = ArtefactFormats.service_formats[0]
        artefact = FakeServiceArtefact(
            resource_id="x",
            artefact_name=expected_str,
            artefact_url=expected_url,
        )

        assert artefact.artefact_id == "863d7dd2-62d7-5ded-b48c-a169c80a2644"  # taken on trust
        assert artefact.name == expected_str
        assert artefact.format == expected_fmt
        assert artefact.validate_format() is None
