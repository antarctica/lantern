from assets_tracking_service.lib.bas_data_catalogue.models.record import Distribution
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import OnlineResource
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.distribution import Format, TransferOption
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import OnlineResourceFunctionCode
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.contacts import make_esri_distributor


def make_esri_feature_layer(
    portal_endpoint: str, server_endpoint: str, service_name: str, item_id: str, item_ogc_id: str | None = None
) -> list[Distribution]:
    """
    Resource distribution for an ArcGIS feature layer and optional OGC feature layer.

    Generates a distribution representing a feature layer as a ArcGIS Server service and an ArcGIS portal item. Both
    are needed for different clients and use-cases.

    Optionally, a feature layer can be published as an OGC API Features service, consisting of a separate server
    endpoint and portal item. If this portal item ID is provided, additional distribution options will be included.
    """
    distributor = make_esri_distributor()

    portal_url = f"{portal_endpoint}/home/item.html?id={item_id}"
    service_url = f"{server_endpoint}/rest/services/{service_name}/FeatureServer"
    distributions = [
        Distribution(
            distributor=distributor,
            format=Format(
                format="ArcGIS Feature Service",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=service_url,
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS feature service.",
                )
            ),
        ),
        Distribution(
            distributor=distributor,
            format=Format(
                format="ArcGIS Feature Layer",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=portal_url,
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS feature layer.",
                )
            ),
        ),
    ]

    if item_ogc_id:
        ogc_features_layer_url = f"{portal_endpoint}/home/item.html?id={item_ogc_id}"
        ogc_features_service_url = f"{server_endpoint}/rest/services/{service_name}/OGCFeatureServer"
        distributions.extend(
            [
                Distribution(
                    distributor=distributor,
                    format=Format(
                        format="OGC API Features Service",
                        href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
                    ),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(
                            href=ogc_features_service_url,
                            function=OnlineResourceFunctionCode.DOWNLOAD,
                            title="ArcGIS Online",
                            description="Access information as an OGC API feature service.",
                        )
                    ),
                ),
                Distribution(
                    distributor=distributor,
                    format=Format(
                        format="ArcGIS OGC Feature Layer",
                        href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
                    ),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(
                            href=ogc_features_layer_url,
                            function=OnlineResourceFunctionCode.DOWNLOAD,
                            title="ArcGIS Online",
                            description="Access information as an ArcGIS OGC feature layer.",
                        )
                    ),
                ),
            ]
        )

    return distributions
