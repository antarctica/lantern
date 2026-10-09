from datetime import UTC, date, datetime
from typing import Literal

from lantern.lib.metadata_library.models.record.elements.common import (
    Contact,
    ContactIdentity,
    Date,
    Dates,
    Identifier,
    Maintenance,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, DomainConsistencies, Lineage
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    Extent,
    Extents,
    Identification,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.base import RecordMagic, RecordMagicOpen
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from tests.resources.admin_keys import test_keys


def make_record(
    open_access: bool,
    file_identifier: str,
    hierarchy_level: HierarchyLevelCode,
    title: str,
    abstract: str,
    purpose: str | None = None,
) -> RecordRevision:
    """Make a record for testing based on RecordMagicDiscoveryV1."""
    admin_keys = test_keys()
    record_cls = RecordMagicOpen if open_access else RecordMagic

    record = record_cls(
        file_identifier=file_identifier,
        hierarchy_level=hierarchy_level,
        meta_date_stamp=date(2023, 10, 1),  # will be popped for use in Metadata
        identification=Identification(
            title=title,
            abstract=abstract,
            purpose=abstract if purpose is None else purpose,
            edition="1",
            dates=Dates(creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR)),
        ),
        data_quality=DataQuality(lineage=Lineage(statement="x")),
        admin_keys=admin_keys,
    )

    record.identification.aggregations = Aggregations(
        [
            Aggregation(
                identifier=Identifier(
                    identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    href=f"https://{CATALOGUE_NAMESPACE}/items/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    namespace=CATALOGUE_NAMESPACE,
                ),
                association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                initiative_type=AggregationInitiativeCode.COLLECTION,
            )
        ]
    )

    record.identification.extents = Extents(
        [
            Extent(
                identifier="bounding",
                geographic=make_bbox_extent(1.0, 2.0, 3.0, 4.0),
                temporal=make_temporal_extent(
                    start=datetime(2023, 10, 1, tzinfo=UTC), end=datetime(2023, 10, 2, tzinfo=UTC)
                ),
            )
        ]
    )

    record.identification.maintenance = Maintenance(
        progress=ProgressCode.COMPLETED,
        maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED,
    )

    # Convert to RecordRevision
    config = {"file_revision": "83fake487e5671f4a1dd7074b92fb94aa68d26bd", **record.dumps(strip_admin=False)}
    return RecordRevision.loads(config)


def make_minimal_open_record(record: RecordRevision) -> None:
    """Remove all non-required fields set by `make_record()` except those needed for open-access."""
    record.identification.edition = None
    record.identification.purpose = None
    record.identification.contacts[0] = Contact(
        organisation=ContactIdentity(name="MAGIC"), email="magic@bas.ac.uk", role={ContactRoleCode.POINT_OF_CONTACT}
    )
    record.identification.other_citation_details = None
    record.identification.aggregations = Aggregations([])
    record.identification.extents = Extents([])
    record.identification.maintenance.progress = None
    record.identification.maintenance.maintenance_frequency = None
    record.data_quality.lineage = None
    record.data_quality.domain_consistency = DomainConsistencies([])


def relate_records(
    file_identifier: str,
    groups: list[Literal["min_max", "lifecycle", "restrictions", "product_types", "others", "data", "licences"]],
) -> Aggregations:
    """
    Make aggregations to relate records together.

    Automatically excludes self relations.

    Groups are used to focus on closely related records, unless 'all' is used.
    """
    restrictions = [
        "b0e92ec2-b018-4f9f-a1e1-bc0fe195619f",  # product (min, Open Access)
        "3b08401d-3dbb-4751-a930-21ca0eced88b",  # product (restricted, MAGIC Team)
        "57327327-4623-4247-af86-77fb43b7f45b",  # product (restricted, BAS Staff)
        "1481464a-521c-49d8-ac0b-c7ade9303bcd",  # product (restricted, Custom Groups)
    ]
    product_types = [
        "a59b5c5b-b099-4f01-b670-3800cb65e666",  # webMapProduct
        "8422d4e7-654f-4fbb-a5e0-4051ee21418e",  # mapProduct
        "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",  # paperMapProduct
        "09dbc743-cc96-46ff-8449-1709930b73ad",  # paperMapProduct (diff)
    ]
    lifecycle = [
        "9edd97d9-3df6-4aff-b356-87d23c9f655f",  # continuous (live)
        "0116d9fe-19c0-4d7f-a5a8-67a8ffed7da2",  # deprecated
        "7e3611a6-8dbf-4813-aaf9-dadf9decff5b",  # superseded
    ]
    min_max_types = [
        "30825673-6276-4e5a-8a97-f97f2094cd25",  # product (all)
        "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",  # product (min)
    ]
    others = [
        "cf80b941-3de6-4a04-8f5a-a2349c1e3ae0",  # checks report
        "e0df252c-fb8b-49ff-9711-f91831b66ea2",  # formatting
    ]
    data = [
        "f90013f6-2893-4c72-953a-a1a6bc1919d7",  # data formats
        "e0743576-e05d-49cd-b7bf-01a0b3ad0430",  # datasets as layers
    ]
    licences = [
        "589408f0-f46b-4609-b537-2f90a2f61243",  # OGL
        "4ba929ac-ca32-4932-a15f-38c1640c0b0f",  # CC
        "5ab58461-5ba7-404d-a904-2b4efcb7556e",  # Ops Mapping (deprecated)
        "60c05109-d15e-4b43-9e36-d4fd9d7c606b",  # MAGIC Products
        "c993ea2b-d44e-4ca0-9007-9a972f7dd117",  # all rights reserved
        "43287219-40aa-47fd-809e-21b50773a052",  # Copernicus Sentinel v1
    ]

    targets = []
    if "restrictions" in groups:
        targets.extend(restrictions)
    if "product_types" in groups:
        targets.extend(product_types)
    if "lifecycle" in groups:
        targets.extend(lifecycle)
    if "min_max" in groups:
        targets.extend(min_max_types)
    if "others" in groups:
        targets.extend(others)
    if "data" in groups:
        targets.extend(data)
    if "licences" in groups:
        targets.extend(licences)

    return Aggregations(
        [
            Aggregation(
                identifier=Identifier(identifier=pid, namespace=CATALOGUE_NAMESPACE),
                association_type=AggregationAssociationCode.CROSS_REFERENCE,
            )
            for pid in targets
            if pid != file_identifier
        ]
    )
