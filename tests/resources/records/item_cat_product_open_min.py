from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for an ItemCatalogue instance with minimum required fields for open-access products.

record = make_record(
    file_identifier="b0e92ec2-b018-4f9f-a1e1-bc0fe195619f",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product with minimum required fields for open-access",
    abstract="Item to test minimal open-access Products are supported and presented correctly.",
)
make_minimal_open_record(record)
