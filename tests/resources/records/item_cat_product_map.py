from lantern.lib.metadata_library.models.record.enums import (
    HierarchyLevelCode,
)
from tests.resources.records.utils import make_record, relate_products

# A record for an ItemCatalogue instance with minimum required fields for map products.

record = make_record(
    file_identifier="8422d4e7-654f-4fbb-a5e0-4051ee21418e",
    hierarchy_level=HierarchyLevelCode.MAP_PRODUCT,
    title="Test Resource - Map Product",
    abstract="Item to test a Product for a Map is presented correctly.",
)
# add related peers
record.identification.aggregations.extend(relate_products(record.file_identifier))
