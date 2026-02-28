from lantern.lib.metadata_library.models.record.enums import (
    HierarchyLevelCode,
)
from tests.resources.records.utils import make_record

# An open-access record for testing a superseded catalogue item.

record = make_record(
    open_access=True,
    file_identifier="7e3611a6-8dbf-4813-aaf9-dadf9decff5b",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product marked as superseded",
    abstract="Item to test a Product which has been superseded is presented correctly.",
)
