from datetime import UTC, date, datetime

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    OnlineResource,
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
    OnlineResourceFunctionCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.base import RecordMagicDiscoveryV1
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent, make_temporal_extent
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision


def make_record(
    file_identifier: str, hierarchy_level: HierarchyLevelCode, title: str, abstract: str, purpose: str | None = None
) -> RecordRevision:
    """Make a record for testing based on RecordMagicDiscoveryV1."""
    record = RecordMagicDiscoveryV1(
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

    record.identification.contacts = Contacts(
        [
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
                role=[ContactRoleCode.PUBLISHER, ContactRoleCode.POINT_OF_CONTACT],
            )
        ]
    )

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
        progress=ProgressCode.ON_GOING,
        maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED,
    )

    record.data_quality.lineage = Lineage(statement="x")

    # Convert to RecordRevision
    config = {"file_revision": "83fake487e5671f4a1dd7074b92fb94aa68d26bd", **record.dumps()}
    return RecordRevision.loads(config)
