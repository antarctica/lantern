from lantern.lib.metadata_library.models.record.enums import (
    HierarchyLevelCode,
)
from tests.resources.records.utils import make_record, relate_products

# An open-access record for a map product.

record = make_record(
    open_access=True,
    file_identifier="8422d4e7-654f-4fbb-a5e0-4051ee21418e",
    hierarchy_level=HierarchyLevelCode.MAP_PRODUCT,
    title="Test Resource - Map Product",
    abstract="Item to test a Product for a Map is presented correctly.",
)
# add related peers
record.identification.aggregations.extend(relate_products(record.file_identifier))
