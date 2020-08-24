from datetime import date, datetime


def make_test_record(identifier: str, title: str) -> dict:
    return {
        "file_identifier": identifier,
        "language": "eng",
        "character_set": "utf-8",
        "hierarchy_level": "dataset",
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
                    "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                    "function": "information",
                },
                "role": ["pointOfContact"],
            }
        ],
        "date_stamp": date(2020, 5, 25).isoformat(),
        "metadata_standard": {
            "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
            "version": "ISO 19115-2:2009(E)",
        },
        "reference_system_info": {
            "authority": {
                "title": {"value": "European Petroleum Survey Group (EPSG) Geodetic Parameter Registry"},
                "dates": [{"date": date(2008, 11, 12).isoformat(), "date_type": "publication"}],
                "contact": {
                    "organisation": {"name": "European Petroleum Survey Group"},
                    "email": "EPSGadministrator@iogp.org",
                    "online_resource": {
                        "href": "https://www.epsg-registry.org/",
                        "title": "EPSG Geodetic Parameter Dataset",
                        "description": "The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate Reference Systems and Coordinate Transformations, accessible through this online registry.",
                        "function": "information",
                    },
                    "role": ["publisher"],
                },
            },
            "code": {"value": "urn:ogc:def:crs:EPSG::3031", "href": "http://www.opengis.net/def/crs/EPSG/0/3031",},
            "version": "6.18.3",
        },
        "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
        "resource": {
            "title": {"value": title},
            "dates": [
                {"date_precision": "year", "date": str(date(2020, 1, 1).year), "date_type": "creation"},
                {"date": date(2020, 2, 26).isoformat(), "date_type": "revision"},
                {"date": datetime(2020, 1, 15, 10, 44, 14).isoformat(), "date_type": "publication"},
                {"date": datetime(2020, 3, 9, 15, 7, 56).isoformat(), "date_type": "released"},
            ],
            "edition": f"1.2",
            "abstract": title,
            "contacts": [
                {
                    "individual": {
                        "name": f"Watson, Constance",
                        "href": f"https://orcid.org/0001-0002-0003-0004",
                        "title": "orcid",
                    },
                    "organisation": {
                        "name": "British Antarctic Survey",
                        "href": "https://ror.org/01rhff309",
                        "title": "ror",
                    },
                    "email": "conwat@bas.ac.uk",
                    "online_resource": {
                        "href": f"https://orcid.org/0001-0002-0003-0004",
                        "title": "ORCID record",
                        "description": "ORCID is an open, non-profit, community-driven effort to create and maintain a registry of unique researcher identifiers and a transparent method of linking research activities and outputs to these identifiers.",
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
                        "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                        "function": "information",
                    },
                    "role": ["publisher", "pointOfContact", "distributor"],
                },
            ],
            "maintenance": {"maintenance_frequency": "biannually", "progress": "completed"},
            "keywords": [
                {
                    "terms": [{"term": "STUFF", "href": f"https://www.eionet.europa.eu/gemet/en/inspire-theme/st",}],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "General Multilingual Environmental Thesaurus - INSPIRE themes",
                            "href": "http://www.eionet.europa.eu/gemet/inspire_themes",
                        },
                        "dates": [{"date": date(2008, 8, 16).isoformat(), "date_type": "publication"}],
                        "edition": "4.1.2",
                        "contact": {
                            "organisation": {
                                "name": "European Environment Information and Observation Network (EIONET), European Environment Agency (EEA)",
                                "href": "https://ror.org/02k4b9v70",
                                "title": "ror",
                            },
                            "email": "helpdesk@eionet.europa.eu",
                            "online_resource": {
                                "href": "https://www.eionet.europa.eu/gemet/en/themes/",
                                "title": "GEMET INSPIRE Spatial Data Themes  General Multilingual Environmental Thesaurus",
                                "description": "GEMET, the GEneral Multilingual Environmental Thesaurus, has been developed as a multilingual thesauri for indexing, retrieval and control of terms in order to save time, energy and funds.",
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
                            "href": "https://gcmdservices.gsfc.nasa.gov/kms/concept/3e822484-c94a-457b-a32f-376fcbd6fd35",
                        },
                        {
                            "term": f"STUFF",
                            "href": f"https://gcmdservices.gsfc.nasa.gov/kms/concept/c4992969-05db-4bb6-9dac-d35535503650",
                        },
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "Global Change Master Directory (GCMD) Science Keywords",
                            "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                        },
                        "dates": [{"date": date(2020, 1, 9).isoformat(), "date_type": "publication"}],
                        "edition": "9.1",
                        "contact": {
                            "organisation": {
                                "name": "Global Change Data Center, Science and Exploration Directorate, Goddard Space Flight Center (GSFC) National Aeronautics and Space Administration (NASA)",
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
                                "description": "The information provided on this page seeks to define how the GCMD Keywords are structured, used and accessed. It also provides information on how users can participate in the further development of the keywords.",
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
                            "href": "http://vocab.nerc.ac.uk/collection/T01/1/9cd3118f-55e2-4c07-b9f4-e260e40e8eb2/1/",
                        }
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "British Antarctic Survey research topics",
                            "href": "http://vocab.nerc.ac.uk/collection/T01/1/",
                        },
                        "dates": [{"date": date(2020, 5, 6).isoformat(), "date_type": "publication"}],
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
                                "description": "General information about the NERC Polar Data Centre (UK PDC) from the British Antarctic Survey (BAS) public website.",
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
                            "href": "http://vocab.nerc.ac.uk/collection/T02/1/8e91de62-b6e3-402e-b11f-73d2c1f37cff/",
                        }
                    ],
                    "type": "theme",
                    "thesaurus": {
                        "title": {
                            "value": "British Antarctic Survey data catalogue collections",
                            "href": "http://vocab.nerc.ac.uk/collection/T02/1/",
                        },
                        "dates": [{"date": date(2020, 5, 5).isoformat(), "date_type": "publication"}],
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
                                "description": "General information about the NERC Polar Data Centre (UK PDC) from the British Antarctic Survey (BAS) public website.",
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
                            "href": "https://gcmdservices.gsfc.nasa.gov/kms/concept/70fb5a3b-35b1-4048-a8be-56a0d865281c",
                        }
                    ],
                    "type": "place",
                    "thesaurus": {
                        "title": {
                            "value": "Global Change Master Directory (GCMD) Location Keywords",
                            "href": "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords",
                        },
                        "dates": [{"date": date(2020, 1, 9).isoformat(), "date_type": "publication"}],
                        "edition": "9.1",
                        "contact": {
                            "organisation": {
                                "name": "Global Change Data Center, Science and Exploration Directorate, Goddard Space Flight Center (GSFC) National Aeronautics and Space Administration (NASA)",
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
                                "description": "The information provided on this page seeks to define how the GCMD Keywords are structured, used and accessed. It also provides information on how users can participate in the further development of the keywords.",
                                "function": "information",
                            },
                            "role": ["publisher"],
                        },
                    },
                },
            ],
            "constraints": {
                "access": [
                    {"restriction_code": "otherRestrictions", "inspire_limitations_on_public_access": "noLimitations",}
                ],
                "usage": [
                    {
                        "copyright_licence": {
                            "statement": "This information is licensed under the Create Commons Attribution 4.0 International Licence (CC BY 4.0). To view this licence, visit https://creativecommons.org/licenses/by/4.0/",
                            "href": "https://creativecommons.org/licenses/by/4.0/",
                        }
                    },
                    {
                        "required_citation": {
                            "statement": "Please cite this item as: 'Produced using data from the SCAR Antarctic Digital Database'."
                        }
                    },
                ],
            },
            "spatial_representation_type": "vector",
            "language": "eng",
            "character_set": "utf-8",
            "topics": ["environment", "geoscientificInformation"],
            "extent": {
                "geographic": {
                    "bounding_box": {
                        "west_longitude": -180.0,
                        "east_longitude": 180.0,
                        "south_latitude": -90.0,
                        "north_latitude": -60.0,
                    }
                },
                "temporal": {
                    "period": {"start": datetime(2020, 6, 25).isoformat(), "end": datetime(2020, 4, 23).isoformat()}
                },
            },
            "formats": [
                {"format": "Web Map Service"},
                {
                    "format": "GeoPackage",
                    "href": "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
                    "version": "1.2",
                },
                {"format": "Shapefile", "href": "https://support.esri.com/en/white-paper/279", "version": "1"},
            ],
            "transfer_options": [
                {
                    "online_resource": {
                        "href": f"https://maps.bas.ac.uk/antarctic/wms?layer=add:test",
                        "title": "Web Map Service (WMS)",
                        "description": "Access information as a OGC Web Map Service layer.",
                        "function": "download",
                    }
                },
                {
                    "size": {"unit": "kB", "magnitude": 8171.0},
                    "online_resource": {
                        "href": f"https://data.bas.ac.uk/download/35b35d75-1060-4340-a365-62c2f718ca0d",
                        "title": "GeoPackage",
                        "description": "Download information as a OGC GeoPackage.",
                        "function": "download",
                    },
                },
                {
                    "size": {"unit": "kB", "magnitude": 7535.0},
                    "online_resource": {
                        "href": f"https://data.bas.ac.uk/download/c9e8ef23-0d49-4059-a013-51fdbc8ba1bb",
                        "title": "Shapefile",
                        "description": "Download information as an ESRI Shapefile.",
                        "function": "download",
                    },
                },
            ],
            "lineage": "Lineage",
        },
    }
