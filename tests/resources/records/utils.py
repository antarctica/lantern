from datetime import UTC, date, datetime

from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.elements.common import (
    Date,
    Dates,
    Identifier,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import Lineage
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    Constraint,
    Constraints,
    Extent,
    Extents,
    Identification,
    Maintenance,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    DatePrecisionCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.base import RecordMagicDiscoveryV2
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from tests.resources.records.admin_keys.testing_keys import load_keys as load_test_keys


def make_record(
    file_identifier: str, hierarchy_level: HierarchyLevelCode, title: str, abstract: str, purpose: str | None = None
) -> RecordRevision:
    """Make a record for testing based on RecordMagicDiscoveryV1."""
    record = RecordMagicDiscoveryV2(
        file_identifier=file_identifier,
        hierarchy_level=hierarchy_level,
        identification=Identification(
            title=title,
            abstract=abstract,
            dates=Dates(creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR)),
        ),
    )

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

    record.identification.constraints = Constraints(
        [
            Constraint(
                type=ConstraintTypeCode.ACCESS,
                restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                statement="Open Access (Anonymous)",
            ),
            Constraint(
                type=ConstraintTypeCode.USAGE,
                restriction_code=ConstraintRestrictionCode.LICENSE,
                href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                statement="This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
            ),
        ]
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

    record.data_quality.lineage = Lineage(statement="x")

    administration = Administration(
        id=record.file_identifier,
        gitlab_issues=[],
        access_permissions=[OPEN_ACCESS],
    )
    keys = load_test_keys()
    set_admin(keys=keys, record=record, admin_meta=administration)

    # Convert to RecordRevision
    config = {"file_revision": "83fake487e5671f4a1dd7074b92fb94aa68d26bd", **record.dumps(strip_admin=False)}
    return RecordRevision.loads(config)
