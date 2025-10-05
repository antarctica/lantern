import json
from datetime import date

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
    OnlineResource,
    Series,
)
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Format,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.elements.projection import (
    Code,
    ReferenceSystemInfo,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE, GITLAB_NAMESPACE
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with all supported fields for products.

abstract = """
I spent so much time making sweet jam in the kitchen that it's hard to hear anything over the clatter of the
tin bath. I shall hide behind the couch. _(Guy's a pro.)_

Interfere? Michael: I'm sorry, have we met? She calls it a mayonegg. The only thing more terrifying than the
escaped lunatic's hook was his twisted call…

> Heyyyyy campers!

I didn't get into this business to please sophomore Tracy Schwartzman, so… onward and upward. On… Why, Tracy?! Why?!!

* Say something that will terrify me.
* Lindsay: Kiss me.
* Tobias: No, that didn't do it.

No, I was ashamed to be **SEEN** with you. I like being **WITH** you.

1. Chickens don't clap!
2. Am I in two thirds of a hospital room?

You're a good guy, mon frere. That means brother in French. I don't know how I know that. I took four years of Spanish.

See [here](#) for more good stuff.

The guy runs a prison, he can have any piece of cake he wants. In fact, it was a box of Oscar's legally obtained
medical marijuana. Primo bud. Real sticky weed. So, what do you say? We got a basket full of father-son fun here.
What's Kama Sutra oil? Maybe it's not for us. He… she… what's the difference? Oh hear, hear. In the dark, it all looks
the same. Well excuse me, Judge Reinhold!
"""

record = make_record(
    file_identifier="30825673-6276-4e5a-8a97-f97f2094cd25",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product with all supported fields",
    abstract=abstract,
    purpose="Item to test all supported Product properties are recognised and presented correctly.",
)
record.reference_system_info = ReferenceSystemInfo(
    code=Code(
        value="urn:ogc:def:crs:EPSG::4326",
        href="http://www.opengis.net/def/crs/EPSG/0/4326",
    ),
    version="6.18.3",
    authority=Citation(
        title="European Petroleum Survey Group (EPSG) Geodetic Parameter Registry",
        dates=Dates(publication=Date(date=date(2008, 11, 12))),
        contacts=Contacts(
            [
                Contact(
                    organisation=ContactIdentity(name="European Petroleum Survey Group"),
                    email="EPSGadministrator@iogp.org",
                    online_resource=OnlineResource(
                        href="https://www.epsg-registry.org/",
                        title="EPSG Geodetic Parameter Dataset",
                        description="The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate Reference Systems and Coordinate Transformations, accessible through this online registry.",
                        function=OnlineResourceFunctionCode.INFORMATION,
                    ),
                    role={ContactRoleCode.PUBLISHER},
                )
            ]
        ),
    ),
)
record.identification.edition = "1.2.3"
record.identification.dates = Dates(
    creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR),
    publication=Date(date=date(2023, 10, 1)),
    revision=Date(date=date(2023, 10, 1)),
    adopted=Date(date=date(2023, 10, 1)),
    deprecated=Date(date=date(2023, 10, 1)),
    distribution=Date(date=date(2023, 10, 1)),
    expiry=Date(date=date(2023, 10, 1)),
    in_force=Date(date=date(2023, 10, 1)),
    last_revision=Date(date=date(2023, 10, 1)),
    last_update=Date(date=date(2023, 10, 1)),
    next_update=Date(date=date(2023, 10, 1)),
    released=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.MONTH),
    superseded=Date(date=date(2023, 10, 1)),
    unavailable=Date(date=date(2023, 10, 1)),
    validity_begins=Date(date=date(2023, 10, 1)),
    validity_expires=Date(date=date(2023, 10, 1)),
)
record.identification.identifiers = Identifiers(
    [
        Identifier(
            identifier="30825673-6276-4e5a-8a97-f97f2094cd25",
            href=f"https://{CATALOGUE_NAMESPACE}/items/30825673-6276-4e5a-8a97-f97f2094cd25",
            namespace=CATALOGUE_NAMESPACE,
        ),
        Identifier(
            identifier=f"https://{GITLAB_NAMESPACE}/MAGIC/test/-/issues/123",
            href=f"https://{GITLAB_NAMESPACE}/MAGIC/test/-/issues/123",
            namespace=GITLAB_NAMESPACE,
        ),
        Identifier(
            identifier="maps/test123",
            href=f"https://{CATALOGUE_NAMESPACE}/maps/test123",
            namespace=ALIAS_NAMESPACE,
        ),
        Identifier(
            identifier="maps/test123alt",
            href=f"https://{CATALOGUE_NAMESPACE}/maps/test123alt",
            namespace=ALIAS_NAMESPACE,
        ),
        Identifier(
            identifier="10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
            href="https://doi.org/10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
            namespace="doi",
        ),
        Identifier(
            identifier="10.123/test123",
            href="https://doi.org/10.123/test123",
            namespace="doi",
        ),
        Identifier(
            identifier="123-1",
            namespace="isbn",
        ),
        Identifier(
            identifier="234-1",
            namespace="isbn",
        ),
    ]
)
record.identification.series = Series(name="Test Series", page="3", edition="1")
record.identification.spatial_resolution = 1_234_567_890
record.identification.contacts = Contacts(
    [
        Contact(
            individual=ContactIdentity(
                name="Connie Watson",
                href="https://sandbox.orcid.org/0000-0001-8373-6934",
                title="orcid",
            ),
            organisation=ContactIdentity(
                name="Mapping and Geographic Information Centre, British Antarctic Survey",
                href="https://ror.org/01rhff309",
                title="ror",
            ),
            phone="+44 (0)1223 221400",
            email="conwat@bas.ac.uk",
            address=Address(
                delivery_point="British Antarctic Survey, High Cross, Madingley Road",
                city="Cambridge",
                administrative_area="Cambridgeshire",
                postal_code="CB3 0ET",
                country="United Kingdom",
            ),
            online_resource=OnlineResource(
                href="https://www.bas.ac.uk/people/conwat",
                title="Connie Watson - BAS public website",
                description="Personal profile for Connie Watson from the British Antarctic Survey (BAS) public website.",
                function=OnlineResourceFunctionCode.INFORMATION,
            ),
            role={ContactRoleCode.AUTHOR},
        ),
        Contact(
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
            role={ContactRoleCode.AUTHOR, ContactRoleCode.POINT_OF_CONTACT},
        ),
        Contact(
            organisation=ContactIdentity(
                name="UK Research and Innovation",
                href="https://ror.org/001aqnf71",
                title="ror",
            ),
            address=Address(
                delivery_point="UK Research and Innovation, Polaris House",
                city="Swindon",
                administrative_area="Hampshire",
                postal_code="SN2 1FL",
                country="United Kingdom",
            ),
            online_resource=OnlineResource(
                href="https://www.ukri.org",
                title="UK Research and Innovation public website",
                description="Public information about UK Research and Innovation (UKRI).",
                function=OnlineResourceFunctionCode.INFORMATION,
            ),
            role={ContactRoleCode.RIGHTS_HOLDER},
        ),
        Contact(
            individual=ContactIdentity(name="Count Dracula"),
            role={ContactRoleCode.RIGHTS_HOLDER},
        ),
        Contact(
            organisation=ContactIdentity(name="MegaDodo Publications"),
            role={ContactRoleCode.RIGHTS_HOLDER},
        ),
        Contact(
            individual=ContactIdentity(name="William Smyth III"),
            online_resource=OnlineResource(
                href="https://www.smyth-holdings.com", function=OnlineResourceFunctionCode.INFORMATION
            ),
            role={ContactRoleCode.RIGHTS_HOLDER},
        ),
    ]
)
record.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            description="Overview",
            href="https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/e46046cc-7375-444a-afaa-3356c278d446/1005-thumbnail.png",
            mime_type="image/png",
        )
    ]
)
record.identification.other_citation_details = "Produced by the Mapping and Geographic Information Centre, British Antarctic Survey, 2025, version 1, https://data.bas.ac.uk/maps/1005."
record.identification.supplemental_information = json.dumps(
    {"physical_size_width_mm": "210", "physical_size_height_mm": "297", "sheet_number": "4"}
)

# add a related peer
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="30825673-6276-4e5a-8a97-f97f2094cd25",
            href=f"https://{CATALOGUE_NAMESPACE}/items/30825673-6276-4e5a-8a97-f97f2094cd25",
            namespace=CATALOGUE_NAMESPACE,
        ),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
    )
)
# add a superseded peer
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="7e3611a6-8dbf-4813-aaf9-dadf9decff5b",
            href=f"https://{CATALOGUE_NAMESPACE}/items/7e3611a6-8dbf-4813-aaf9-dadf9decff5b",
            namespace=CATALOGUE_NAMESPACE,
        ),
        association_type=AggregationAssociationCode.REVISION_OF,
    )
)
# Haven't added a parent collection as one already set
# Can't add a collection cross-reference as not a collection (is added in max collection)
# Can't add opposite side relation as not a physical map side
# Can't add a parent physical map as not a physical map side

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
                title="PNG (alt title)",
                description="Optional value.",
            ),
        ),
    ),
]
