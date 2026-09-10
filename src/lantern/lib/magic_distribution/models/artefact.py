import uuid
from abc import ABC, abstractmethod
from base64 import b64encode, urlsafe_b64encode
from contextlib import contextmanager
from enum import Enum
from functools import cached_property
from json import JSONDecodeError
from pathlib import Path
from typing import IO, TYPE_CHECKING, Final, NamedTuple, cast, get_type_hints

import geojson
from PIL import Image, UnidentifiedImageError
from quickxorhash import quickxorhash  # ty: ignore[unresolved-import]

from lantern.lib.magic_distribution.models.metadata import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.distribution import Format

if TYPE_CHECKING:
    from collections.abc import Iterator

    from PIL.TiffImagePlugin import TiffImageFile


class ArtefactFormatUnknownError(Exception):
    """Raised when a requested ArtefactFormat is not defined, and therefore unsupported."""


class ArtefactFormatNotSupportedError(Exception):
    """Raised when a requested ArtefactFormat is known but unsupported."""


class ArtefactFormatLabel(Enum):
    """Labels for supported artefact formats."""

    # Files
    CSV = "csv"
    FPL = "fpl"
    GPX = "gpx"
    JPEG = "jpeg"
    GEOJSON = "geojson"
    GEOPACKAGE = "gpkg"
    GEOPACKAGE_ZIP = "gpkg_zip"
    MAPBOX_VECTOR_TILES = "mbtiles"
    PDF = "pdf"
    GEOPDF = "pdf_geo"
    PNG = "png"
    SHAPEFILE_ZIP = "shp_zip"
    GEOTIFF = "geotiff"
    # Services
    ARCGIS_FEATURE_SERVICE = "arcgis_feature_service"
    ARCGIS_FEATURE_LAYER = "arcgis_feature_layer"
    ARCGIS_OGC_FEATURES_SERVICE = "arcgis_ogc_features_service"
    ARCGIS_OGC_FEATURES_LAYER = "arcgis_ogc_features_layer"
    ARCGIS_RASTER_TILE_SERVICE = "arcgis_raster_tile_service"
    ARCGIS_RASTER_TILE_LAYER = "arcgis_raster_tile_layer"
    ARCGIS_VECTOR_TILE_SERVICE = "arcgis_vector_tile_service"
    ARCGIS_VECTOR_TILE_LAYER = "arcgis_vector_tile_layer"
    ARCGIS_SCENE_SERVICE = "arcgis_scene_service"
    ARCGIS_SCENE_LAYER = "arcgis_scene_layer"
    ARCGIS_WEB_MAP = "arcgis_web_map"


class ArtefactFormat(NamedTuple):
    """Artefact format."""

    label: ArtefactFormatLabel
    name: str
    title: str | None
    description: str | None
    extensions: list[str]
    media_types: list[str]
    registration: str | None


