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
            "organisation": {"name": "British Antarctic Survey", "href": "https://ror.org/01rhff309", "title": "ror"},
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
            "online_resource": {
                "href": "https://www.bas.ac.uk/team/business-teams/mapping-and-geographic-information/",
                "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) "
                "from the British Antarctic Survey (BAS) public website.",
                "function": "information",
            },
            "role": ["pointOfContact"],
        }
    ],
    "date_stamp": datetime.utcnow(),
    "maintenance": {"maintenance_frequency": "asNeeded", "progress": "underDevelopment"},
    "metadata_standard": {"name": "ISO 19115", "version": "1.0"},
    "reference_system_info": {
        "code": {"value": "urn:ogc:def:crs:EPSG::3031", "href": "http://www.opengis.net/def/crs/EPSG/0/4326"},
        "version": "6.18.3",
        "authority": {
            "title": {"value": "European Petroleum Survey Group (EPSG) Geodetic Parameter Registry"},
            "dates": [{"date": date(2008, 11, 12), "date_type": "publication"}],
            "contact": {
                "organisation": {"name": "European Petroleum Survey Group"},
                "email": "EPSGadministrator@iogp.org",
                "online_resource": {
                    "href": "https://www.epsg-registry.org/",
                    "title": "EPSG Geodetic Parameter Dataset",
                    "description": "The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate "
                    "Reference Systems and Coordinate Transformations, accessible through this online registry",
                    "function": "information",
                },
                "role": ["publisher"],
            },
        },
    },
    "resource": {
        "title": {"value": "Antarctic Coastline (Polygon)"},
        "dates": [{"date": date(2020, 4, 2), "date_precision": "year", "date_type": "creation"}],
        "abstract": "Coastline of Antarctica encoded as a polygon. This abstract, and the dataset to which it belongs, "
        "is fictitious. This is a candidate record to develop and validate discovery level metadata for "
        "SCAR Antarctic Digital Database (ADD) datasets. See the ADD website for real datasets "
        "(https://add.scar.org).",
        "edition": "1",
        "contacts": [
            {
                "individual": {
                    "name": "Watson, Constance",
                    "href": "https://sandbox.orcid.org/0000-0001-8373-6934",
                    "title": "orcid",
                },
                "organisation": {"name": "British Antarctic Survey"},
                "email": "conwat@bas.ac.uk",
                "online_resource": {
                    "href": "https://sandbox.orcid.org/0000-0001-8373-6934",
                    "title": "ORCID record",
                    "description": "ORCID is an open, non-profit, community-driven effort to create and maintain a "
                    "registry of unique researcher identifiers and a transparent method of linking research activities "
                    "and outputs to these identifiers.",
                    "function": "information",
                },
                "role": ["author"],
            }
        ],
        "keywords": [
            {
                "terms": [{"term": "Land Cover", "href": "https://www.eionet.europa.eu/gemet/en/inspire-theme/lc"}],
                "thesaurus": {
                    "title": {
                        "value": "General Multilingual Environmental Thesaurus - INSPIRE themes",
                        "href": "http://www.eionet.europa.eu/gemet/inspire_themes",
                    },
                    "dates": [{"date": date(2018, 8, 16), "date_type": "publication"}],
                    "edition": "4.1.2",
                    "contact": {
                        "organisation": {
                            "name": "European Environment Information and Observation Network (EIONET), "
                            "European Environment Agency (EEA)",
                            "href": "https://ror.org/02k4b9v70",
                            "title": "ror",
                        },
                        "email": "helpdesk@eionet.europa.eu",
                        "online_resource": {
                            "href": "https://www.eionet.europa.eu/gemet/en/themes/",
                            "title": "GEMET INSPIRE Spatial Data Themes  General Multilingual Environmental Thesaurus",
                            "description": "GEMET, the GEneral Multilingual Environmental Thesaurus, has been "
                            "developed as a multilingual thesauri for indexing, retrieval and control of terms in "
                            "order to save time, energy and funds",
                            "function": "information",
                        },
                        "role": ["publisher"],
                    },
                },
                "type": "theme",
            }
        ],
        "maintenance": {"maintenance_frequency": "biannually", "progress": "completed"},
        "constraints": {
            "access": [
                {"restriction_code": "otherRestrictions", "inspire_limitations_on_public_access": "noLimitations"}
            ],
            "usage": [
                {
                    "copyright_licence": {
                        # "code": "CC-BY-4.0",
                        "statement": "This information is licensed under the Create Commons Attribution 4.0 "
                        "International Licence (CC BY 4.0). To view this licence, visit "
                        "https://creativecommons.org/licenses/by/4.0/",
                        "href": "https://creativecommons.org/licenses/by/4.0/",
                    }
                }
            ],
        },
        "spatial_representation_type": "vector",
        "character_set": "utf8",
        "language": "eng",
        "topics": ["environment", "environment"],
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
                "size": {"unit": "MB", "magnitude": 20},
                "online_resource": {
                    "href": "https://example.com/data/add-coastline-polygon.gpkg",
                    "title": "GeoPackage",
                    "description": "Download information as a OGC GeoPackage.",
                    "function": "download",
                },
            },
            {
                "size": {"unit": "MB", "magnitude": 25},
                "online_resource": {
                    "href": "https://example.com/data/add-coastline-polygon.shp.zip",
                    "title": "GeoPackage",
                    "description": "Download information as an ESRI Shapefile.",
                    "function": "download",
                },
            },
            {
                "size": {"unit": "MB", "magnitude": 2},
                "online_resource": {
                    "href": "https://example.com/data/add-coastline-polygon.csv",
                    "title": "CSV",
                    "description": "Download information as a Comma Separated Value file.",
                    "function": "download",
                },
            },
        ],
        "measures": [
            {
                "code": "Conformity_001",
                "code_space": "INSPIRE",
                "pass": True,
                "title": {
                    "value": "Commission Regulation (EU) No 1089/2010 of 23 November 2010 implementing Directive "
                    "2007/2/EC of the European Parliament and of the Council as regards interoperability of "
                    "spatial data sets and services",
                    "href": "http://data.europa.eu/eli/reg/2010/1089",
                },
                "dates": [{"date": date(2010, 12, 8), "date_type": "publication"}],
                "explanation": "See the referenced specification",
            }
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
