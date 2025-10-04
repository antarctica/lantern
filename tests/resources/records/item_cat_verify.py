from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Format,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.enums import (
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from tests.resources.records.utils import make_record

# A record with all distinct verification distribution options.

abstract = """
Item to test all VerificationDistributionType enum members:

- open/regular files
- ArcGIS Layers
- ArcGIS Services
- NORA file
- SharePoint file
- published map purchase option

Distribution option URLs all need to parse as URLs. Some must match a specific format to be matched to the right enum.
"""

file_formats = [
    "https://www.iana.org/assignments/media-types/text/csv",
    "https://metadata-resources.data.bas.ac.uk/media-types/application/fpl+xml",
    "https://www.iana.org/assignments/media-types/application/geo+json",
    "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
    "https://metadata-resources.data.bas.ac.uk/media-types/application/gpx+xml",
    "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
    "https://www.iana.org/assignments/media-types/image/jpeg",
    "https://www.iana.org/assignments/media-types/application/vnd.mapbox-vector-tile",
    "https://www.iana.org/assignments/media-types/application/pdf",
    "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
    "https://www.iana.org/assignments/media-types/image/png",
    "https://metadata-resources.data.bas.ac.uk/media-types/application/vnd.shp+zip",
]
file_url = "https://example.com/x"
file_distributions = [
    Distribution(
        distributor=Contact(
            organisation=ContactIdentity(
                name="Mapping and Geographic Information Centre, British Antarctic Survey",
                href="https://ror.org/01rhff309",
                title="ror",
            ),
            phone="+44 (0)1223 221400",
            email="magic@bas.ac.uk",
            address=Address(
                delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                city="Cambridge",
                administrative_area="Cambridgeshire",
                postal_code="CB3 0ET",
                country="United Kingdom",
            ),
            online_resource=OnlineResource(
                href="https://www.bas.ac.uk/teams/magic",
                title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                function=OnlineResourceFunctionCode.INFORMATION,
            ),
            role={ContactRoleCode.DISTRIBUTOR},
        ),
        format=Format(
            format="-",
            href=file_format,
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=15),
            online_resource=OnlineResource(
                href=file_url,
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="-",
                description="Verify distribution as a file.",
            ),
        ),
    )
    for file_format in file_formats
]

arc_layer_formats = [
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
]
arc_layer_url = "https://example.com/x"
arc_layer_distributions = [
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
            format="-",
            href=arc_layer,
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="-",
                description="Verify distribution as an ArcGIS layer item.",
            )
        ),
    )
    for arc_layer in arc_layer_formats
]

arc_service_formats = [
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
]
arc_service_url = "https://example.com/x"
arc_service_distributions = [
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
            format="-",
            href=arc_service,
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="-",
                description="Verify distribution as an ArcGIS service item.",
            )
        ),
    )
    for arc_service in arc_service_formats
]

nora_file = Distribution(
    distributor=Contact(
        organisation=ContactIdentity(
            name="NERC Open Research Archive",
            href="https://ror.org/02b5d8509",
            title="ror",
        ),
        email="nora.nerc@bgs.ac.uk",
        online_resource=OnlineResource(
            href="https://nora.nerc.ac.uk/information.html",
            title="About this repository - NERC Open Research Archive",
            description="General information about the NERC Open Research Archive (NORA) from the NORA website.",
            function=OnlineResourceFunctionCode.INFORMATION,
        ),
        role={ContactRoleCode.DISTRIBUTOR},
    ),
    format=Format(
        format="-",
        href="https://www.iana.org/assignments/media-types/application/pdf",
    ),
    transfer_option=TransferOption(
        size=Size(unit="bytes", magnitude=15),
        online_resource=OnlineResource(
            href="https://nora.nerc.ac.uk/x",
            function=OnlineResourceFunctionCode.DOWNLOAD,
            title="-",
            description="Verify distribution as a NORA hosted file.",
        ),
    ),
)

sharepoint_file = Distribution(
    distributor=Contact(
        organisation=ContactIdentity(name="Microsoft Corporation", href="https://ror.org/00d0nc645", title="ror"),
        address=Address(
            delivery_point="1 Microsoft Way, Bldg 37",
            city="Redmond",
            administrative_area="Washington",
            postal_code="98052",
            country="United States of America",
        ),
        online_resource=OnlineResource(
            href="https://www.microsoft.com",
            title="Microsoft - AI, Cloud, Productivity, Computing, Gaming & Apps",
            description="Corporate website for Microsoft.",
            function=OnlineResourceFunctionCode.INFORMATION,
        ),
        role={ContactRoleCode.DISTRIBUTOR},
    ),
    format=Format(
        format="-",
        href="https://www.iana.org/assignments/media-types/application/pdf",
    ),
    transfer_option=TransferOption(
        size=Size(unit="bytes", magnitude=15),
        online_resource=OnlineResource(
            href="https://example-my.sharepoint.com/:b:/r/personal/conwat_example_com/Documents/x.pdf",
            function=OnlineResourceFunctionCode.DOWNLOAD,
            title="-",
            description="Verify distribution as a SharePoint hosted file.",
        ),
    ),
)

map_purchase = Distribution(
    distributor=Contact(
        organisation=ContactIdentity(
            name="Mapping and Geographic Information Centre, British Antarctic Survey",
            href="https://ror.org/01rhff309",
            title="ror",
        ),
        phone="+44 (0)1223 221400",
        email="magic@bas.ac.uk",
        address=Address(
            delivery_point="British Antarctic Survey, High Cross, Madingley Road",
            city="Cambridge",
            administrative_area="Cambridgeshire",
            postal_code="CB3 0ET",
            country="United Kingdom",
        ),
        online_resource=OnlineResource(
            href="https://www.bas.ac.uk/teams/magic",
            title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
            description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
            function=OnlineResourceFunctionCode.INFORMATION,
        ),
        role={ContactRoleCode.DISTRIBUTOR},
    ),
    transfer_option=TransferOption(
        online_resource=OnlineResource(
            href="https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/",
            function=OnlineResourceFunctionCode.ORDER,
            title="Map ordering information - BAS public website",
            description="Access information on how to order item.",
        ),
    ),
)

record = make_record(
    file_identifier="cf80b941-3de6-4a04-8f5a-a2349c1e3ae0",
    hierarchy_level=HierarchyLevelCode.DATASET,
    title="Test Resource - Item to test verification download types",
    abstract=abstract,
    purpose="Item to test all distinct verification download types.",
)
record.distribution = [
    *file_distributions,
    *arc_layer_distributions,
    *arc_service_distributions,
    nora_file,
    sharepoint_file,
    map_purchase,
]
