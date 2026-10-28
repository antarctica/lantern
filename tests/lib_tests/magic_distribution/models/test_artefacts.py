from __future__ import annotations

from base64 import urlsafe_b64decode
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest

from lantern.lib.arcgis.gis.enums import SharingLevel
from lantern.lib.magic_distribution.formats import (
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormats,
    ArtefactFormatUnknownError,
)
from lantern.lib.magic_distribution.models.artefact import (
    ArtefactArcGisService,
    ArtefactBase,
    ArtefactFile,
    ArtefactLocalFile,
    ArtefactService,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.types import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.common import Contact
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode

if TYPE_CHECKING:
    from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem


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
        raw_url = "https://example.com/file.txt"
        common_query = "sha256=y&quickxor=x"
        expected_url = (
            f"{proxy_base}?{common_query}&url=aHR0cHM6Ly9leGFtcGxlLmNvbS9maWxlLnR4dA%3D%3D&name=x"
            if proxy_base and unrestricted
            else f"{raw_url}?{common_query}"
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


class TestArtefactArcGisService:
    """Test ArcGIS based service Artefact class."""

    format_label_item = ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_LAYER).label
    format_label_service = ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE).label

    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_init(self, fx_lib_arcgis_item: ArcGisItem, service_label: ArtefactFormatLabel | None):
        """Can create an ArcGIS item (and service) artefact."""
        artefact = ArtefactArcGisService(
            resource_id="x",
            item=fx_lib_arcgis_item,
            format_label=self.format_label_item,
            format_service_label=service_label,
        )

        assert artefact.name == "x"
        assert artefact._artefact_url == "https://www.maps.arcgis.com/home/item.html?id=x"

    @pytest.mark.cov()
    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_repr(
        self, fx_lib_arcgis_service_artefact: ArtefactArcGisService, service_label: ArtefactFormatLabel | None
    ):
        """Can get string representation."""
        fx_lib_arcgis_service_artefact._format_service_label = service_label
        expected = (
            "<ArtefactArcGiS: x, ArcGIS Feature Layer, https://www.maps.arcgis.com/home/item.html?id=x>"
            if not service_label
            else "<ArtefactArcGiS: x, ArcGIS Feature Layer (ArcGIS Feature Service), https://www.maps.arcgis.com/home/item.html?id=x>"
        )

        assert repr(fx_lib_arcgis_service_artefact) == expected

    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_format(
        self, fx_lib_arcgis_service_artefact: ArtefactArcGisService, service_label: ArtefactFormatLabel | None
    ):
        """Can get artefact format, and by extension format label, for item and service if applicable."""
        fx_lib_arcgis_service_artefact._format_service_label = service_label
        expected_item = ArtefactFormats.get_by_label(self.format_label_item)
        expected_service = ArtefactFormats.get_by_label(self.format_label_service) if service_label else None

        assert fx_lib_arcgis_service_artefact.format == expected_item
        assert fx_lib_arcgis_service_artefact.format_label == self.format_label_item

        assert fx_lib_arcgis_service_artefact.format_service == expected_service
        assert fx_lib_arcgis_service_artefact.format_label_service == service_label

    def test_unsupported_format(self, fx_lib_arcgis_service_artefact: ArtefactArcGisService):
        """Cannot create a valid ArcGIS artefact with an unsupported format."""
        fx_lib_arcgis_service_artefact._format_label = "invalid"
        with pytest.raises(ArtefactFormatUnknownError):
            repr(fx_lib_arcgis_service_artefact)
        with pytest.raises(ArtefactFormatUnknownError):
            fx_lib_arcgis_service_artefact.validate_format()

    @pytest.mark.parametrize("sharing_level", [SharingLevel.EVERYONE, SharingLevel.PRIVATE])
    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_distribution(
        self,
        fx_lib_arcgis_service_artefact: ArtefactArcGisService,
        sharing_level: SharingLevel,
        service_label: ArtefactFormatLabel | None,
    ):
        """Can get ISO distribution and component elements based on artefact for item and service if applicable."""
        fx_lib_arcgis_service_artefact._format_service_label = service_label
        fx_lib_arcgis_service_artefact._item.url = "x" if service_label else None
        fx_lib_arcgis_service_artefact._item.sharing_level = sharing_level
        expected_host = "maps.arcgis.com" if sharing_level == SharingLevel.EVERYONE else "bas.maps.arcgis.com"
        expected_title = "ArcGIS Online"

        assert isinstance(fx_lib_arcgis_service_artefact.distribution_option, Distribution)
        assert isinstance(fx_lib_arcgis_service_artefact.distributor, Contact)
        assert isinstance(fx_lib_arcgis_service_artefact.distribution_format, Format)
        assert isinstance(fx_lib_arcgis_service_artefact.distribution_transfer_opt, TransferOption)

        _online_resource = fx_lib_arcgis_service_artefact.distribution_transfer_opt.online_resource
        assert _online_resource.title == expected_title
        assert _online_resource.description == "Access information as an ArcGIS feature layer."
        assert _online_resource.href.startswith(f"https://{expected_host}")
        assert _online_resource.function == OnlineResourceFunctionCode.INFORMATION

        if service_label:
            assert isinstance(fx_lib_arcgis_service_artefact.distribution_option_service, Distribution)
            assert isinstance(fx_lib_arcgis_service_artefact.distribution_format_service, Format)
            assert isinstance(fx_lib_arcgis_service_artefact.distribution_transfer_opt_service, TransferOption)

            _online_resource_service = fx_lib_arcgis_service_artefact.distribution_transfer_opt_service.online_resource
            assert _online_resource_service.title == expected_title
            assert _online_resource_service.description == "Access information as an ArcGIS feature service."
            assert _online_resource_service.href == "x"
            assert _online_resource_service.function == OnlineResourceFunctionCode.DOWNLOAD
        else:
            assert fx_lib_arcgis_service_artefact.distribution_option_service is None
            assert fx_lib_arcgis_service_artefact.distribution_format_service is None
            assert fx_lib_arcgis_service_artefact.distribution_transfer_opt_service is None

    @pytest.mark.cov()
    def test_distribution_transfer_opt_service_no_description(
        self, fx_lib_arcgis_service_artefact: ArtefactArcGisService
    ):
        """Can get ISO distribution and component elements based on artefact for item and service if applicable."""
        fx_lib_arcgis_service_artefact._item.url = "x"

        assert isinstance(fx_lib_arcgis_service_artefact.distribution_transfer_opt_service, TransferOption)
        assert fx_lib_arcgis_service_artefact.distribution_transfer_opt_service.online_resource.description is None
