import csv
from pathlib import Path

from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR, MAGIC_DISTRIBUTOR
from lantern.lib.metadata_library.models.record.presets.distribution import (
    make_distribution,
    make_esri_feature_layer,
    make_file_distribution,
    make_file_format,
)
from lantern.lib.metadata_library.models.record.utils.distribution import ZapFormat


class TestMakeEsriFeatureLayer:
    """Test `make_esri_feature_layer()` preset."""

    def test_default(self):
        """Can generate expected distribution options for an ArcGIS feature layer."""
        distributor = ESRI_DISTRIBUTOR
        portal_endpoint = "https://example.com"
        server_endpoint = f"{portal_endpoint}/arcgis"
        service_name = "x"
        item_id = "y"

        expected_server_url = f"{server_endpoint}/rest/services/{service_name}/FeatureServer"
        expected_server_media_type = (
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        )
        expected_portal_url = f"{portal_endpoint}/home/item.html?id={item_id}"
        expected_portal_media_type = (
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature"
        )

        result = make_esri_feature_layer(portal_endpoint, server_endpoint, service_name, item_id)

        assert len(result) == 2
        assert all(isinstance(distribution, Distribution) for distribution in result)
        assert all(distribution.distributor == distributor for distribution in result)

        assert result[0].format.href == expected_server_media_type
        assert result[0].transfer_option.online_resource.href == expected_server_url

        assert result[1].format.href == expected_portal_media_type
        assert result[1].transfer_option.online_resource.href == expected_portal_url

    def test_with_ogc(self):
        """Can generate expected distribution options for an ArcGIS feature layer with optional OGC features layer."""
        distributor = ESRI_DISTRIBUTOR
        portal_endpoint = "https://example.com"
        server_endpoint = f"{portal_endpoint}/arcgis"
        service_name = "x"
        item_id = "y"
        ogc_item_id = "z"

        expected_server_url = f"{server_endpoint}/rest/services/{service_name}/OGCFeatureServer"
        expected_server_media_type = "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature"
        expected_portal_url = f"{portal_endpoint}/home/item.html?id={ogc_item_id}"
        expected_portal_media_type = (
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc"
        )

        result = make_esri_feature_layer(portal_endpoint, server_endpoint, service_name, item_id, ogc_item_id)

        assert len(result) == 4
        assert all(isinstance(distribution, Distribution) for distribution in result)
        assert all(distribution.distributor == distributor for distribution in result)

        assert result[2].format.href == expected_server_media_type
        assert result[2].transfer_option.online_resource.href == expected_server_url

        assert result[3].format.href == expected_portal_media_type
        assert result[3].transfer_option.online_resource.href == expected_portal_url


class TestFileFormat:
    """Test `make_file_format` preset."""

    def test_make_file_format(self):
        """Can make a distribution format from a known file path extension."""
        result = make_file_format(Path("x.csv"))
        assert isinstance(result, Format)
        assert result.href == "https://www.iana.org/assignments/media-types/text/csv"


class TestDistribution:
    """Test `make_distribution` preset."""

    def test_make_distribution(self):
        """Can make a distribution option with Zap format and optional format description and resource size."""
        format_ = ZapFormat(
            slug="csv",
            name="Comma Separated Values",
            url="https://www.iana.org/assignments/media-types/text/csv",
            extensions=[".csv"],
            media_types="text/csv",
        )
        result = make_distribution(format_=format_, access_url="x", distributor=MAGIC_DISTRIBUTOR, size_bytes=123)
        assert isinstance(result, Distribution)
        assert isinstance(result.format, Format)
        assert result.transfer_option.online_resource.href == "x"


class TestFileDistribution:
    """Test `make_file_distribution` preset."""

    def test_make_file_distribution(self, tmp_path: Path):
        """Can make a distribution option for a local file available at an access URL via a distributor."""
        csv_path = tmp_path / "x.csv"
        with csv_path.open("w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])

        result = make_file_distribution(path=csv_path, access_url="x", distributor=MAGIC_DISTRIBUTOR)
        assert isinstance(result, Distribution)
        assert result.transfer_option.online_resource.href == "x"
