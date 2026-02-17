from lantern.lib.metadata_library.models.record.elements.identification import Aggregations
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with minimal fields for open-access collections.

record = make_record(
    file_identifier="8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
    hierarchy_level=HierarchyLevelCode.COLLECTION,
    title="Test Resource - Collection with minimal required fields",
    abstract="Item to test a minimal Collection is accepted and presented correctly.",
    purpose="Item to test a minimal Collection is accepted and presented correctly.",
)

# Reset collection members
record.identification.aggregations = Aggregations([])

# un-set non-required fields set by `make_record()`
record.identification.purpose = None
