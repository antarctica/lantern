from datetime import UTC, date, datetime

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata

from lantern.lib.metadata_library.models.record.elements.common import (
    Constraints,
    Date,
    Dates,
    Identifier,
    Maintenance,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import Lineage
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
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS as OPEN_ACCESS_PERMISSION
from lantern.lib.metadata_library.models.record.presets.base import RecordMagic
from lantern.lib.metadata_library.models.record.presets.constraints import CC_BY_ND_V4, OGL_V3, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from tests.resources.admin_keys import test_keys


def make_record(
    file_identifier: str, hierarchy_level: HierarchyLevelCode, title: str, abstract: str, purpose: str | None = None
) -> RecordRevision:
    """Make a record for testing based on RecordMagicDiscoveryV1."""
    admin_keys = test_keys()
    admin_meta = AdministrationMetadata(
        id=file_identifier,
        gitlab_issues=[],
        metadata_permissions=[OPEN_ACCESS_PERMISSION],
        resource_permissions=[OPEN_ACCESS_PERMISSION],
    )

    record = RecordMagic(
        file_identifier=file_identifier,
        hierarchy_level=hierarchy_level,
        identification=Identification(
            title=title,
            abstract=abstract,
            dates=Dates(creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR)),
        ),
        admin_keys=admin_keys,
        admin_meta=admin_meta,
    )

    record.metadata.constraints = Constraints([OPEN_ACCESS, CC_BY_ND_V4])
    record.metadata.date_stamp = date(2023, 10, 1)

    record.identification.edition = "1"

    record.identification.purpose = abstract if purpose is None else purpose

    # Include additional role for existing magic contact
    magic_contact = make_magic_role({ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER})
    magic_index = next(
        (
            i
            for i, c in enumerate(record.identification.contacts)
            if c.organisation.name == magic_contact.organisation.name
        ),
        None,
    )
    record.identification.contacts[magic_index] = magic_contact

    record.identification.constraints = Constraints([OPEN_ACCESS, OGL_V3])

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

    record.data_quality.lineage = Lineage(statement="x")

    # Convert to RecordRevision
    config = {"file_revision": "83fake487e5671f4a1dd7074b92fb94aa68d26bd", **record.dumps(strip_admin=False)}
    return RecordRevision.loads(config)


def relate_products(file_identifier: str) -> Aggregations:
    """
    Make aggregations to relate records together.

    Superseded product ('7e3611a6-8dbf-4813-aaf9-dadf9decff5b') excluded as it's covered by another aggregation type.
    """
    product_ids = [
        "a59b5c5b-b099-4f01-b670-3800cb65e666",  # webMapProduct
        "8422d4e7-654f-4fbb-a5e0-4051ee21418e",  # mapProduct
        "30825673-6276-4e5a-8a97-f97f2094cd25",  # product (all)
        "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",  # product (min)
        "57327327-4623-4247-af86-77fb43b7f45b",  # product (restricted
        "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",  # paperMapProduct
        "09dbc743-cc96-46ff-8449-1709930b73ad",  # paperMapProduct (diff)
    ]

    return Aggregations(
        [
            Aggregation(
                identifier=Identifier(identifier=pid, namespace=CATALOGUE_NAMESPACE),
                association_type=AggregationAssociationCode.CROSS_REFERENCE,
            )
            for pid in product_ids
            if pid != file_identifier
        ]
    )
