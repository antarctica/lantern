import json
from datetime import UTC, date, datetime

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    Date,
    Identifier,
    OnlineResource,
    Series,
)
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, TransferOption
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Constraint,
    Constraints,
    Extent,
    Extents,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.models.item.base.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from tests.resources.records.utils import make_record

# A trio of records to demonstrate a published map with two, mostly similar, sides.

ids = {
    "c": "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",
    "a": "bcacfe16-52da-4b26-94db-8a567e4292db",
    "b": "e30ac1c0-ed6a-49bd-8ca3-205610bf91bf",
}
graphics = {
    "c": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2/overview.jpg",
    "a": "https://images.unsplash.com/photo-1519821767025-2b43a48282ca?w=360&h=360&auto=format&fit=crop&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    "b": "https://images.unsplash.com/photo-1615012553971-f7251c225e01?w=360&h=360&auto=format&fit=crop&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
}
constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
            statement="Open Access (Anonymous)",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
            statement="All rights for this information are reserved. View the (Local) All Rights Reserved v1 licence, https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/, for more information.",
        ),
    ]
)
distribution = [
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
        transfer_option=TransferOption(
            online_resource=OnlineResource(
                href="https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/",
                function=OnlineResourceFunctionCode.ORDER,
                title="Map ordering information - BAS public website",
                description="Access information on how to order item.",
            ),
        ),
    )
]

combined = make_record(
    file_identifier=ids["c"],
    hierarchy_level=HierarchyLevelCode.PAPER_MAP_PRODUCT,
    title="Test Resource - Published map (X and Y)",
    abstract="A fake published printed map.",
    purpose="Item to test published maps are presented correctly.",
)
combined.identification.identifiers.append(Identifier(identifier="123-0-11111-001-1 (Folded)", namespace="isbn"))
combined.identification.identifiers.append(Identifier(identifier="123-0-22222-001-8 (Flat)", namespace="isbn"))
combined.identification.identifiers.append(
    Identifier(
        identifier="maps/test-pub-map",
        href=f"https://{CATALOGUE_NAMESPACE}/maps/test-pub-map",
        namespace=ALIAS_NAMESPACE,
    ),
)
combined.identification.edition = "1"
combined.identification.series = Series(name="Catalogue Test Resources", edition="1")
combined.identification.dates.creation = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
combined.identification.dates.published = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
combined.identification.spatial_resolution = 400_000
combined.identification.supplemental_information = json.dumps(
    {"physical_size_width_mm": 890, "physical_size_height_mm": 840, "sheet_number": "1"}
)
combined.identification.constraints = constraints
combined.distribution = distribution
combined.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            href=graphics["c"],
            mime_type="image/png",
        )
    ]
)
combined.identification.aggregations.extend(
    [
        Aggregation(
            identifier=Identifier(
                identifier=ids["a"],
                href=f"https://{CATALOGUE_NAMESPACE}/items/{ids['a']}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
            initiative_type=AggregationInitiativeCode.PAPER_MAP,
        ),
        Aggregation(
            identifier=Identifier(
                identifier=ids["b"],
                href=f"https://{CATALOGUE_NAMESPACE}/items/{ids['b']}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
            initiative_type=AggregationInitiativeCode.PAPER_MAP,
        ),
    ]
)
combined.identification.extents = Extents(
    [
        Extent(
            identifier="bounding",
            geographic=make_bbox_extent(-1, 1, -1, 1),
            temporal=make_temporal_extent(
                start=datetime(2020, 10, 1, tzinfo=UTC), end=datetime(2023, 10, 2, tzinfo=UTC)
            ),
        )
    ]
)

side_a = make_record(
    file_identifier=ids["a"],
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Published map (Side X)",
    abstract="Map X for testing published maps support.",
    purpose="Item to test published maps are presented correctly (side A).\n\nIt's Sunday, but screw it — juice box time. Say something that will terrify me. Yeah, I invited her. You said you wanted to spend time some with her.",
)
side_a.identification.edition = "1"
side_a.identification.series = Series(name="Catalogue Test Resources", edition="1")
side_a.identification.dates.creation = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_a.identification.dates.published = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_a.identification.spatial_resolution = 400_000
side_a.identification.supplemental_information = json.dumps(
    {"physical_size_width_mm": 890, "physical_size_height_mm": 840, "sheet_number": "1"}
)
side_a.identification.constraints = constraints
side_a.distribution = distribution
side_a.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            href=graphics["a"],
            mime_type="image/png",
        )
    ]
)
side_a.identification.aggregations.extend(
    [
        Aggregation(
            identifier=Identifier(
                identifier=ids["c"],
                href=f"https://{CATALOGUE_NAMESPACE}/items/{ids['c']}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.PAPER_MAP,
        ),
        Aggregation(
            identifier=Identifier(
                identifier=ids["b"],
                href=f"https://{CATALOGUE_NAMESPACE}/items/{ids['b']}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.PHYSICAL_REVERSE_OF,
            initiative_type=AggregationInitiativeCode.PAPER_MAP,
        ),
    ]
)
side_a.identification.extents = Extents(
    [
        Extent(
            identifier="bounding",
            geographic=make_bbox_extent(1, 1, 1, 1),
            temporal=make_temporal_extent(
                start=datetime(2020, 10, 1, tzinfo=UTC), end=datetime(2020, 10, 2, tzinfo=UTC)
            ),
        )
    ]
)

side_b = make_record(
    file_identifier=ids["b"],
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Published map (Side Y)",
    abstract="Map Y for testing published maps support.",
    purpose="Item to test published maps are presented correctly (side B).",
)
side_b.identification.edition = "1"
combined.identification.series = Series(name="Catalogue Test Resources", edition="1")
side_b.identification.dates.creation = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_b.identification.dates.published = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_b.identification.spatial_resolution = 400_000
side_b.identification.supplemental_information = json.dumps(
    {"physical_size_width_mm": 890, "physical_size_height_mm": 840, "sheet_number": "1"}
)
side_b.identification.constraints = constraints
side_b.distribution = distribution
side_b.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            href=graphics["b"],
            mime_type="image/png",
        )
    ]
)
side_b.identification.aggregations.extend(
    [
        Aggregation(
            identifier=Identifier(
                identifier=ids["c"],
                href=f"https://{CATALOGUE_NAMESPACE}/items/{ids['c']}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.PAPER_MAP,
        ),
        Aggregation(
            identifier=Identifier(
                identifier=ids["a"],
                href=f"https://{CATALOGUE_NAMESPACE}/items/{ids['a']}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.PHYSICAL_REVERSE_OF,
            initiative_type=AggregationInitiativeCode.PAPER_MAP,
        ),
    ]
)
side_b.identification.extents = Extents(
    [
        Extent(
            identifier="bounding",
            geographic=make_bbox_extent(-1, -1, -1, -1),
            temporal=make_temporal_extent(
                start=datetime(2023, 10, 1, tzinfo=UTC), end=datetime(2023, 10, 2, tzinfo=UTC)
            ),
        )
    ]
)
