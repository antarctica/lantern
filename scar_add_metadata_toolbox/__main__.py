from datetime import datetime, date
from pathlib import Path

# noinspection PyPackageRequirements
# Exempting Bandit security issue (Using Element to parse untrusted XML data is known to be vulnerable to XML attacks)
#
# We don't currently allow untrusted/user-provided XML so this is not a risk
from lxml.etree import ElementTree, ProcessingInstruction, fromstring, tostring  # nosec

from bas_metadata_library.standards.iso_19115_2_v1 import MetadataRecordConfig, MetadataRecord

minimal_record_config = {
    "file_identifier": "86bd7a1a-845d-48a9-8d71-59fdf7290556",
    "language": "eng",
    "character_set": "utf8",
    "hierarchy_level": "dataset",
    "contacts": [
        {
            "organisation": {"name": "British Antarctic Survey"},
            # "position": "Mapping and Geographic Information Centre",
            "phone": "+44 (0)1223 221400",
            "address": {
                "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                "city": "Cambridge",
                "administrative_area": "Cambridgeshire",
                "postal_code": "CB3 0ET",
                "country": "United Kingdom",
            },
            "email": "magic@bas.ac.uk",
            "role": ["pointOfContact"],
        }
    ],
    "date_stamp": datetime.utcnow(),
    "maintenance": {"maintenance_frequency": "asNeeded", "progress": "underDevelopment"},
    "metadata_standard": {"name": "ISO 19115", "version": "1.0"},
    "reference_system_info": {"code": {"value": "urn:ogc:def:crs:EPSG::3031"}},
    "resource": {
        "title": {"value": "Antarctic Coastline (Polygon)"},
        "dates": [{"date": date(2020, 4, 2), "date_precision": "year", "date_type": "creation"}],
        "abstract": "Coastline of Antarctica encoded as a polygon. This abstract, and the dataset to which it belongs, "
        "is fictitious. This is a candidate record to develop and validate discovery level metadata for "
        "SCAR Antarctic Digital Database (ADD) datasets. See the ADD website for real datasets "
        "(https://add.scar.org).",
        "contacts": [
            {
                "individual": {"name": "Watson, Constance"},
                "organisation": {"name": "British Antarctic Survey"},
                "email": "conwat@bas.ac.uk",
                "role": ["author"],
            }
        ],
        "keywords": [{"terms": [{"term": "Land Cover"}], "type": "theme"}],
        "maintenance": {"maintenance_frequency": "biannually", "progress": "completed"},
        "constraints": {
            "access": [{"restriction_code": "otherRestrictions"}],
            "usage": [
                {
                    "copyright_licence": {
                        "statement": "This information is licensed under the Create Commons Attribution 4.0 "
                        "International Licence (CC BY 4.0). To view this licence, visit "
                        "https://creativecommons.org/licenses/by/4.0/",
                    }
                }
            ],
        },
        "spatial_representation_type": "vector",
        "character_set": "utf8",
        "language": "eng",
        "topics": ["environment", "climatologyMeteorologyAtmosphere"],
        "extent": {
            "geographic": {
                "bounding_box": {
                    "west_longitude": -45.61521,
                    "east_longitude": -27.04976,
                    "south_latitude": -68.1511,
                    "north_latitude": -54.30761,
                }
            },
            "temporal": {"period": {"start": datetime(2020, 4, 2, 0, 0), "end": datetime(2020, 4, 2, 0, 0)}},
        },
        "formats": [
            {"format": "Web Map Service"},
            {"format": "GeoPackage"},
            {"format": "Shapefile"},
            {"format": "CSV"},
        ],
        "transfer_options": [
            {
                "online_resource": {
                    "href": "https://example.com/ogc/wms?layer=add-coastline-polygon",
                    "title": "Web Map Service (WMS)",
                    "description": "Access information as a OGC Web Map Service layer",
                    "function": "download",
                }
            },
            {
                "online_resource": {
                    "href": "https://example.com/data/add-coastline-polygon.gpkg",
                    "title": "GeoPackage",
                    "description": "Download information as a OGC GeoPackage",
                    "function": "download",
                }
            },
            {
                "online_resource": {
                    "href": "https://example.com/data/add-coastline-polygon.shp.zip",
                    "title": "GeoPackage",
                    "description": "Download information as an ESRI Shapefile",
                    "function": "download",
                }
            },
            {
                "online_resource": {
                    "href": "https://example.com/data/add-coastline-polygon.csv",
                    "title": "CSV",
                    "description": "Download information as a Comma Separated Value file",
                    "function": "download",
                }
            },
        ],
        "lineage": "This dataset is fictitious and does not exist, it therefore has no lineage",
    },
}
configuration = MetadataRecordConfig(**minimal_record_config)

record = MetadataRecord(configuration=configuration)
document = record.generate_xml_document()

record_iso_html = ElementTree(fromstring(document))
record_iso_html_root = record_iso_html.getroot()
record_iso_html_root.addprevious(
    ProcessingInstruction(
        "xml-stylesheet", 'type="text/xsl" href="http://localhost:9000/stylesheets/iso-html/xml-to-html-ISO.xsl"',
    )
)
document_iso_html = tostring(record_iso_html, pretty_print=True, xml_declaration=True, encoding="utf-8")


record_iso_rubric = ElementTree(fromstring(document))
record_iso_rubric_root = record_iso_rubric.getroot()
record_iso_rubric_root.addprevious(
    ProcessingInstruction(
        "xml-stylesheet", 'type="text/xsl" href="http://localhost:9000/stylesheets/iso-rubric/isoRubricHTML.xsl"',
    )
)
document_iso_rubric = tostring(record_iso_rubric, pretty_print=True, xml_declaration=True, encoding="utf-8")


if __name__ == "__main__":
    with open(Path("output/candidate-record.xml"), "w") as file:
        file.write(document.decode())

    with open(Path("output/candidate-record-iso-html.xml"), "w") as file:
        file.write(document_iso_html.decode())

    with open(Path("output/candidate-record-iso-rubric.xml"), "w") as file:
        file.write(document_iso_rubric.decode())
