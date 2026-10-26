from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from functools import cached_property
from json import JSONDecodeError
from pathlib import Path, PurePosixPath
from typing import IO, TYPE_CHECKING, Final, NamedTuple, cast
from urllib.parse import parse_qs, urlsplit
from zipfile import ZipFile

import geojson
import requests
from PIL import Image, UnidentifiedImageError
from requests import Response

from lantern.lib.arcgis.utils import ArcGISAuthError, ArcGISRequestError, check_arcgis_error, ensure_query_param

if TYPE_CHECKING:
    from collections.abc import Iterator

    from PIL.TiffImagePlugin import TiffImageFile
    from requests.auth import AuthBase

Image.MAX_IMAGE_PIXELS = None  # We routinely need to handle large rasters


class ArtefactFormatUnknownError(Exception):
    """Raised when a requested ArtefactFormat is not defined, and therefore unsupported."""


class ArtefactFormatNotSupportedError(Exception):
    """Raised when a requested ArtefactFormat is known but unsupported."""


class ArtefactInaccessibleError(Exception):
    """
    Raised when a requested artefact cannot be accessed and its format cannot be checked.

    E.g. a file or service that requires authentication to access.
    """


class ArtefactFormatLabel(Enum):
    """Labels for supported artefact formats."""

    # Files
    CSV = "csv"
    FPL = "fpl"
    GEOPACKAGE = "gpkg"
    GEOPACKAGE_ZIP = "gpkg_zip"
    GPX = "gpx"
    JPEG = "jpeg"
    GEOJSON = "geojson"
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
    ARCGIS_WEB_SCENE = "arcgis_web_scene"
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
            ArtefactFormatLabel.ARCGIS_WEB_MAP,
            "ArcGIS Web Map",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+web+map",
        ),
        ArtefactFormat(
            ArtefactFormatLabel.ARCGIS_WEB_SCENE,
            "ArcGIS Web Scene",
            None,
            None,
            [],
            [],
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+web+scene",
        ),
    ]

    @classmethod
    def get_by_label(cls, label: ArtefactFormatLabel) -> ArtefactFormat:
        """Get supported format by internal label."""
        for format_ in [*cls.file_formats, *cls.service_formats]:
            if format_.label == label:
                return format_
        raise ArtefactFormatUnknownError() from None

    @classmethod
    def get_by_registration(cls, registration_uri: str) -> ArtefactFormat:
        """
        Get supported format by registered media type URI.

        E.g. from a distribution option format.
        """
        for format_ in [*cls.file_formats, *cls.service_formats]:
            if format_.registration == registration_uri:
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
    def _check_file_gpkg_zip(file: IO[bytes]) -> bool:
        """
        Check if a zip archive contains a GeoPackage file.

        To distinguish archives containing GeoPackages from others, without only relying on a conventional file name.

        As weak resistance to smuggling unsupported formats within archives.

        WARNING! This check is not definitive as GeoPackage files are not parsed specifically.
        """
        with ZipFile(file) as archive:
            for f in archive.infolist():
                if PurePosixPath(f.filename).suffix == ".gpkg":
                    return True
        return False

    @staticmethod
    def _check_file_shp_zip(file: IO[bytes]) -> bool:
        """
        Check if a zip archive contains files required for a shapefile.

        To distinguish archives containing shapefiles from others, without only relying on a conventional file name.

        As weak resistance to smuggling unsupported formats within archives.

        WARNING! This check is not definitive as Shapefile files are not parsed specifically.
        """
        required = {".shp", ".shx", ".dbf"}

        with ZipFile(file) as archive:
            extensions = {PurePosixPath(f.filename).suffix for f in archive.infolist()}
            if extensions.issuperset(required):
                return True

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

        Checks the contents of zip archives for formats consisting of multiple files and/or allowing compression
        (e.g. Shapefile).

        Note: Media types are not checked as Python's `mimetypes` lookup maps to file extensions, which we already have
        a controlled list of.

        Raises:
        - ArtefactFormatUnknownError: where a file is an unsupported file format
        - ArtefactFormatNotSupportedError: where a file is a known format but not supported (e.g. non-georeferenced)

        Intended for parsing/validating file uploads or script arguments where only a binary pass/fail is needed.

        This 'None or Raise' pattern is used for consistency with `Record.validate()`.
        """
        geojson_exts = cls.get_by_label(ArtefactFormatLabel.GEOJSON).extensions
        geotiff_exts = cls.get_by_label(ArtefactFormatLabel.GEOTIFF).extensions
        gpkg_z_exts = cls.get_by_label(ArtefactFormatLabel.GEOPACKAGE_ZIP).extensions
        shp_z_exts = cls.get_by_label(ArtefactFormatLabel.SHAPEFILE_ZIP).extensions

        file_ext = cls._get_file_extension(file=file, name=name)

        if file_ext not in {ext for format_ in cls.file_formats for ext in format_.extensions}:
            raise ArtefactFormatUnknownError() from None
        if file_ext not in {*geojson_exts, *geotiff_exts, *gpkg_z_exts, *shp_z_exts}:
            return  # known, unambiguous, format

        with cls._open_binary(file) as f:
            if file_ext in geojson_exts and not cls._check_file_geojson(f):
                msg = "Non-Geo JSON is not supported."
                raise ArtefactFormatNotSupportedError(msg) from None
            if file_ext in geotiff_exts and not cls._check_file_geotiff(f):
                msg = "Non-Geo Tiffs are not supported."
                raise ArtefactFormatNotSupportedError(msg) from None
            if file_ext in gpkg_z_exts and not cls._check_file_gpkg_zip(f):
                msg = "GeoPackage archives must contain a GeoPackage."
                raise ArtefactFormatNotSupportedError(msg) from None
            if file_ext in shp_z_exts and not cls._check_file_shp_zip(f):
                msg = "Shapefile archives must contain required Shapefile component files."
                raise ArtefactFormatNotSupportedError(msg) from None

    @classmethod
    def get_file_format(cls, file: Path | IO[bytes], name: str | None = None) -> ArtefactFormat:
        """
        Get the format for a supported file.

        `file` may be a `pathlib.Path`, or a binary file-like object together with a `name` including file extension.

        Implicitly checks format is supported.

        Raises `ArtefactFormatUnknownError` or `ArtefactFormatNotSupportedError` if not supported.

        Intended for use in Artefact classes.
        """
        geopdf_format = cls.get_by_label(ArtefactFormatLabel.GEOPDF)
        file_ext = cls._get_file_extension(file=file, name=name)

        cls.check_file_supported(file=file, name=name)  # may raise ArtefactFormatUnknown or NotSupported errors

        # explicitly check for GeoPDFs as they don't have a distinct file extension and we allow non-GeoPDFs
        if file_ext in geopdf_format.extensions:
            with cls._open_binary(file) as f:
                return geopdf_format if cls._check_file_geopdf(f) else cls.get_by_label(ArtefactFormatLabel.PDF)

        return next(_format for _format in cls.file_formats if file_ext in _format.extensions)

    @classmethod
    def _check_arcgis_error(cls, res: requests.Response) -> None:
        """Interpret ArcGIS endpoint errors within the context of determining a service format."""
        try:
            check_arcgis_error(res)
        except ArcGISAuthError as e:
            raise ArtefactInaccessibleError() from e
        except ArcGISRequestError as e:
            raise ArtefactFormatUnknownError() from e

    @classmethod
    def _check_arcgis_headers(cls, res: requests.Response) -> bool:
        """
        Check if a response contains headers related to ArcGIS services.

        Used as a corroborating hint that an endpoint should be interpreted as an ArcGIS service.
        """
        if (
            "ArcGIS Online" in [s.strip() for s in res.headers.get("Server", "").split(",")]
            or res.headers.get("x-powered-by", "") == "ArcGIS-Online-Hosted-Services"
        ):
            return True
        if any(
            header in res.headers
            for header in (
                "x-arcgis-trace-id",
                "x-arcgis-correlation-id",
                "x-arcgis-instance",
                "x-arcgis-instance-id",
                "x-arcgis-upstream",
            )
        ):
            return True
        return "x-esri-authorization" in ",".join(
            {res.headers.get(h, "").lower() for h in ("access-control-allow-headers", "vary")}
        )

    @classmethod
    def check_service_supported(cls, endpoint: str, endpoint_auth: AuthBase | None = None) -> None:
        """
        Check if a service is supported based on an endpoint URL.

        Wrapper around `get_service_format` returning None rather than a format if supported. Intended for
        parsing/validating service references where only a binary pass/fail is needed.

        This 'None or Raise' pattern is used for consistency with `Record.validate()`.

        Raises:
        - ArtefactFormatUnknownError: where a service type is an unsupported
        - ArtefactFormatNotSupportedError: where a service type is known but specifically not supported
        """
        _ = cls.get_service_format(endpoint=endpoint, endpoint_auth=endpoint_auth)

    @staticmethod
    def get_arcgis_item_format(item_type: str, item_type_keywords: set[str]) -> ArtefactFormat:
        """
        Determine if ArcGIS item type and item type keywords relates to a supported format.

        `item_type_keywords` should be returned as a set of strings.

        Raises `ArtefactFormatUnknownError` if not supported.
        """
        item_type = item_type.lower()
        item_type_keywords = {k.lower() for k in item_type_keywords}
        # as per https://developers.arcgis.com/rest/users-groups-and-items/items-and-item-types/
        if item_type == "feature service":
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_LAYER)
        if item_type == "ogcfeatureserver":
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_OGC_FEATURES_LAYER)
        if (
            item_type == "map service"
            and {"wmts", "hosted service"}.issubset(item_type_keywords)
            and "dynamic" not in item_type_keywords
        ):
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_RASTER_TILE_LAYER)
        if item_type == "vector tile service":
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_VECTOR_TILE_LAYER)
        if item_type == "web scene":
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_WEB_SCENE)
        if item_type == "web map":
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_WEB_MAP)
        raise ArtefactFormatUnknownError()

    @staticmethod
    def _classify_arcgis_service(response: Response) -> ArtefactFormat | None:
        """Determine if endpoint response relates to an ArcGIS service format."""
        endpoint = urlsplit(response.url).path

        if endpoint.endswith("/FeatureServer"):
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE)
        if endpoint.endswith("/OGCFeatureServer"):
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_OGC_FEATURES_SERVICE)
        if endpoint.endswith("/VectorTileServer"):
            return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_VECTOR_TILE_SERVICE)
        if endpoint.endswith("/MapServer"):
            # MapServers are ambiguous so check JSON payload
            try:
                data = response.json()
            except JSONDecodeError as e:
                raise ArtefactFormatUnknownError() from e
            if "TilesOnly" in str(data.get("capabilities", "")).split(","):
                return ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_RASTER_TILE_SERVICE)

        return None

    @staticmethod
    def _classify_arcgis_item(response: Response, endpoint_auth: AuthBase | None = None) -> ArtefactFormat | None:
        """Determine if endpoint response relates to an ArcGIS item format."""
        query = parse_qs(urlsplit(response.url).query, keep_blank_values=False)

        if not response.url.split("?")[0].endswith("/item.html") or "id" not in query:
            raise ArtefactFormatUnknownError()

        item_url = f"https://www.arcgis.com/sharing/rest/content/items/{query['id'][0]}"
        item_res = requests.get(url=item_url, auth=endpoint_auth, params={"f": "json"}, timeout=10)
        item_res.raise_for_status()
        ArtefactFormats._check_arcgis_error(item_res)
        item_data = item_res.json()
        try:
            return ArtefactFormats.get_arcgis_item_format(
                item_type=item_data.get("type", "").strip().lower(),
                item_type_keywords={t.lower() for t in item_data.get("typeKeywords", [])},
            )
        except ArtefactFormatUnknownError:
            return None

    @classmethod
    def get_service_format(cls, endpoint: str, endpoint_auth: AuthBase | None = None) -> ArtefactFormat:
        """
        Get the format for a supported service endpoint.

        Requires:
        - services are accessible via a URL

        Assumes:
        - services use HTTP as a protocol
        - services are RESTful and support JSON as a response content type

        Supports:
        - optional authentication

        Implicitly checks service type/format is supported.

        Raises one of these exceptions if not supported:
        - `ArtefactFormatUnknownError`
        - `ArtefactFormatNotSupportedError`
        - `ArtefactInaccessibleError` (where endpoint requires unprovided or unsatisfactory authentication)

        Intended for use in Artefact classes.
        """
        url = ensure_query_param(url=endpoint, name="f", value="json")  # as only ArcGIS services are supported
        res = requests.get(url=url, auth=endpoint_auth, headers={"Accept": "application/json"}, timeout=10)
        res.raise_for_status()

        # as only ArcGIS services/items are supported
        cls._check_arcgis_error(res)
        if not cls._check_arcgis_headers(res):
            raise ArtefactFormatUnknownError()

        # try as ArcGIS service, determining format via endpoint URL and JSON payload
        arc_service = cls._classify_arcgis_service(res)
        if arc_service:
            return arc_service

        # try as ArcGIS item, determining format via sharing API
        arc_item = cls._classify_arcgis_item(response=res, endpoint_auth=endpoint_auth)
        if arc_item:
            return arc_item

        raise ArtefactFormatUnknownError()