class ArtefactFormats:
    """Artefact formats manager."""

    file_formats: Final[list[ArtefactFormat]] = [
        ArtefactFormat(
            ArtefactFormatLabel.CSV,
            "CSV",
            "Comma Separated Values",
            None,
            [".csv"],
            ["text/csv"],
            "https://www.iana.org/assignments/media-types/text/csv",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.FPL,
            "FPL",
            "Garmin Flight Plan (FPL)",
            None,
            [".fpl"],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/application/fpl+xml",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.GPX,
            "GPX",
            "GPS Exchange Format",
            None,
            [".gpx"],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/application/gpx+xml",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.JPEG,
            "JPEG",
            None,
            None,
            [".jpg", ".jpeg"],
            ["image/jpeg"],
            "https://www.iana.org/assignments/media-types/image/jpeg",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.GEOJSON,
            "GeoJSON",
            None,
            None,
            [".geojson", ".json"],
            ["application/geo+json"],
            "https://www.iana.org/assignments/media-types/application/geo+json",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.GEOPACKAGE,
            "GeoPackage",
            None,
            None,
            [".gpkg"],
            ["application/geopackage+sqlite3"],
            "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.GEOPACKAGE_ZIP,
            "GeoPackage (Zipped)",
            None,
            "Download information as a GeoPackage file compressed as a Zip archive.",
            [".gpkg.zip"],
            [],
            "https://www.iana.org/assignments/media-types/application/geo+json",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.MAPBOX_VECTOR_TILES,
            "MBTiles",
            "MapBox Vector Tiles (MBTiles)",
            None,
            [".mbtiles"],
            ["application/vnd.mapbox-vector-tile"],
            "https://www.iana.org/assignments/media-types/application/vnd.mapbox-vector-tile",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.PDF,
            "PDF",
            None,
            None,
            [".pdf"],
            ["application/pdf"],
            "https://www.iana.org/assignments/media-types/application/pdf",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.GEOPDF,
            "GeoPDF",
            "PDF (Georeferenced)",
            "Download information as a PDF file with embedded georeferencing.",
            [".pdf"],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/application/geo+pdf",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.PNG,
            "PNG",
            None,
            None,
            [".png"],
            ["image/png"],
            "https://www.iana.org/assignments/media-types/image/png",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.SHAPEFILE_ZIP,
            "Shapefile (Zipped)",
            None,
            "Download information as a Shapefile compressed as a Zip archive.",
            [".shp.zip"],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/application/shapefile+zip",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.GEOTIFF,
            "GeoTIFF",
            None,
            None,
            [".tif", ".tiff"],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/image/geo+tiff",
        ),
    ]
    service_formats: Final[list[ArtefactFormat]] = [
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE,
            "ArcGIS Feature Service",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_SERVICE,
            "OGC API Features (ArcGIS) Service",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_SERVICE,
            "ArcGIS Raster Tile Service",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_SERVICE,
            "ArcGIS Vector Tile Service",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_SCENE_SERVICE,
            "ArcGIS 3D Scene Service",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+scene",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_FEATURE_LAYER,
            "ArcGIS Feature Layer",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_LAYER,
            "OGC API Features (ArcGIS) Layer",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_LAYER,
            "ArcGIS Raster Tile Layer",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_LAYER,
            "ArcGIS Vector Tile Layer",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_SCENE_LAYER,
            "ArcGIS 3D Scene Layer",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+scene",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_WEB_MAP,
            "ArcGIS Web Map",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+webmap",
        ),
    ]

    @classmethod
    def get_label(cls, label: ArtefactFormatLabel) -> ArtefactFormat:
        """Get supported format by internal label."""
        for format_ in [*cls.file_formats, *cls.service_formats]:
            if format_.label == label:
                return format_
        raise ArtefactFormatUnknownError() from None

    @cached_property
    def supported_extensions(self) -> set[str]:
        """
        All supported extensions.

        Does not include formats without extensions (such as services).

        Intended for file inputs which support setting a list of allowed file types by extension (e.g. `['.csv']`).

        WARNING! Checking file extensions is not sufficient for formats we only support when georeferenced (e.g. GeoJSON
        vs. JSON), as they share a common extension. Call `file_supported()` after upload to run additional checks.
        """
        return {ext for format_ in self.file_formats for ext in format_.extensions}

    @cached_property
    def supported_media_types(self) -> set[str]:
        """
        All supported media (MIME) types.

        Does not include formats without media types (such as services).

        Intended for file inputs which support setting a list of allowed file types by media type (e.g. `['text/csv']`).

        WARNING! Checking media types is not sufficient for formats we only support when georeferenced (e.g. GeoJSON
        vs. JSON), as they are often derived from the file extension. Call `file_supported()` after upload to run
        additional checks.
        """
        return {type_ for format_ in self.file_formats for type_ in format_.media_types}

    @staticmethod
    def _check_file_geojson(file: IO[bytes]) -> bool:
        """Check if a JSON file is GeoJSON."""
        try:
            data = geojson.load(file)
        except JSONDecodeError:
            return False
        else:
            # non-GeoJSON data is returned as-is and won't have a `is_valid` attribute so check first
            if "is_valid" not in dir(data):
                return False
            return data.is_valid

    @staticmethod
    def _check_file_geopdf(file: IO[bytes]) -> bool:
        """
        Check if a PDF file is a GeoPDF.

        PDFs have a complex structure and there are multiple ways to include georeferencing information used by
        different tools. This check looks for common georeferencing markers only.

        Markers checked:
        - `/LGIDict`: container for information about a map frame within the PDF
        - `/Projection`: information about the projection used for a map frame (optional)
        - `/GPTS`: geospatial points, mapping page/pixel coordinates to geographic space (optional)

        Sources:
        - https://docs.ogc.org/bp/08-139r3/08-139r3.pdf
        - https://stackoverflow.com/a/75262732

        Note: PDFs may contain multiple map frames, which are not distinguished by this method.

        WARNING! This check is not definitive as the file is not parsed as a GeoPDF specifically.
        """
        data = file.read()
        return b"/LGIDict" in data or b"/Projection" in data or b"/GPTS" in data

    @staticmethod
    def _check_file_geotiff(file: IO[bytes]) -> bool:
        """
        Check if a Tiff image is a GeoTiff.

        Tiff files can include tags. This check looks for tag '34735' (GeoKeyDirectoryTag), used to include the CRS and
        other spatial metadata in GeoTiffs.

        WARNING! This check is not definitive as the file is not parsed as a GeoTiff specifically.
        """
        geo_key_directory_tag = 34735
        try:
            with Image.open(file) as f:
                f = cast("TiffImageFile", f)
                return geo_key_directory_tag in f.tag_v2
        except UnidentifiedImageError:
            return False

    @staticmethod
    def _get_file_extension(file: Path | IO[bytes], name: str | None = None) -> str:
        """Normalise opening an input file from a path or existing IO buffer."""
        if isinstance(file, Path):
            return "".join(file.suffixes).lower()
        if isinstance(name, str):
            return "".join(Path(name).suffixes).lower()
        msg = "Either a Path, or a binary file-like object and file name with extension, are required."
        raise TypeError(msg) from None

    @staticmethod
    @contextmanager
    def _open_binary(file: Path | IO[bytes]) -> Iterator[IO[bytes]]:
        """Normalise opening an input file from a path or IO buffer."""
        if isinstance(file, Path):
            with file.open("rb") as f:
                yield f
        else:
            file.seek(0)  # for Streamlit's UploadedFile
            yield file

    @classmethod
    def check_file_supported(cls, file: Path | IO[bytes], name: str | None = None) -> None:
        """
        Check if a file is supported based on extension and additional checks.

        `file` may be a `pathlib.Path`, or a binary file-like object together with a `name` including file extension.

        Distinguishes between georeferenced and non-georeferenced formats where:
        - both formats are supported but are distinguished (e.g. PDFs and GeoPDFs are both supported)
        - only georeferenced instances are supported (e.g. GeoJSON vs JSON where only GeoJSON is supported)

        Note: Media types are not checked as Python's `mimetypes` lookup maps to file extensions, which we already have
        a controlled list of.

        Raises:
        - ArtefactFormatUnknownError: where a file is an unsupported file format
        - ArtefactFormatNotSupportedError: where a file is a known format but not supported (e.g. non-georeferenced)

        Intended for parsing/validating file uploads or script arguments where only a binary pass/fail is needed.
        """
        geojson_exts = cls.get_label(ArtefactFormatLabel.GEOJSON).extensions
        geotiff_exts = cls.get_label(ArtefactFormatLabel.GEOTIFF).extensions
        file_ext = cls._get_file_extension(file=file, name=name)

        if file_ext not in [ext for format_ in cls.file_formats for ext in format_.extensions]:
            raise ArtefactFormatUnknownError() from None
        if file_ext not in geojson_exts and file_ext not in geotiff_exts:
            return  # known, unambiguous, format

        with cls._open_binary(file) as f:
            if file_ext in geojson_exts and not cls._check_file_geojson(f):
                msg = "Non-Geo JSON is not supported."
                raise ArtefactFormatNotSupportedError(msg) from None
            if file_ext in geotiff_exts and not cls._check_file_geotiff(f):
                msg = "Non-Geo Tiffs are not supported."
                raise ArtefactFormatNotSupportedError(msg) from None

    @classmethod
    def get_file_format(cls, file: Path | IO[bytes], name: str | None = None) -> ArtefactFormat:
        """
        Get the format for a supported file.

        `file` may be a `pathlib.Path`, or a binary file-like object together with a `name` including file extension.

        Implicitly checks format is supported.

        Raises:
        - ArtefactFormatUnknownError or ArtefactFormatNotSupportedError: from checking whether a file is supported
        - RuntimeError: as a fallback for a supported file not matched to a supported format (this shouldn't happen)

        Intended for use in Artefact classes.
        """
        geopdf_format = cls.get_label(ArtefactFormatLabel.GEOPDF)
        file_ext = cls._get_file_extension(file=file, name=name)

        cls.check_file_supported(file=file, name=name)  # may raise ArtefactFormatUnknown or NotSupported errors

        # explicitly check for GeoPDFs as they don't have a distinct file extension and we allow non-GeoPDFs
        if file_ext in geopdf_format.extensions:
            with cls._open_binary(file) as f:
                return geopdf_format if cls._check_file_geopdf(f) else cls.get_label(ArtefactFormatLabel.PDF)

        return next(_format for _format in cls.file_formats if file_ext in _format.extensions)


