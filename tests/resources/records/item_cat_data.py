from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse

from lantern.lib.magic_distribution.models.artefact import ArtefactLocalFile
from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    Identifier,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Distributions,
    Format,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.models.item.catalogue.enums import DistributionType
from lantern.models.record.const import CATALOGUE_NAMESPACE
from tests.resources.records.utils import make_record

# An open-access record to test all supported data formats.

file_identifier = "f90013f6-2893-4c72-953a-a1a6bc1919d7"

abstract = """
Item to test all supported data formats:

- ArcGIS Feature Layer
- ArcGIS OGC Feature Layer
- ArcGIS Raster Tile Layer
- ArcGIS Vector Tile Layer
- ArcGIS Scene Layer
- ArcGIS Web Map
- BAS SAN (not format based/aware)
- BAS Paper Map ordering (not format based/aware)

> [!NOTE]
> Downloads for these formats link against
> [Sample Artefacts](https://github.com/antarctica/lantern/blob/main/docs/dev.md#test-artefacts) but with exaggerated
> file sizes to test the 'humanise' logic used when file sizes are expressed in bytes.

- CSV
- FPL
- GeoPackage (optional compression)
- GPX
- JPEG
- GeoJSON (required geospatial)
- Mapbox Vector Tiles
- PNG
- PDF (optional georeferencing)
- Shapefile (required compression)
- GeoTIFF (required georeferencing)
"""


def _make_dist_opt_for_artefact(path: Path, fake_size: int | None = None) -> Distribution:
    """
    Generate a record distribution option for a given sample artefact.

    It is assumed `path` is to a sample file in, and relative to, ./tests/resources/artefacts/` (which is accessible
    through the test site at `/.sample-artefacts/`). For example `path=Path('csv/sample.csv')`.

    For simulating file size handling for larger files, the file size can optionally be overridden with a fake value.
    """
    file_path = Path(__file__).parent.parent / "artefacts" / path
    artefact = ArtefactLocalFile(resource_id=file_identifier, artefact_path=file_path)
    params = {"sha256": artefact.sha256, "quickxor": artefact.quickxor}
    href = urlunparse(urlparse(str(Path("/.sample-artefacts") / path))._replace(query=urlencode(params)))

    return Distribution(
        distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
        format=artefact.distribution_format,
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href=href,
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title=artefact.format.name,
                description=artefact.format.description,
            ),
            size=Size(unit="bytes", magnitude=fake_size or file_path.stat().st_size),
        ),
    )


