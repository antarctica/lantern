import pytest

from lantern.lib.metadata_library.models.record import Distribution as RecordDistribution
from lantern.lib.metadata_library.models.record.elements.common import Contact, ContactIdentity, OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Format, Size, TransferOption
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode
from lantern.models.item.base import AccessLevel
from lantern.models.item.base.elements import Link
from lantern.models.item.catalogue.distributions import (
    ArcGISDistribution,
    ArcGisFeatureLayer,
    ArcGisOgcApiFeatures,
    ArcGisVectorTileLayer,
    Distribution,
    FileDistribution,
    GeoJson,
    GeoPackage,
    Jpeg,
    Pdf,
    Png,
    Shapefile,
)
from lantern.models.item.catalogue.enums import DistributionType


def _make_dist(format_href: str) -> RecordDistribution:
    return RecordDistribution(
        distributor=Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.DISTRIBUTOR]),
        transfer_option=TransferOption(
            online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
        ),
        format=Format(format="x", href=format_href),
    )


class FakeDistributionType(Distribution):
    """For testing non-abstract distribution properties."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Match."""
        return False

    @property
    def format_type(self) -> DistributionType:
        """Format."""
        return DistributionType.ARCGIS_FEATURE_LAYER

    @property
    def size(self) -> str:
        """Size."""
        return "x"

    @property
    def action(self) -> Link:
        """Link."""
        return Link(value="x", href="x")

    @property
    def action_btn_icon(self) -> str:
        """Link icon."""
        return "far fa-square"

    @property
    def access_target(self) -> None:
        """Access target."""
        return None


class FakeArcGISDistributionType(ArcGISDistribution):
    """For testing non-abstract or common ArcGIS distribution properties."""

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution], **kwargs: dict) -> None:
        service_media_href = "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        super().__init__(option, other_options, service_media_href, **kwargs)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Match."""
        return False

    @property
    def format_type(self) -> DistributionType:
        """Format."""
        return DistributionType.ARCGIS_FEATURE_LAYER


class FakeFileDistributionType(FileDistribution):
    """For testing non-abstract or common file distribution properties."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Match."""
        return False

    @property
    def format_type(self) -> DistributionType:
        """Format."""
        return DistributionType.GEOJSON


class TestDistribution:
    """Test base Catalogue distribution."""

    def test_encode_url(self):
        """Can encode a URL into a DOM selector."""
        value = "https://example.com"
        expected = "aHR0cHM6Ly9leGFtcGxlLmNvbQ"

        result = Distribution._encode_url(value)
        assert result == expected

    @pytest.mark.cov()
    def test_defaults(self):
        """Can get default values."""
        dist = FakeDistributionType()
        assert dist.action_btn_variant != ""
        assert dist.action_btn_icon != ""


class TestArcGISDistribution:
    """Test base ArcGIS based Catalogue distribution."""

    def test_get_service_option(self):
        """Can get distribution option for relevant ArcGIS service."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist._service == service_dist

    def test_get_service_option_missing(self):
        """Cannot get distribution option for relevant ArcGIS service if missing."""
        with pytest.raises(
            ValueError, match="Required corresponding service option not found in resource distributions."
        ):
            FakeArcGISDistributionType(option=_make_dist("x"), other_options=[])

    def test_size(self):
        """Can get non-applicable size."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.size == ""

    def test_item_link(self):
        """Can get link to ArcGIS layer."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.item_link == Link(value="x", href="x", external=True)

    def test_service_endpoint(self):
        """Can get endpoint to ArcGIS service."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.service_endpoint == "x"

    def test_action(self):
        """Can get action link."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.action == Link(value="Add to GIS", href=None)

    def test_action_variant(self):
        """Can get action variant."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.action_btn_variant == "primary"

    def test_action_btn_icon(self):
        """Can get action icon."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.action_btn_icon == "far fa-layer-plus"

    def test_access_target(self):
        """Can get action target."""
        service_dist = _make_dist(
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        dist = FakeArcGISDistributionType(option=_make_dist("x"), other_options=[service_dist])
        assert dist.access_target == "#item-data-info-eA"


class TestFileDistribution:
    """Test base file based Catalogue distribution."""

    @pytest.mark.parametrize(
        ("size", "expected"),
        [(Size(unit="bytes", magnitude=2), "2 Bytes"), (Size(unit="x", magnitude=1), "1 x"), (None, "")],
    )
    def test_size(self, size: Size | None, expected: str):
        """Can format file size."""
        dist = FakeFileDistributionType(option=_make_dist("x"), access_level=AccessLevel.PUBLIC)
        dist._option.transfer_option.size = size
        assert dist.size == expected

    @pytest.mark.parametrize(
        ("access", "expected"), [(AccessLevel.PUBLIC, "Download"), (AccessLevel.BAS_SOME, "Download")]
    )
    def test_action(self, access: AccessLevel, expected: str):
        """Can get action link."""
        dist = FakeFileDistributionType(option=_make_dist("x"), access_level=access)
        assert dist.action == Link(value=expected, href="x")

    @pytest.mark.parametrize(
        ("access", "expected"), [(AccessLevel.PUBLIC, "default"), (AccessLevel.BAS_SOME, "warning")]
    )
    def test_action_btn_variant(self, access: AccessLevel, expected: str):
        """Can get action variant."""
        dist = FakeFileDistributionType(option=_make_dist("x"), access_level=access)
        assert dist.action_btn_variant == expected

    @pytest.mark.parametrize(
        ("access", "expected"), [(AccessLevel.PUBLIC, "far fa-download"), (AccessLevel.BAS_SOME, "far fa-lock-alt")]
    )
    def test_action_btn_icon(self, access: AccessLevel, expected: str):
        """Can get action icon."""
        dist = FakeFileDistributionType(option=_make_dist("x"), access_level=access)
        assert dist.action_btn_icon == expected

    def test_access_target(self):
        """Can get null action target."""
        dist = FakeFileDistributionType(option=_make_dist("x"), access_level=AccessLevel.PUBLIC)
        assert dist.access_target is None


class TestDistributionArcGisFeatureLayer:
    """Test ArcGIS Feature Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature")
        others = [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")]

        dist = ArcGisFeatureLayer(main, others)
        assert dist.format_type == DistributionType.ARCGIS_FEATURE_LAYER

    @pytest.mark.parametrize(
        ("main", "others", "expected"),
        [
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")],
                True,
            ),
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature"),
                [_make_dist("x")],
                False,
            ),
            (
                _make_dist("x"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature")],
                False,
            ),
            (_make_dist("x"), [_make_dist("y")], False),
        ],
    )
    def test_matches(self, main: RecordDistribution, others: list[Distribution], expected: bool):
        """Can determine if a record distribution matches this catalogue distribution."""
        result = ArcGisFeatureLayer.matches(main, others)
        assert result == expected