class ArtefactBase(ABC):
    """Artefact abstract base class."""

    _artefact_namespace: Final[str] = "https://artefacts.data.bas.ac.uk"

    def __init__(self, resource_id: str) -> None:
        self._resource_id = resource_id

    @property
    @abstractmethod
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""

    @cached_property
    def artefact_id(self) -> str:
        """
        Artefact identifier.

        Derived from resource identifier and a suitable hash of the artefact given by `_artefact_hash`.
        The URL (https://artefacts.data.bas.ac.uk/) is used as a namespace only and will not resolve to the artefact.
        """
        name = f"{self._artefact_namespace}/{self._resource_id}:{self._artefact_hash}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, name))

    @property
    def resource_id(self) -> str:
        """Resource identifier."""
        return self._resource_id

    @property
    @abstractmethod
    def format(self) -> ArtefactFormat:
        """Artefact format."""

    @property
    def format_label(self) -> ArtefactFormatLabel:
        """Artefact format label."""
        return self.format.label

    @property
    def distribution_format(self) -> Format | None:
        """Artefact format as an ISO distribution format."""
        return Format(format=self.format.name, href=self.format.registration)

    @property
    @abstractmethod
    def name(self) -> str:
        """Artefact name."""

    @property
    @abstractmethod
    def size_bytes(self) -> int | None:
        """Optional artefact size in bytes."""

    @abstractmethod
    def validate(self) -> bool:
        """Check artefact is a supported type."""


