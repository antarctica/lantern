from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for a collection with minimum required fields for open-access.

record = make_record(
    open_access=True,
    file_identifier="8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
    hierarchy_level=HierarchyLevelCode.COLLECTION,
    title="Test Resource - Collection with minimum required fields for open-access",
    abstract="Item to test minimal open-access Collection are supported and presented correctly.",
)
make_minimal_open_record(record)
