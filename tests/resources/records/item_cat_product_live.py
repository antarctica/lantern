from datetime import UTC, datetime

from lantern.lib.metadata_library.models.record.elements.common import Date, Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
)
from lantern.models.record.const import CATALOGUE_NAMESPACE
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for an open product considered to be 'live' in terms of update frequency.

now = datetime.now(tz=UTC).replace(microsecond=0)

record = make_record(
    open_access=True,
    file_identifier="9edd97d9-3df6-4aff-b356-87d23c9f655f",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item with 'live' update",
    abstract="Item to test the 'live' status, based on update frequently, is supported and presented correctly.",
    purpose="Item to test the 'live' status, based on update frequently.",
)
make_minimal_open_record(record)
# to make record live
record.identification.maintenance.maintenance_frequency = MaintenanceFrequencyCode.CONTINUAL
# to fill out item summary and check elative date handling
record.identification.dates.publication = Date(date=now.replace(hour=1, minute=0, second=0))
record.identification.dates.revision = Date(date=now)
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            href=f"https://{CATALOGUE_NAMESPACE}/items/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            namespace=CATALOGUE_NAMESPACE,
        ),
        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
        initiative_type=AggregationInitiativeCode.COLLECTION,
    )
)