class ArtefactFile(ArtefactBase):
    """Artefact representing a file."""

    @property
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return self.quickxor

    @property
    @abstractmethod
    def data(self) -> bytes:
        """Artefact content as bytes."""

    @property
    @abstractmethod
    def size_bytes(self) -> int:
        """Artefact size in bytes."""

    @cached_property
    def quickxor(self) -> str:
        """Microsoft QuickXorHash."""
        h = quickxorhash()
        chunk_size = 8192
        data = self.data
        for i in range(0, len(data), chunk_size):
            h.update(bytes(data[i : i + chunk_size]))
        return b64encode(h.digest()).decode()

    @property
    def deposit_metadata(self) -> ArtefactMetadata:
        """
        Artefact metadata required for file deposits.

        The required `unrestricted` property depends on access permissions artefacts don't hold and defaults to False.
        This property should be overridden in a context where access permissions are known and can be accurately set.
        """
        return ArtefactMetadata(
            resource_id=self.resource_id,
            artefact_id=self.artefact_id,
            artefact_fmt=self.format_label.name,
            unrestricted=False,
        )


class ArtefactServicePlaceholder(ArtefactBase):
    """
    Artefact representing a service.

    Placeholder implementation to show an alternative to file artefacts.
    """

    def __init__(
        self, resource_id: str, artefact_name: str, artefact_url: str, artefact_format: ArtefactFormat
    ) -> None:
        super().__init__(resource_id)
        self._artefact_name = artefact_name
        self._artefact_url = artefact_url
        self._artefact_format = artefact_format

    @property
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return urlsafe_b64encode(self._artefact_url.encode()).decode()

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._artefact_name

    @property
    def format(self) -> ArtefactFormat:
        """Artefact format."""
        return self._artefact_format

    @property
    def size_bytes(self) -> None:
        """Artefact size in bytes."""
        return None

    def validate(self) -> bool:
        """Check service is a supported type."""
        return False


class ArtefactLocalFile(ArtefactFile):
    """
    File artefact for a local file.

    Intended for file artefacts before they've been deposited for use with scripts, CLIs, etc.

    Uses the contents and properties of a file directly to determine its format, size, name, etc. and to allow upload
    to a data access system.

    Note: This class assumes the entire file contents can be read into memory, which is a known limitation. Care should
    be when handling large files.
    """

    def __init__(self, resource_id: str, artefact_path: Path) -> None:
        super().__init__(resource_id)
        self._artefact = artefact_path

    def __repr__(self) -> str:
        """Class representation."""
        return f"<ArtefactLocal: {self.name}, {self.format.name}, {self.size_bytes} bytes>"

    @property
    def format(self) -> ArtefactFormat:
        """
        Artefact format.

        Raises ArtefactFormatUnknownError, ArtefactFormatNotSupportedError if not supported.
        """
        return ArtefactFormats.get_file_format(self._artefact, name=self.name)

    def validate(self) -> bool:
        """Check file is a supported type."""
        try:
            ArtefactFormats.check_file_supported(self._artefact, name=self.name)
        except ArtefactFormatUnknownError, ArtefactFormatNotSupportedError:
            return False
        else:
            return True

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._artefact.name

    @property
    def data(self) -> bytes:
        """Artefact content as bytes."""
        return self._artefact.read_bytes()

    @property
    def size_bytes(self) -> int:
        """Artefact size in bytes."""
        return self._artefact.stat().st_size


