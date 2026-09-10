from base64 import urlsafe_b64decode
from io import BytesIO
from pathlib import Path
from typing import IO
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest

from lantern.lib.magic_distribution.models.artefact import (
    ArtefactBase,
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormatNotSupportedError,
    ArtefactFormats,
    ArtefactFormatUnknownError,
    ArtefactLocalFile,
    ArtefactServicePlaceholder,
    ArtefactSharePointFile,
)
from lantern.lib.magic_distribution.models.metadata import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.distribution import Format


class TestArtefactsFormats:
    """Test artefact formats manager."""

    artefacts_path = Path(__file__).parent.parent.parent.parent / "resources" / "artefacts"

    def test_init(self):
        """Can create an artefact formats manager instance."""
        manager = ArtefactFormats()

        assert len(manager.file_formats) > 0
        assert len(manager.service_formats) > 0
        assert all(isinstance(fmt, ArtefactFormat) for fmt in manager.file_formats)
        assert all(isinstance(fmt, ArtefactFormat) for fmt in manager.service_formats)
        assert all(isinstance(fmt.label, ArtefactFormatLabel) for fmt in manager.file_formats)
        assert all(isinstance(fmt.label, ArtefactFormatLabel) for fmt in manager.service_formats)

    @pytest.mark.cov()
    @pytest.mark.parametrize(("label", "expected"), [(ArtefactFormatLabel.CSV, True), ("INVALID", False)])
    def test_get_label(self, label: ArtefactFormatLabel, expected: bool):
        """Can get format for a format label enum member if it exists."""
        manager = ArtefactFormats()

        if not expected:
            with pytest.raises(ArtefactFormatUnknownError):
                manager.get_label(label=label)
            return

        result = manager.get_label(label=label)
        assert isinstance(result, ArtefactFormat)

    def test_supported_extensions(self):
        """Can get a flattened set of supported file extensions."""
        manager = ArtefactFormats()
        result = manager.supported_extensions
        assert isinstance(result, set)
        assert all(isinstance(ext, str) for ext in result)
        assert all(ext.startswith(".") for ext in result)

    def test_supported_media_types(self):
        """Can get a flattened set of supported media types."""
        manager = ArtefactFormats()
        result = manager.supported_media_types
        assert isinstance(result, set)
        assert all(isinstance(mt, str) for mt in result)
        assert all("/" in mt for mt in result)

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (artefacts_path / "geojson" / "sample.geojson", True),
            (artefacts_path / "geojson" / "sample.json", True),
            (artefacts_path / "_unsupported" / "sample.json", False),  # JSON but not GeoJSON
            (artefacts_path / "_unsupported" / "sample.x", False),  # not JSON
        ],
    )
    def test_check_file_geojson(self, path: Path, expected: bool):
        """
        Can check a file is GeoJSON not regular JSON.

        Implictly checks file is JSON parsable and valid GeoJSON.
        """
        manager = ArtefactFormats()
        with path.open() as f:
            assert manager._check_file_geojson(f) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (artefacts_path / "pdf_geo" / "sample.pdf", True),
            (artefacts_path / "pdf" / "sample.pdf", False),  # PDF but not a GeoPDF
            (artefacts_path / "_unsupported" / "sample.x", False),  # not a PDF
        ],
    )
    def test_check_file_geopdf(self, path: Path, expected: bool):
        """Can check a file is a regular or georeferenced PDF."""
        manager = ArtefactFormats()
        with path.open(mode="rb") as f:
            assert manager._check_file_geopdf(f) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (artefacts_path / "tiff_geo" / "sample.tif", True),
            (artefacts_path / "tiff_geo" / "sample.tiff", True),
            (artefacts_path / "_unsupported" / "sample.tiff", False),  # Tiff but not a GeoTiff
            (artefacts_path / "_unsupported" / "sample.x", False),  # not a Tiff
        ],
    )
    def test_check_file_geotiff(self, path: Path, expected: bool):
        """Can check a file is a GeoTiff not a regular Tiff."""
        manager = ArtefactFormats()
        with path.open(mode="rb") as f:
            assert manager._check_file_geotiff(f) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name", "expected"),
        [(Path("x"), None, ""), (Path("x.Y.z"), None, ".y.z"), (BytesIO(b""), "x.Y.z", ".y.z"), (None, "x.x", ".x")],
    )
    def test_get_file_extension(self, file: Path | IO[bytes], name: str | None, expected: str):
        """Can get file extension from path or file name."""
        manager = ArtefactFormats()
        assert manager._get_file_extension(file=file, name=name) == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name"),
        [(None, None), (BytesIO(b""), None)],
    )
    def test_get_file_extension_invalid(self, file: Path | IO[bytes], name: str | None):
        """Cannot get file extension with invalid arguments."""
        manager = ArtefactFormats()
        with pytest.raises(TypeError):
            assert manager._get_file_extension(file=file, name=name)

    @pytest.mark.cov()
    @pytest.mark.parametrize("file", [artefacts_path / "csv" / "sample.csv", BytesIO(b"x,y\n1,2")])
    def test_open_binary(self, file: Path | IO[bytes]):
        """
        Can open a file from a path or buffer.

        Where a buffer is used, simulate a Streamlit file upload which needs rewinding before reading.
        """
        if isinstance(file, BytesIO):
            file.seek(0, 2)  # ensure _open_binary must seek back to zero

        with ArtefactFormats._open_binary(file) as f:
            if isinstance(file, BytesIO):
                assert f.tell() == 0

            assert isinstance(f.read(), bytes)

        if isinstance(file, BytesIO):
            # ensure the context manager does not close an externally owned buffer
            assert not file.closed

    @pytest.mark.parametrize(
        ("file", "name"),
        [
            (artefacts_path / "png" / "sample.png", None),
            (BytesIO(b""), "x.png"),
            (artefacts_path / "tiff_geo" / "sample.tiff", None),
            (artefacts_path / "geojson" / "sample.json", None),
        ],
    )
    def test_check_file_supported(self, file: Path | IO[bytes], name: str | None):
        """
        Can determine supported formats by file extension and contents where ambigious.

        Ambigious formats:
        - GeoJSON (non-geo JSON unsupported and '.geojson' ext not always used)
        - GeoTiff (non-geo Tiff unsupported)
        """
        manager = ArtefactFormats()
        manager.check_file_supported(file=file, name=name)

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name"),
        [(Path("x.x"), None), (BytesIO(b""), "x"), (Path("x.zip"), None)],
    )
    def test_check_file_unknown(self, file: Path | IO[bytes], name: str | None):
        """Can determine unknown and supporteded formats by file extension."""
        manager = ArtefactFormats()

        with pytest.raises(ArtefactFormatUnknownError):
            manager.check_file_supported(file=file, name=name)

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name"),
        [
            (artefacts_path / "_unsupported" / "sample.json", None),  # non-geo JSON
            (artefacts_path / "_unsupported" / "sample.tiff", None),  # non-geo Tiff
        ],
    )
    def test_check_file_unsupported(self, file: Path | IO[bytes], name: str | None):
        """Can determine known and unsupporteded formats by file extension."""
        manager = ArtefactFormats()

        with pytest.raises(ArtefactFormatNotSupportedError):
            manager.check_file_supported(file=file, name=name)

    @pytest.mark.parametrize(
        ("file", "name", "expected"),
        [
            (artefacts_path / "csv" / "sample.csv", None, ArtefactFormatLabel.CSV),
            (BytesIO(b""), "x.csv", ArtefactFormatLabel.CSV),
            (artefacts_path / "fpl" / "sample.fpl", None, ArtefactFormatLabel.FPL),
            (artefacts_path / "gpx" / "sample.gpx", None, ArtefactFormatLabel.GPX),
            (artefacts_path / "jpeg" / "sample.jpg", None, ArtefactFormatLabel.JPEG),
            (artefacts_path / "jpeg" / "sample.jpeg", None, ArtefactFormatLabel.JPEG),
            (artefacts_path / "geojson" / "sample.json", None, ArtefactFormatLabel.GEOJSON),
            (artefacts_path / "geojson" / "sample.geojson", None, ArtefactFormatLabel.GEOJSON),
            (artefacts_path / "gpkg" / "sample.gpkg", None, ArtefactFormatLabel.GEOPACKAGE),
            (artefacts_path / "gpkg" / "sample.gpkg.zip", None, ArtefactFormatLabel.GEOPACKAGE_ZIP),
            (artefacts_path / "mbtiles" / "sample.mbtiles", None, ArtefactFormatLabel.MAPBOX_VECTOR_TILES),
            (artefacts_path / "pdf" / "sample.pdf", None, ArtefactFormatLabel.PDF),
            (artefacts_path / "pdf_geo" / "sample.pdf", None, ArtefactFormatLabel.GEOPDF),
            (artefacts_path / "png" / "sample.png", None, ArtefactFormatLabel.PNG),
            (artefacts_path / "shp_zip" / "sample.shp.zip", None, ArtefactFormatLabel.SHAPEFILE_ZIP),
            (artefacts_path / "tiff_geo" / "sample.tiff", None, ArtefactFormatLabel.GEOTIFF),
        ],
    )
    def test_get_file_format(self, file: Path | IO[bytes], name: str | None, expected: ArtefactFormatLabel):
        """
        Can get supported format by file extension and contents where ambigious.

        Ambigious formats:
        - PDF (both supported)
        """
        manager = ArtefactFormats()
        result = manager.get_file_format(file=file, name=name)
        assert result.label == expected


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

    def validate(self) -> bool:
        """Check artefact is a supported type."""
        return False


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
        assert artefact.validate() is False


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
        assert artefact.validate() is True

    def test_unsupported(self):
        """Cannot create a valid local file artefact with an unsupported format."""
        expected_size = 25
        artefact = ArtefactLocalFile(resource_id="x", artefact_path=self.artefacts_path / "_unsupported" / "sample.x")

        # from ArtefactFile
        assert artefact.quickxor == "VH6vNOkIy6i6d5q1NAkZQDCHMLQ="  # not dependent on format

        # ArtefactLocalFile
        assert artefact.validate() is False
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
        assert artefact.validate() is True

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

        assert artefact.validate() is False
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
