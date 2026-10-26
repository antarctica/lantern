from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import IO, Final

import pytest
import requests
from _pytest.mark import ParameterSet
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture
from werkzeug import Response

from lantern.lib.arcgis.utils import ArcGISAuthError, ArcGISRequestError, HTTPArcGISTokenAuth
from lantern.lib.magic_distribution.formats import (
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormatNotSupportedError,
    ArtefactFormats,
    ArtefactFormatUnknownError,
    ArtefactInaccessibleError,
)


class TestArtefactsFormats:
    """Test artefact formats manager."""

    artefacts_path = Path(__file__).parent.parent.parent / "resources" / "artefacts"

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
    def test_get_by_label(self, label: ArtefactFormatLabel, expected: bool):
        """Can get format for a format label enum member if it exists."""
        if not expected:
            with pytest.raises(ArtefactFormatUnknownError):
                ArtefactFormats.get_by_label(label=label)
            return

        result = ArtefactFormats.get_by_label(label=label)
        assert isinstance(result, ArtefactFormat)
        assert result.label == label

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("registration_uri", "expected_label"),
        [("https://www.iana.org/assignments/media-types/text/csv", ArtefactFormatLabel.CSV), ("INVALID", False)],
    )
    def test_get_by_registration(self, registration_uri: str, expected_label: ArtefactFormatLabel | bool):
        """Can get format for a media_type enum member if it exists."""
        if not expected_label:
            with pytest.raises(ArtefactFormatUnknownError):
                ArtefactFormats.get_by_registration(registration_uri=registration_uri)
            return

        result = ArtefactFormats.get_by_registration(registration_uri=registration_uri)
        assert isinstance(result, ArtefactFormat)
        assert result.label == expected_label

    def test_supported_extensions(self):
        """Can get a flattened set of supported file extensions."""
        result = ArtefactFormats().supported_extensions
        assert isinstance(result, set)
        assert all(isinstance(ext, str) for ext in result)
        assert all(ext.startswith(".") for ext in result)

    def test_supported_media_types(self):
        """Can get a flattened set of supported media types."""
        result = ArtefactFormats().supported_media_types
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

        Implicitly checks file is JSON parsable and valid GeoJSON.
        """
        with path.open() as f:
            assert ArtefactFormats._check_file_geojson(f) is expected

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
        with path.open(mode="rb") as f:
            assert ArtefactFormats._check_file_geopdf(f) is expected

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
        with path.open(mode="rb") as f:
            assert ArtefactFormats._check_file_geotiff(f) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (artefacts_path / "gpkg_zip" / "sample.gpkg.zip", True),
            (artefacts_path / "_unsupported" / "invalid.gpkg.zip", False),
        ],
    )
    def test_check_file_gpkg_zip(self, path: Path, expected: bool):
        """Can check a file is a compressed GeoPackage archive."""
        with path.open(mode="rb") as f:
            assert ArtefactFormats._check_file_gpkg_zip(f) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (artefacts_path / "shp_zip" / "sample.shp.zip", True),
            (artefacts_path / "_unsupported" / "invalid.shp.zip", False),
        ],
    )
    def test_check_file_shp_zip(self, path: Path, expected: bool):
        """Can check a file is a Shapefile bundle archive."""
        with path.open(mode="rb") as f:
            assert ArtefactFormats._check_file_shp_zip(f) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name", "expected"),
        [(Path("x"), None, ""), (Path("x.Y.z"), None, ".y.z"), (BytesIO(b""), "x.Y.z", ".y.z"), (None, "x.x", ".x")],
    )
    def test_get_file_extension(self, file: Path | IO[bytes], name: str | None, expected: str):
        """Can get file extension from path or file name."""
        assert ArtefactFormats._get_file_extension(file=file, name=name) == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name"),
        [(None, None), (BytesIO(b""), None)],
    )
    def test_get_file_extension_invalid(self, file: Path | IO[bytes], name: str | None):
        """Cannot get file extension with invalid arguments."""
        with pytest.raises(TypeError):
            assert ArtefactFormats._get_file_extension(file=file, name=name)

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
        Can determine supported formats by file extension and contents where ambiguous.

        Ambiguous formats:
        - GeoJSON (non-geo JSON unsupported and '.geojson' ext not always used)
        - GeoTiff (non-geo Tiff unsupported)
        """
        ArtefactFormats.check_file_supported(file=file, name=name)

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("file", "name"),
        [(Path("x.x"), None), (BytesIO(b""), "x"), (Path("x.zip"), None)],
    )
    def test_check_file_unknown(self, file: Path | IO[bytes], name: str | None):
        """Can determine unknown and supported formats by file extension."""
        with pytest.raises(ArtefactFormatUnknownError):
            ArtefactFormats.check_file_supported(file=file, name=name)

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        "file",
        [
            artefacts_path / "_unsupported" / "sample.json",  # non-geo JSON
            artefacts_path / "_unsupported" / "sample.tiff",  # non-geo Tiff
            artefacts_path / "_unsupported" / "invalid.gpkg.zip",  # archive without a GeoPackage
            artefacts_path / "_unsupported" / "invalid.shp.zip",  # archive without Shapefile files
        ],
    )
    def test_check_file_unsupported(self, file: Path | IO[bytes]):
        """Can determine known and unsupported formats by file extension and/or archive contents."""
        with pytest.raises(ArtefactFormatNotSupportedError):
            ArtefactFormats.check_file_supported(file=file)

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
            (artefacts_path / "gpkg_zip" / "sample.gpkg.zip", None, ArtefactFormatLabel.GEOPACKAGE_ZIP),
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
        Can get supported format by file extension and contents where ambiguous.

        Ambiguous formats:
        - PDF (both supported)
        - Shapefile archives (to not solely rely on file extension convention)
        """
        result = ArtefactFormats.get_file_format(file=file, name=name)
        assert result.label == expected

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("exception", "expected"),
        [
            (ArcGISAuthError, ArtefactInaccessibleError),
            (ArcGISRequestError, ArtefactFormatUnknownError),
        ],
    )
    def test_check_arcgis_error(self, mocker: MockerFixture, exception: Exception, expected: Exception):
        """Can correctly contextualise ArcGIS API errors."""
        mocker.patch("lantern.lib.magic_distribution.formats.check_arcgis_error", side_effect=exception)
        res = mocker.MagicMock(spec_set=requests.Response)

        with pytest.raises(expected):
            ArtefactFormats._check_arcgis_error(res=res)

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("headers", "expected"),
        [
            ({}, False),
            ({"Server": "ArcGIS Online"}, True),
            ({"x-powered-by": "ArcGIS-Online-Hosted-Services"}, True),
            ({"x-arcgis-trace-id": "x"}, True),
            ({"x-arcgis-correlation-id": "x"}, True),
            ({"x-arcgis-instance": "x"}, True),
            ({"x-arcgis-instance-id": "x"}, True),
            ({"x-arcgis-upstream": "x"}, True),
            ({"access-control-allow-headers": "x-esri-authorization"}, True),
            ({"vary": "x-ESRI-authorization, x"}, True),
        ],
    )
    def test_check_arcgis_headers(self, httpserver: HTTPServer, headers: dict, expected: bool):
        """Can check for ArcGIS related headers in responses."""
        _route = "/endpoint"
        httpserver.expect_request(_route).respond_with_response(Response(headers=headers, status=HTTPStatus.OK))

        result = requests.get(httpserver.url_for(_route), timeout=10)
        assert ArtefactFormats._check_arcgis_headers(res=result) is expected

    @pytest.mark.cov()
    @pytest.mark.parametrize("state", ["supported", "unsupported"])
    def test_check_service_supported(self, mocker: MockerFixture, state: str) -> bool:
        """Can check if a service endpoint is supported."""
        mocker.patch.object(
            ArtefactFormats,
            "get_service_format",
            return_value=ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE),
        )
        if state == "supported":
            ArtefactFormats.check_service_supported(endpoint="x")
            return

        mocker.patch.object(ArtefactFormats, "get_service_format", side_effect=ArtefactFormatNotSupportedError)
        with pytest.raises(ArtefactFormatNotSupportedError):
            ArtefactFormats.check_service_supported(endpoint="x")

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("item_type", "item_type_keywords", "expected"),
        [
            (
                "Feature Service",
                {
                    "ArcGIS Server",
                    "Data",
                    "Feature Access",
                    "Feature Service",
                    "Metadata",
                    "Service",
                    "Single layer",
                    "Hosted Service",
                },
                ArtefactFormatLabel.ARCGIS_FEATURE_LAYER,
            ),
            (
                "OGCFeatureServer",
                {
                    "Data",
                    "Feature Service",
                    "Features",
                    "Metadata",
                    "OGC",
                    "OGC Feature Service",
                    "Service",
                    "Hosted Service",
                },
                ArtefactFormatLabel.ARCGIS_OGC_FEATURES_LAYER,
            ),
            (
                "Map Service",
                {"ArcGIS Server", "Data", "Map Service", "Metadata", "Service", "WMTS", "Hosted Service"},
                ArtefactFormatLabel.ARCGIS_RASTER_TILE_LAYER,
            ),
            (
                "Vector Tile Service",
                {"Data", "Service", "Vector Tile Service", "ArcGIS Server", "Hosted Service"},
                ArtefactFormatLabel.ARCGIS_VECTOR_TILE_LAYER,
            ),
            (
                "Web Scene",
                {
                    "3D",
                    "ArcGIS Online",
                    "Explorer Web Scene",
                    "Map",
                    "Online Scene",
                    "Scene",
                    "Streaming",
                    "ViewingMode-Local",
                    "Web",
                    "Web Scene",
                },
                ArtefactFormatLabel.ARCGIS_WEB_SCENE,
            ),
            (
                "Web Map",
                {"ArcGIS API for JavaScript", "ArcGIS Online", "Explorer Web Map", "Map", "Online Map", "Web Map"},
                ArtefactFormatLabel.ARCGIS_WEB_MAP,
            ),
        ],
    )
    def test_get_arcgis_item_format(self, item_type: str, item_type_keywords: set[str], expected: ArtefactFormatLabel):
        """Can get supported ArcGIS Portal item formats by item properties."""
        result = ArtefactFormats.get_arcgis_item_format(item_type=item_type, item_type_keywords=item_type_keywords)
        assert result.label == expected

    get_service_format_cases: Final[list[ParameterSet]] = [
        pytest.param(
            "https://x.arcgis.com/x/arcgis/rest/services/feature_service_open/FeatureServer",
            False,
            ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE,
            id="service-features-open",
        ),
        pytest.param(
            "https://x.arcgis.com/x/arcgis/rest/services/feature_service_closed/FeatureServer",
            True,
            ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE,
            id="service-features-closed",
        ),
        pytest.param(
            "https://x.arcgis.com/x/arcgis/rest/services/ogc_features_open/OGCFeatureServer",
            False,
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_SERVICE,
            id="service-ogc-features-open",
        ),
        pytest.param(
            "https://x.arcgis.com/x/arcgis/rest/services/ogc_features_closed/OGCFeatureServer",
            True,
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_SERVICE,
            id="service-ogc-features-closed",
        ),
        pytest.param(
            "https://tiles.arcgis.com/tiles/x/arcgis/rest/services/raster_tiles_open/MapServer",
            False,
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_SERVICE,
            id="service-raster-tiles-open",
        ),
        pytest.param(
            "https://tiles.arcgis.com/tiles/x/arcgis/rest/services/raster_tiles_closed/MapServer",
            True,
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_SERVICE,
            id="service-raster-tiles-closed",
        ),
        pytest.param(
            "https://vectortilex.arcgis.com/x/arcgis/rest/services/vector_tiles_open/VectorTileServer",
            False,
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_SERVICE,
            id="service-vector-tiles-open",
        ),
        pytest.param(
            "https://tiles.arcgis.com/tiles/x/arcgis/rest/services/vector_tiles_closed/VectorTileServer",
            True,
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_SERVICE,
            id="service-vector-tiles-closed",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789010",
            False,
            ArtefactFormatLabel.ARCGIS_FEATURE_LAYER,
            id="item-features-open",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789012",
            True,
            ArtefactFormatLabel.ARCGIS_FEATURE_LAYER,
            id="item-features-closed",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789020",
            False,
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_LAYER,
            id="item-ogc-features-open",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789022",
            True,
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_LAYER,
            id="item-ogc-features-closed",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789030",
            False,
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_LAYER,
            id="item-raster-tiles-open",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789032",
            True,
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_LAYER,
            id="item-raster-tiles-closed",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789040",
            False,
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_LAYER,
            id="item-vector-tiles-open",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789042",
            True,
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_LAYER,
            id="item-vector-tiles-closed",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789050",
            False,
            ArtefactFormatLabel.ARCGIS_WEB_SCENE,
            id="item-web-scene-open",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789052",
            True,
            ArtefactFormatLabel.ARCGIS_WEB_SCENE,
            id="item-web-scene-closed",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789060",
            False,
            ArtefactFormatLabel.ARCGIS_WEB_MAP,
            id="item-web-map-open",
        ),
        pytest.param(
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789062",
            True,
            ArtefactFormatLabel.ARCGIS_WEB_MAP,
            id="item-web-map-closed",
        ),
    ]

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(("endpoint", "with_auth", "expected"), get_service_format_cases)
    def test_get_service_format(self, endpoint: str, with_auth: bool, expected: ArtefactFormatLabel):
        """Can get supported format by service endpoint."""
        auth = HTTPArcGISTokenAuth(token="x") if with_auth else None  # noqa: S106
        result = ArtefactFormats.get_service_format(endpoint=endpoint, endpoint_auth=auth)
        assert result.label == expected

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_service_format_arc_error(self):
        """Cannot get service format where endpoint returns an ArcGIS application error."""
        with pytest.raises(ArtefactFormatUnknownError):
            _ = ArtefactFormats.get_service_format(endpoint="https://example.com")

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_service_format_not_arc_error(self):
        """Cannot get service format where endpoint headers don't indicate an ArcGIS application."""
        with pytest.raises(ArtefactFormatUnknownError):
            _ = ArtefactFormats.get_service_format(endpoint="https://example.com")

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        "endpoint",
        [
            "https://x.arcgis.com/x/arcgis/rest/services/feature_service_closed/FeatureServer",
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789000",
        ],
    )
    def test_get_service_format_auth_error(self, endpoint: str):
        """Cannot get service format where required authentication is not included for endpoint."""
        with pytest.raises(ArtefactInaccessibleError):
            _ = ArtefactFormats.get_service_format(endpoint=endpoint, endpoint_auth=None)

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        "endpoint",
        [
            "https://utility.arcgis.com/usrsvcs/servers/x/rest/services/x/map_image/MapServer",
            "https://utility.arcgis.com/usrsvcs/servers/x/rest/services/x/invalid/MapServer",
            "https://x.maps.arcgis.com/home/item.html?id=12345678901234567890123456789000",
        ],
    )
    def test_get_service_format_map_type_error(self, endpoint: str):
        """
        Cannot get service format for unsupported ArcGIS map formats.

        'invalid' case used to check service body contains valid JSON to check service capabilities.
        """
        with pytest.raises(ArtefactFormatUnknownError):
            _ = ArtefactFormats.get_service_format(endpoint=endpoint)
