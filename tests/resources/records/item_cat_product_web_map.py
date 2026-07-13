from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    Identifier,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.models.item.catalogue.enums import DistributionType
from lantern.models.record.const import CATALOGUE_NAMESPACE
from tests.resources.records.utils import make_record, relate_products

# An open-access record for a web map product.


record = make_record(
    open_access=True,
    file_identifier="a59b5c5b-b099-4f01-b670-3800cb65e666",
    hierarchy_level=HierarchyLevelCode.WEB_MAP_PRODUCT,
    title="Test Resource - Web Map Product",
    abstract="Item to test a Product for a Web Map is presented correctly.",
)
# add related peers
record.identification.aggregations.extend(relate_products(record.file_identifier))
# add child layers
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(identifier="e0743576-e05d-49cd-b7bf-01a0b3ad0430", namespace=CATALOGUE_NAMESPACE),
        association_type=AggregationAssociationCode.IS_COMPOSED_OF,
        initiative_type=AggregationInitiativeCode.MAP_LAYER,
    )
)
# add web map distribution option
record.distribution.append(
    Distribution(
        distributor=Contact(
            organisation=ContactIdentity(
                name="Environmental Systems Research Institute", href="https://ror.org/0428exr50", title="ror"
            ),
            address=Address(
                delivery_point="380 New York Street",
                city="Redlands",
                administrative_area="California",
                postal_code="92373",
                country="United States of America",
            ),
            online_resource=OnlineResource(
                href="https://www.esri.com",
                title="GIS Mapping Software, Location Intelligence & Spatial Analytics | Esri",
                description="Corporate website for Environmental Systems Research Institute (ESRI).",
                function=OnlineResourceFunctionCode.INFORMATION,
            ),
            role={ContactRoleCode.DISTRIBUTOR},
        ),
        format=Format(
            format=DistributionType.ARCGIS_WEBMAP.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+webmap",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="wm",
                function=OnlineResourceFunctionCode.INFORMATION,
                title="ArcGIS Online",
                description="Access information as an ArcGIS scene service.",
            )
        ),
    )
)
