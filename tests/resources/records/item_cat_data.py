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

# A record with all supported distribution options.

abstract = """
Item to test all supported data formats:

- ArcGIS Feature Layer
- ArcGIS OGC Feature Layer
- ArcGIS Raster Tile Layer
- ArcGIS Vector Tile Layer
- GeoJSON
- GeoPackage (optional compression)
- PNG
- PDF (optional georeferenced)
- Shapefile (required compression)
"""
record = make_record(
    file_identifier="f90013f6-2893-4c72-953a-a1a6bc1919d7",
    hierarchy_level=HierarchyLevelCode.DATASET,
    title="Test Resource - Item to test data formats",
    abstract=abstract,
    purpose="Item to test all supported data formats are recognised and presented correctly.",
)
record.distribution = [
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
            format="ArcGIS Feature Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS feature service.",
            )
        ),
    ),
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
            format="ArcGIS Feature Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS feature layer.",
            )
        ),
    ),
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
            format="OGC API Features Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="y",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an OGC API feature service.",
            )
        ),
    ),
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
            format="ArcGIS OGC Feature Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="y",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS OGC feature layer.",
            )
        ),
    ),
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
            format="ArcGIS Raster Tile Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="za",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS raster tile layer.",
            )
        ),
    ),
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
            format="ArcGIS Raster Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="za",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS raster tile service.",
            )
        ),
    ),
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
            format="ArcGIS Vector Tile Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="z",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS vector tile layer.",
            )
        ),
    ),
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
            format="ArcGIS Vector Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="z",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS vector tile service.",
            )
        ),
    ),
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
            format="GeoJSON",
            href="https://www.iana.org/assignments/media-types/application/geo+json",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=24 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="GeoJSON",
                description="Access information as a GeoJSON file.",
            ),
        ),
    ),
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
            format="GeoPackage",
            href="https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=21 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="GeoJSON",
                description="Access information as a GeoPackage file.",
            ),
        ),
    ),
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
            format="GeoPackage (Zipped)",
            href="https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=18 * 1024 * 1024 * 1024 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="GeoJSON (Zipped)",
                description="Access information as a GeoPackage file compressed as a Zip archive.",
            ),
        ),
    ),
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
            format="JPEG",
            href="https://jpeg.org/jpeg/",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=15 * 1024 * 1024 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="JPEG",
                description="Access information as a JPEG image.",
            ),
        ),
    ),
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
            format="PDF",
            href="https://www.iana.org/assignments/media-types/application/pdf",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=12 * 1024 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="PDF",
                description="Access information as a PDF file.",
            ),
        ),
    ),
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
            format="PDF (Georeferenced)",
            href="https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=9 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="PDF (Georeferenced)",
                description="Access information as a PDF file with georeferencing.",
            ),
        ),
    ),
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
            format="PNG",
            href="https://www.iana.org/assignments/media-types/image/png",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=6 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="PNG",
                description="Access information as a PNG image.",
            ),
        ),
    ),
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
            format="Shapefile (Zipped)",
            href="https://metadata-resources.data.bas.ac.uk/media-types/application/vnd.shp+zip",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=3),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="Shapefile (Zipped)",
                description="Access information as a Shapefile compressed as a Zip archive.",
            ),
        ),
    ),
]
