from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for an ItemCatalogue instance with minimal fields for open-access collections.

record = make_record(
    file_identifier="8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
    hierarchy_level=HierarchyLevelCode.COLLECTION,
    title="Test Resource - Collection with minimum required fields for open-access",
    abstract="Item to test minimal open-access Collection are supported and presented correctly.",
)
make_minimal_open_record(record)
