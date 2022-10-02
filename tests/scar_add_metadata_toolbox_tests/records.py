from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord, MetadataRecordConfigV3


def make_test_record_config(
    identifier: str, title: str, hierarchy_level: str, item_identifiers: Optional[List[str]] = None
) -> dict:
    config = {
        "$schema": "https://metadata-standards.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v3.json",
        "file_identifier": identifier,
        "metadata": {
            "language": "eng",
            "character_set": "utf-8",
            "contacts": [
                {
                    "organisation": {
                        "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                        "href": "https://ror.org/01rhff309",
                        "title": "ror",
                    },
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
                        "href": "https://www.bas.ac.uk/team/magic",
                        "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                        "description": "General information about the BAS Mapping and Geographic Information Centre "
                        "(MAGIC) from the British Antarctic Survey (BAS) public website.",
                        "function": "information",
                    },
                    "role": ["pointOfContact"],
                }
            ],
            "date_stamp": date(2020, 5, 25),
            "metadata_standard": {
                "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                "version": "ISO 19115-2:2009(E)",
            },
            "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
        },
        "identification": {
            "title": {"value": title},
            "dates": {
                "creation": {"date": date(2020, 1, 1), "date_precision": "year"},
                "revision": {"date": date(2020, 2, 26)},
                "publication": {"date": datetime(2020, 1, 15, 10, 44, 14)},
                "released": {"date": date(2020, 2, 26)},
            },
            "edition": "1.2",
            "abstract": title,
            "contacts": [
                {
                    "individual": {
                        "name": "Watson, Constance",
                        "href": "https://sandbox.orcid.org/0000-0001-8373-6934",
                        "title": "orcid",
                    },
                    "organisation": {
                        "name": "British Antarctic Survey",
                        "href": "https://ror.org/01rhff309",
                        "title": "ror",
                    },
                    "email": "conwat@bas.ac.uk",
                    "online_resource": {
                        "href": "https://sandbox.orcid.org/0000-0001-8373-6934",
                        "title": "ORCID record",
                        "description": "ORCID is an open, non-profit, community-driven effort to create and maintain a "
                        "registry of unique researcher identifiers and a transparent method of linking "
                        "research activities and outputs to these identifiers.",
                        "function": "information",
                    },
                    "role": ["author"],
                },
                {
                    "organisation": {
                        "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                        "href": "https://ror.org/01rhff309",
                        "title": "ror",
                    },
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
                        "href": "https://www.bas.ac.uk/team/magic",
                        "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                        "description": "General information about the BAS Mapping and Geographic Information Centre "
                        "(MAGIC) from the British Antarctic Survey (BAS) public website.",
                        "function": "information",
                    },
                    "role": ["publisher", "pointOfContact"],
                },
            ],
            "maintenance": {"maintenance_frequency": "biannually", "progress": "completed"},
            "keywords": [
                {
                    "terms": [
                        {
                            "term": "STUFF",
                            "href": "https://www.eionet.europa.eu/gemet/en/inspire-theme/st",
                        }
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "General Multilingual Environmental Thesaurus - INSPIRE themes",
                            "href": "http://www.eionet.europa.eu/gemet/inspire_themes",
                        },
                        "dates": {"publication": {"date": date(2008, 8, 16)}},
                        "edition": "4.1.2",
                        "contact": {
                            "organisation": {
                                "name": "European Environment Information and Observation Network (EIONET), European "
                                "Environment Agency (EEA)",
                                "href": "https://ror.org/02k4b9v70",
                                "title": "ror",
                            },
                            "email": "helpdesk@eionet.europa.eu",
                            "online_resource": {
                                "href": "https://www.eionet.europa.eu/gemet/en/themes/",
                                "title": "GEMET INSPIRE Spatial Data Themes  General Multilingual Environmental Thesaurus",
                                "description": "GEMET, the GEneral Multilingual Environmental Thesaurus, has been "
                                "developed as a multilingual thesauri for indexing, retrieval and "
                                "control of terms in order to save time, energy and funds.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                },
                {
                    "terms": [
                        {
                            "term": "TOPOGRAPHY",
                            "href": "https://gcmd.earthdata.nasa.gov/kms/concept/3e822484-c94a-457b-a32f-376fcbd6fd35",
                        },
                        {
                            "term": "STUFF",
                            "href": "https://gcmd.earthdata.nasa.gov/kms/concept/c4992969-05db-4bb6-9dac-d35535503650",
                        },
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "Global Change Master Directory (GCMD) Science Keywords",
                            "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                        },
                        "dates": {"publication": {"date": date(2020, 1, 9)}},
                        "edition": "9.1",
                        "contact": {
                            "organisation": {
                                "name": "Global Change Data Center, Science and Exploration Directorate, Goddard Space "
                                "Flight Center (GSFC) National Aeronautics and Space Administration (NASA)",
                                "href": "https://ror.org/027ka1x80",
                                "title": "ror",
                            },
                            "address": {
                                "city": "Greenbelt",
                                "administrative_area": "MD",
                                "country": "United States of America",
                            },
                            "online_resource": {
                                "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                                "title": "Global Change Master Directory (GCMD) Keywords",
                                "description": "The information provided on this page seeks to define how the GCMD "
                                "Keywords are structured, used and accessed. It also provides "
                                "information on how users can participate in the further development of "
                                "the keywords.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                },
                {
                    "terms": [
                        {
                            "term": "Topographic mapping",
                            "href": "http://vocab.nerc.ac.uk/collection/T01/current/9cd3118f-55e2-4c07-b9f4-e260e40e8eb2/1/",
                        }
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "British Antarctic Survey research topics",
                            "href": "http://vocab.nerc.ac.uk/collection/T01/current/",
                        },
                        "dates": {"publication": {"date": date(2020, 5, 6)}},
                        "edition": "1",
                        "contact": {
                            "organisation": {
                                "name": "UK Polar Data Centre, British Antarctic Survey",
                                "href": "https://ror.org/01rhff309",
                                "title": "ror",
                            },
                            "phone": "+44 (0)1223 221400",
                            "address": {
                                "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                "city": "Cambridge",
                                "administrative_area": "Cambridgeshire",
                                "postal_code": "CB3 0ET",
                                "country": "United Kingdom",
                            },
                            "email": "polardatacentre@bas.ac.uk",
                            "online_resource": {
                                "href": "https://www.bas.ac.uk/team/business-teams/information-services/uk-polar-data-centre/",
                                "title": "UK Polar Data Centre (UK PDC) - BAS public website",
                                "description": "General information about the NERC Polar Data Centre (UK PDC) from the "
                                "British Antarctic Survey (BAS) public website.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                },
                {
                    "terms": [
                        {
                            "term": "Antarctic Digital Database",
                            "href": "http://vocab.nerc.ac.uk/collection/T02/current/8e91de62-b6e3-402e-b11f-73d2c1f37cff/",
                        }
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "British Antarctic Survey data catalogue collections",
                            "href": "http://vocab.nerc.ac.uk/collection/T02/current/",
                        },
                        "dates": {"publication": {"date": date(2020, 5, 5)}},
                        "edition": "1",
                        "contact": {
                            "organisation": {
                                "name": "UK Polar Data Centre, British Antarctic Survey",
                                "href": "https://ror.org/01rhff309",
                                "title": "ror",
                            },
                            "phone": "+44 (0)1223 221400",
                            "address": {
                                "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                                "city": "Cambridge",
                                "administrative_area": "Cambridgeshire",
                                "postal_code": "CB3 0ET",
                                "country": "United Kingdom",
                            },
                            "email": "polardatacentre@bas.ac.uk",
                            "online_resource": {
                                "href": "https://www.bas.ac.uk/team/business-teams/information-services/uk-polar-data-centre/",
                                "title": "UK Polar Data Centre (UK PDC) - BAS public website",
                                "description": "General information about the NERC Polar Data Centre (UK PDC) from the "
                                "British Antarctic Survey (BAS) public website.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                },
                {
                    "terms": [
                        {
                            "term": "ANTARCTICA",
                            "href": "https://gcmd.earthdata.nasa.gov/kms/concept/70fb5a3b-35b1-4048-a8be-56a0d865281c",
                        }
                    ],
                    "type": "place",
                    "thesaurus": {
                        "title": {
                            "value": "Global Change Master Directory (GCMD) Location Keywords",
                            "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                        },
                        "dates": {"publication": {"date": date(2020, 1, 9)}},
                        "edition": "9.1",
                        "contact": {
                            "organisation": {
                                "name": "Global Change Data Center, Science and Exploration Directorate, Goddard Space "
                                "Flight Center (GSFC) National Aeronautics and Space Administration (NASA)",
                                "href": "https://ror.org/027ka1x80",
                                "title": "ror",
                            },
                            "address": {
                                "city": "Greenbelt",
                                "administrative_area": "MD",
                                "country": "United States of America",
                            },
                            "online_resource": {
                                "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                                "title": "Global Change Master Directory (GCMD) Keywords",
                                "description": "The information provided on this page seeks to define how the GCMD "
                                "Keywords are structured, used and accessed. It also provides "
                                "information on how users can participate in the further development of "
                                "the keywords.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                },
            ],
            "constraints": [
                {
                    "type": "usage",
                    "restriction_code": "license",
                    "statement": "This information is licensed under the Create Commons Attribution 4.0 International "
                    "Licence (CC BY 4.0). To view this licence, "
                    "visit https://creativecommons.org/licenses/by/4.0/",
                    "href": "https://creativecommons.org/licenses/by/4.0/",
                },
                {
                    "type": "usage",
                    "restriction_code": "otherRestrictions",
                    "statement": "Please cite this item as: "
                    "'Produced using data from the SCAR Antarctic Digital Database'.",
                },
            ],
            "spatial_representation_type": "vector",
            "language": "eng",
            "character_set": "utf-8",
            "topics": ["environment", "geoscientificInformation"],
            "extents": [
                {
                    "identifier": "bounding",
                    "geographic": {
                        "bounding_box": {
                            "west_longitude": -180.0,
                            "east_longitude": 180.0,
                            "south_latitude": -90.0,
                            "north_latitude": -60.0,
                        }
                    },
                    "temporal": {
                        "period": {"start": {"date": datetime(2020, 6, 25)}, "end": {"date": datetime(2020, 4, 23)}}
                    },
                }
            ],
            "lineage": {"statement": "Lineage"},
        },
    }

    if hierarchy_level != "collection":
        _distributor = {
            "organisation": {
                "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                "href": "https://ror.org/01rhff309",
                "title": "ror",
            },
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
                "href": "https://www.bas.ac.uk/team/magic",
                "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                "description": "General information about the BAS Mapping and Geographic Information Centre "
                "(MAGIC) from the British Antarctic Survey (BAS) public website.",
                "function": "information",
            },
            "role": ["distributor"],
        }

        config["hierarchy_level"] = "dataset"
        config["reference_system_info"] = {
            "authority": {
                "title": {"value": "European Petroleum Survey Group (EPSG) Geodetic Parameter Registry"},
                "dates": {"publication": {"date": date(2008, 11, 12)}},
                "contact": {
                    "organisation": {"name": "European Petroleum Survey Group"},
                    "email": "EPSGadministrator@iogp.org",
                    "online_resource": {
                        "href": "https://www.epsg-registry.org/",
                        "title": "EPSG Geodetic Parameter Dataset",
                        "description": "The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate "
                        "Reference Systems and Coordinate Transformations, accessible through this "
                        "online registry.",
                        "function": "information",
                    },
                    "role": ["publisher"],
                },
            },
            "code": {
                "value": "urn:ogc:def:crs:EPSG::3031",
                "href": "http://www.opengis.net/def/crs/EPSG/0/3031",
            },
            "version": "6.18.3",
        }
        config["distribution"] = [
            {
                "distributor": _distributor,
                "transfer_option": {
                    "online_resource": {
                        "href": "https://maps.bas.ac.uk/antarctic/wms?layer=add:test",
                        "title": "Web Map Service (WMS)",
                        "description": "Access information as a OGC Web Map Service layer.",
                        "function": "download",
                    }
                },
                "format": {"format": "Web Map Service"},
            },
            {
                "distributor": _distributor,
                "transfer_option": {
                    "size": {"unit": "kB", "magnitude": 8171.0},
                    "online_resource": {
                        "href": "https://data.bas.ac.uk/download/35b35d75-1060-4340-a365-62c2f718ca0d",
                        "title": "GeoPackage",
                        "description": "Download information as a OGC GeoPackage.",
                        "function": "download",
                    },
                },
                "format": {
                    "format": "GeoPackage",
                    "version": "1.2",
                    "href": "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
                },
            },
            {
                "distributor": _distributor,
                "transfer_option": {
                    "size": {"unit": "kB", "magnitude": 7535.0},
                    "online_resource": {
                        "href": "https://data.bas.ac.uk/download/c9e8ef23-0d49-4059-a013-51fdbc8ba1bb",
                        "title": "Shapefile",
                        "description": "Download information as an ESRI Shapefile.",
                        "function": "download",
                    },
                },
                "format": {
                    "format": "Shapefile",
                    "version": "1",
                    "href": "https://support.esri.com/en/white-paper/279",
                },
            },
        ]
    elif hierarchy_level == "collection":
        config["hierarchy_level"] = "collection"

        aggregations = []
        if item_identifiers is not None:
            for item_identifier in item_identifiers:
                aggregations.append(
                    {
                        "association_type": "isComposedOf",
                        "initiative_type": "collection",
                        "identifier": {
                            "identifier": item_identifier,
                            "href": f"https://data.bas.ac.uk/items/{item_identifier}",
                            "namespace": "data.bas.ac.uk",
                        },
                    }
                )
        config["identification"]["aggregations"] = aggregations

    return config


class TestRecordConfigurations(Enum):
    __test__ = False

    TEST_RECORD_1 = make_test_record_config(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f",
        title="Test Item Record 1 (Published)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_2 = make_test_record_config(
        identifier="39d47e50-f94f-43c5-9060-510d9374b81b",
        title="Test Item Record 2 (Unpublished)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_3 = make_test_record_config(
        identifier="180d07c4-8b97-48ed-87ac-359b6899fa8b",
        title="Test Item Record 3 (Imported, Unpublished)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_4 = make_test_record_config(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f",
        title="Test Item Record 4 (Imported, Updated, Unpublished)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_5 = make_test_record_config(
        identifier="2f8ad5b8-b861-4459-88d9-b9ff98a34a98",
        title="Test Item Record 5 (Imported, Published)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_6 = make_test_record_config(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f",
        title="Test Item Record 6 (Imported, Updated, Published, Republished)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_7 = make_test_record_config(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f",
        title="Test Item Record 7 (Imported, Duplicate of Test Record 1)",
        hierarchy_level="dataset",
        item_identifiers=None,
    )
    TEST_RECORD_8 = make_test_record_config(
        identifier="b759077f-bd3f-4a18-bbd7-e6b3f84bc551",
        title="Test Collection 1 (Published)",
        hierarchy_level="collection",
        item_identifiers=["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
    )
    TEST_RECORD_9 = make_test_record_config(
        identifier="6062c26f-0165-4109-a2d9-29cf884f079d",
        title="Test Collection 2 (Imported)",
        hierarchy_level="collection",
        item_identifiers=["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
    )
    TEST_RECORD_10 = make_test_record_config(
        identifier="b759077f-bd3f-4a18-bbd7-e6b3f84bc551",
        title="Test Collection 3 (Imported, Updated, Duplicate of Test Collection 1)",
        hierarchy_level="collection",
        item_identifiers=["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
    )
    TEST_RECORD_11 = make_test_record_config(
        identifier="0d1b9063-da63-403d-ba16-f72e5f6f5688",
        title="Test Collection 4 (Imported, contains unknown item identifier)",
        hierarchy_level="collection",
        item_identifiers=["unknown"],
    )


def make_csw_test_records() -> None:
    records_base_path = Path("resources/csw/records").resolve()
    for record_config in TestRecordConfigurations:
        print(f"Generating test record for '{record_config.name}'")
        configuration = MetadataRecordConfigV3(**record_config.value)
        record = MetadataRecord(configuration=configuration)
        record_path = records_base_path.joinpath(f"get_record_{record_config.value['file_identifier']}_full.xml")
        with open(Path(record_path), mode="w") as record_file:
            record_file.write(record.generate_xml_document().decode())
    print("Test records regenerated")