distributions = {
    "ArcGIS Feature Layer": Distribution(
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
            format=DistributionType.ARCGIS_FEATURE_LAYER.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.INFORMATION,
                title="ArcGIS Online",
                description="Access information as an ArcGIS feature layer.",
            )
        ),
    ),
    "ArcGIS Feature Service": Distribution(
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
            format=DistributionType.ARCGIS_FEATURE_LAYER.value.replace("Layer", "Service"),
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
    "ArcGIS OGC Feature Layer": Distribution(
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
            format=DistributionType.ARCGIS_OGC_FEATURE_LAYER.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="y",
                function=OnlineResourceFunctionCode.INFORMATION,
                title="ArcGIS Online",
                description="Access information as an ArcGIS OGC feature layer.",
            )
        ),
    ),
    "OGC API Features Service": Distribution(
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
            format=DistributionType.ARCGIS_OGC_FEATURE_LAYER.value.replace("(ArcGIS) Layer", "Service"),
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
    "ArcGIS Raster Tile Layer": Distribution(
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
            format=DistributionType.ARCGIS_RASTER_TILE_LAYER.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="za",
                function=OnlineResourceFunctionCode.INFORMATION,
                title="ArcGIS Online",
                description="Access information as an ArcGIS raster tile layer.",
            )
        ),
    ),
    "ArcGIS Raster Tile Service": Distribution(
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
            format=DistributionType.ARCGIS_RASTER_TILE_LAYER.value.replace("Layer", "Service"),
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
    "ArcGIS Vector Tile Layer": Distribution(
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
            format=DistributionType.ARCGIS_VECTOR_TILE_LAYER.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="z",
                function=OnlineResourceFunctionCode.INFORMATION,
                title="ArcGIS Online",
                description="Access information as an ArcGIS vector tile layer.",
            )
        ),
    ),
    "ArcGIS Vector Tile Service": Distribution(
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
            format=DistributionType.ARCGIS_VECTOR_TILE_LAYER.value.replace("Layer", "Service"),
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
    "ArcGIS Scene Layer": Distribution(
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
            format=DistributionType.ARCGIS_SCENE_LAYER.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+scene",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="s",
                function=OnlineResourceFunctionCode.INFORMATION,
                title="ArcGIS Online",
                description="Access information as an ArcGIS 3D scene layer.",
            )
        ),
    ),
    "ArcGIS Scene Service": Distribution(
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
            format="ArcGIS 3D Scene Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+scene",
        ),
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="s",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="ArcGIS Online",
                description="Access information as an ArcGIS 3D scene service.",
            )
        ),
    ),
    "ArcGIS Web Map": Distribution(
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
    ),
    "CSV": _make_dist_opt_for_artefact(path=Path("csv/sample.csv"), fake_size=12 * 1024),
    "FPL": _make_dist_opt_for_artefact(path=Path("fpl/sample.fpl"), fake_size=12 * 1024 * 1024),
    "GeoPackage": _make_dist_opt_for_artefact(
        path=Path("gpkg/sample.gpkg"), fake_size=21 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024
    ),
    "GeoPackage (Zipped)": _make_dist_opt_for_artefact(
        path=Path("gpkg_zip/sample.gpkg.zip"), fake_size=18 * 1024 * 1024 * 1024 * 1024 * 1024
    ),
    "GPX": _make_dist_opt_for_artefact(path=Path("gpx/sample.gpx"), fake_size=12 * 1024 * 1024 * 1024),
    "JPEG": _make_dist_opt_for_artefact(path=Path("jpeg/sample.jpg"), fake_size=15 * 1024 * 1024 * 1024 * 1024),
    "GeoJSON": _make_dist_opt_for_artefact(
        path=Path("geojson/sample.json"), fake_size=24 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024
    ),
    "MapBox Vector Tile": _make_dist_opt_for_artefact(path=Path("mbtiles/sample.mbtiles"), fake_size=16 * 1024 * 1024),
    "PDF": _make_dist_opt_for_artefact(path=Path("pdf/sample.pdf"), fake_size=12 * 1024 * 1024 * 1024),
    "PDF (GeoReferenced)": _make_dist_opt_for_artefact(path=Path("pdf_geo/sample.pdf"), fake_size=9 * 1024 * 1024),
    "PNG": _make_dist_opt_for_artefact(path=Path("png/sample.png"), fake_size=6 * 1024),
    "Shapefile (Zipped)": _make_dist_opt_for_artefact(path=Path("shp_zip/sample.shp.zip"), fake_size=3),
    "GeoTIFF": _make_dist_opt_for_artefact(path=Path("tiff_geo/sample.tiff"), fake_size=36 * 1024 * 1024 * 1024 * 1024),
    "X - BAS Published Map Ordering": Distribution(
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
                href="https://data.bas.ac.uk/guides/map-purchasing/",
                function=OnlineResourceFunctionCode.ORDER,
                title="Map ordering information - BAS public website",
            ),
        ),
    ),
    "X - BAS SAN Access": Distribution(
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
                href="sftp://san.nerc-bas.ac.uk/data/x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                # title deliberately not set to use default value in distribution option
            ),
        ),
    ),
}

record = make_record(
    open_access=True,
    file_identifier="f90013f6-2893-4c72-953a-a1a6bc1919d7",
    hierarchy_level=HierarchyLevelCode.DATASET,
    title="Test Resource - Item to test data formats",
    abstract=abstract,
    purpose="Item to test all supported data formats are recognised and presented correctly.",
)
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="57327327-4623-4247-af86-77fb43b7f45b",
            href=f"https://{CATALOGUE_NAMESPACE}/items/57327327-4623-4247-af86-77fb43b7f45b",
            namespace=CATALOGUE_NAMESPACE,
        ),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
    )
)

record.distribution = Distributions(distributions.values())
