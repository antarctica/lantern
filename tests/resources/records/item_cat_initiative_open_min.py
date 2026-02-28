from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for an initiative with minimum required fields for open-access.

record = make_record(
    open_access=True,
    file_identifier="c31720da-8c10-496a-893d-f003f09151e9",
    hierarchy_level=HierarchyLevelCode.INITIATIVE,
    title="Test Resource - Initiative with minimum required fields for open-access",
    abstract="Item to test minimal open-access Initiatives are supported and presented correctly.",
)
make_minimal_open_record(record)
