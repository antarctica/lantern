from datetime import UTC, date, datetime

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Constraint,
    Constraints,
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
from lantern.lib.metadata_library.models.record.presets.constraints import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.lib.metadata_library.models.record.utils.kv import set_kv
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from tests.resources.records.utils import make_record, relate_products

# A trio of records to demonstrate a published map with two dissimilar sides
#
# Dissimilar properties:
# - file_identifier*
# - title*
# - abstract*
# - purpose*
# - edition*
# - series (inc. sheet number via supplemental_information)
# - spatial_resolution
# - graphic_overviews*
# - extents*
# - aggregations*
#
# (*) items are expected to differ between sides of a published map.

ids = {
    "c": "09dbc743-cc96-46ff-8449-1709930b73ad",
    "a": "01cfa0fc-4c95-464d-88b7-01c54f0d8b8e",
    "b": "002f07e6-1d87-4a10-a2cb-f1c97024f071",
}
graphics = {
    "c": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/09dbc743-cc96-46ff-8449-1709930b73ad/overview.jpg",
    "a": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/09dbc743-cc96-46ff-8449-1709930b73ad/side-a.jpg",
    "b": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/09dbc743-cc96-46ff-8449-1709930b73ad/side-b.jpg",
}

constraints = Constraints(
    [
        OPEN_ACCESS,
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
    title="Test Resource - Published map (Z and Soaring Crescendo)",
    abstract="A fake published printed map with dissimilar sides.",
    purpose="Item to test dissimilar published maps are presented correctly.",
)
combined.identification.identifiers.append(Identifier(identifier="123-0-11111-001-1 (Folded)", namespace="isbn"))
combined.identification.identifiers.append(Identifier(identifier="123-0-22222-001-8 (Flat)", namespace="isbn"))
combined.identification.identifiers.append(
    Identifier(
        identifier="maps/test-pub-map2",
        href=f"https://{CATALOGUE_NAMESPACE}/maps/test-pub-map2",
        namespace=ALIAS_NAMESPACE,
    ),
)
combined.identification.edition = "1"
combined.identification.series = Series(name="Catalogue Test Resources", page="3", edition="1")
combined.identification.dates.creation = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
combined.identification.dates.published = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
set_kv({"physical_size_width_mm": 890, "physical_size_height_mm": 840}, combined)
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
combined.identification.aggregations.extend(relate_products(combined.file_identifier))
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
    title="Test Resource - Published map (Side Z)",
    abstract="Map Z for testing dissimilar published maps support.",
    purpose="Item to test dissimilar published maps are presented correctly (side Z [A]).",
)
side_a.identification.edition = "20"
side_a.identification.series = Series(name="Catalogue Test Resources", page="3(⬆️)", edition="20")
side_a.identification.dates.creation = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_a.identification.dates.published = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_a.identification.spatial_resolution = 200_000
set_kv({"physical_size_width_mm": 890, "physical_size_height_mm": 840}, side_a)
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
    title="Test Resource - Published map (Side Soaring Crescendo)",
    abstract="Map Soaring Crescendo for testing dissimilar published maps support.",
    purpose="Item to test dissimilar published maps are presented correctly (side Soaring Crescendo [B]).",
)
side_b.identification.edition = "400"
side_b.identification.series = Series(name="Alt Catalogue Test Resources", page='"3(⬇️)"', edition="400")
side_b.identification.dates.creation = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_b.identification.dates.published = Date(date=date(year=2023, month=10, day=30), precision=DatePrecisionCode.YEAR)
side_b.identification.spatial_resolution = 800_000
set_kv({"physical_size_width_mm": 890, "physical_size_height_mm": 840}, side_b)
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
