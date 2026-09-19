from contextlib import contextmanager
from enum import Enum
from functools import cached_property
from json import JSONDecodeError
from pathlib import Path
from typing import IO, TYPE_CHECKING, Final, NamedTuple, cast

import geojson
from PIL import Image, UnidentifiedImageError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from PIL.TiffImagePlugin import TiffImageFile

Image.MAX_IMAGE_PIXELS = None  # We routinely need to handle large rasters


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