class TestDistributionArcGisOgcApiFeatures:
    """Test ArcGIS OGC Features Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc")
        others = [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature")]

        dist = ArcGisOgcApiFeatures(main, others)
        assert dist.format_type == DistributionType.ARCGIS_OGC_FEATURE_LAYER

    @pytest.mark.parametrize(
        ("main", "others", "expected"),
        [
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature")],
                True,
            ),
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc"),
                [_make_dist("x")],
                False,
            ),
            (
                _make_dist("x"),
                [_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature")],
                False,
            ),
            (_make_dist("x"), [_make_dist("y")], False),
        ],
    )
    def test_matches(self, main: RecordDistribution, others: list[Distribution], expected: bool):
        """Can determine if a record distribution matches this catalogue distribution."""
        result = ArcGisOgcApiFeatures.matches(main, others)
        assert result == expected


class TestDistributionArcGisVectorTileLayer:
    """Test ArcGIS Vector Tile Layer catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        main = _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector")
        others = [
            _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector")
        ]

        dist = ArcGisVectorTileLayer(main, others)
        assert dist.format_type == DistributionType.ARCGIS_VECTOR_TILE_LAYER

    @pytest.mark.parametrize(
        ("main", "others", "expected"),
        [
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector"),
                [
                    _make_dist(
                        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector"
                    )
                ],
                True,
            ),
            (
                _make_dist("https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector"),
                [_make_dist("x")],
                False,
            ),
            (
                _make_dist("x"),
                [
                    _make_dist(
                        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector"
                    )
                ],
                False,
            ),
            (_make_dist("x"), [_make_dist("y")], False),
        ],
    )
    def test_matches(self, main: RecordDistribution, others: list[Distribution], expected: bool):
        """Can determine if a record distribution matches this catalogue distribution."""
        result = ArcGisVectorTileLayer.matches(main, others)
        assert result == expected


class TestDistributionGeoJson:
    """Test GeoJSON catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = GeoJson(
            option=_make_dist("https://www.iana.org/assignments/media-types/application/geo+json"),
            access_level=AccessLevel.PUBLIC,
        )

        assert dist.format_type == DistributionType.GEOJSON


class TestDistributionGeoPackage:
    """Test GeoPackage catalogue distribution."""

    @pytest.mark.parametrize(
        ("href", "format_type", "compressed"),
        [
            (
                "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
                DistributionType.GEOPACKAGE,
                False,
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
                DistributionType.GEOPACKAGE_ZIP,
                True,
            ),
        ],
    )
    def test_init(self, href: str, format_type: DistributionType, compressed: bool):
        """Can create a distribution."""
        dist = GeoPackage(option=_make_dist(format_href=href), access_level=AccessLevel.PUBLIC)

        assert dist.format_type == format_type
        assert dist._compressed == compressed


class TestDistributionJpeg:
    """Test JPEG catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = Jpeg(option=_make_dist("https://jpeg.org/jpeg/"), access_level=AccessLevel.PUBLIC)
        assert dist.format_type == DistributionType.JPEG


class TestDistributionPdf:
    """Test PDF catalogue distribution."""

    @pytest.mark.parametrize(
        ("href", "format_type", "georeferenced"),
        [
            (
                "https://www.iana.org/assignments/media-types/application/pdf",
                DistributionType.PDF,
                False,
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
                DistributionType.PDF_GEO,
                True,
            ),
        ],
    )
    def test_init(self, href: str, format_type: DistributionType, georeferenced: bool):
        """Can create a distribution."""
        dist = Pdf(option=_make_dist(format_href=href), access_level=AccessLevel.PUBLIC)

        assert dist.format_type == format_type
        assert dist._georeferenced == georeferenced


class TestDistributionPng:
    """Test PNG catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = Png(
            option=_make_dist("https://www.iana.org/assignments/media-types/image/png"),
            access_level=AccessLevel.PUBLIC,
        )
        assert dist.format_type == DistributionType.PNG


class TestDistributionShapefile:
    """Test Shapefile catalogue distribution."""

    def test_init(self):
        """Can create a distribution."""
        dist = Shapefile(
            option=_make_dist("https://metadata-resources.data.bas.ac.uk/media-types/application/vnd.shp+zip"),
            access_level=AccessLevel.PUBLIC,
        )
        assert dist.format_type == DistributionType.SHAPEFILE_ZIP
