from lantern.lib.metadata_library.models.record.elements.distribution import Distribution
from lantern.lib.metadata_library.models.record.presets.contacts import make_esri_distributor
from lantern.lib.metadata_library.models.record.presets.distribution import make_esri_feature_layer


class TestMakeEsriFeatureLayer:
    """Test `make_esri_feature_layer()` preset."""

    def test_default(self):
        """Can generate expected distribution options for an ArcGIS feature layer."""
        distributor = make_esri_distributor()
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
        distributor = make_esri_distributor()
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