class ArtefactSharePointFile(ArtefactFile):
    """
    File artefact for a remote file stored in SharePoint.

    Intended for, and specific to, file artefacts deposited in the MAGIC Resource Distribution SharePoint site.

    Uses metadata recorded about a file to state its format, size, name, etc. Does not allow access to file content.

    Provides an access URL to access the artefact file for use in distribution options within resource records.

    Metadata
    --------

    Metadata consists of:
    - `drive_item`: system metadata (file size, hash, name, etc.), via an MS Graph `driveItem` resource [1]
    - `list_metadata`: user metadata (artefact/resource ID, controlled format and unrestricted status), via an MS Graph
      `fieldValueSet` [2]

    `drive_item` properties are generic and controlled by the underlying SharePoint/Graph platform. `list_metadata`
    properties are intended to provide additional context where needed. `list_metadata` values are explicitly trusted.

    Artefact format
    ---------------

    As determining the artefact format accuretly requires access the file content (e.g. for geo-PDFs) and file content
    is not accessible, a known format must be provided by via `list_metadata`. This stated value MUST be a member of
    the `lantern.lib.magic_distribution.models.artefacts.ArtefactFormatLabel` enum and will be treated as authoriative.

    Access Proxy
    ------------

    The anonymous sharing level within SharePoint can be disabled at a site or tenancy level, preventing access to any
    files without explict sharing. To overcome this for files intended for open access resources an access proxy CAN be
    used. At a high level, this proxy will request a file on the client's behalf, checking access permissions and if
    applicable, returning a pre-signed URL to the file via a redirect.

    The access URL will use an access proxy where the `proxy_base` parameter is set and the `unrestricted` value in
    `list_metadata` is true.

    [1] https://learn.microsoft.com/en-us/graph/api/resources/driveitem
    [2] https://learn.microsoft.com/en-us/graph/api/resources/fieldvalueset
    """

    def __init__(self, drive_item: dict, list_metadata: ArtefactMetadata, proxy_base: str | None = None) -> None:
        self._check_artefact_metadata(list_metadata)
        self._drive_item = drive_item
        self._list_fields = list_metadata
        self._proxy_base = proxy_base
        super().__init__(self.resource_id)

    def __repr__(self) -> str:
        """Class representation."""
        return f"<ArtefactSpFile: {self.artefact_id} (driveItem: {self._drive_item['id']}), {self.format.name}, {self.size_bytes} bytes>"

    @staticmethod
    def _check_artefact_metadata(list_metadata: ArtefactMetadata) -> None:
        """Validate required metadata against typed dict."""
        keys = get_type_hints(ArtefactMetadata).keys()
        if not all(key in list_metadata for key in keys):
            msg = "One or more required artefact metadata keys are missing from SharePoint list metadata."
            raise KeyError(msg)

    @property
    def artefact_id(self) -> str:
        """Artefact identifier."""
        return self._list_fields["artefact_id"]

    @property
    def resource_id(self) -> str:
        """Resource identifier."""
        return self._list_fields["resource_id"]

    @property
    def format(self) -> ArtefactFormat:
        """Artefact format if supported."""
        try:
            label = ArtefactFormatLabel[self._list_fields["artefact_fmt"]]
        except KeyError:
            raise ArtefactFormatUnknownError() from None
        else:
            return ArtefactFormats.get_label(label)

    def validate(self) -> bool:
        """Check file is a supported type."""
        try:
            _ = self.format
        except ArtefactFormatUnknownError:
            return False
        else:
            return True

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._drive_item["name"]

    @property
    def data(self) -> memoryview:
        """Artefact content as bytes."""
        raise NotImplementedError() from None

    @property
    def size_bytes(self) -> int:
        """Artefact size in bytes."""
        return self._drive_item["size"]

    @property
    def quickxor(self) -> str:
        """Microsoft QuickXorHash."""
        return self._drive_item["file"]["hashes"]["quickXorHash"]

    @property
    def url(self) -> str:
        """
        Direct access URL, unless an access proxy is configured and the artefact is unrestricted.

        Where an access proxy is used, the direct URL will be base 64 encoded and appended to the `proxy_base`
        parameter as a `url` query parameter.

        E.g. For a proxy base `https://example.com` and direct URL of `https://example.com/file.ext`,
        `https://example.com?url=aHR0cHM6Ly9leGFtcGxlLmNvbS9maWxlLnR4dA==` will be returned.
        """
        if self._list_fields["unrestricted"] and self._proxy_base:
            return f"{self._proxy_base}?url={urlsafe_b64encode(self._drive_item['webUrl'].encode()).decode()}"
        return self._drive_item["webUrl"]
