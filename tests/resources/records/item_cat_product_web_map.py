from lantern.lib.metadata_library.models.record.enums import (
    HierarchyLevelCode,
)
from tests.resources.records.utils import make_record, relate_products

# An open-access record for a web map product.

record = make_record(
    open_access=True,
    file_identifier="a59b5c5b-b099-4f01-b670-3800cb65e666",
    hierarchy_level=HierarchyLevelCode.WEB_MAP_PRODUCT,
    title="Test Resource - Web Map Product",
    abstract="Item to test a Product for a Web Map is presented correctly.",
)
# add related peers
record.identification.aggregations.extend(relate_products(record.file_identifier))
