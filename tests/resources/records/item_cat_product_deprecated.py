from datetime import date
from textwrap import dedent

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.enums import (
    HierarchyLevelCode,
    ProgressCode,
)
from tests.resources.records.utils import make_record, relate_records

# An open-access record for testing a deprecated catalogue item.

record = make_record(
    open_access=True,
    file_identifier="0116d9fe-19c0-4d7f-a5a8-67a8ffed7da2",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product marked as deprecated",
    abstract="Item to test a Product which has been deprecated is presented correctly.",
)

record.identification.dates.deprecated = Date(date=date(2023, 10, 1))
record.identification.maintenance.progress = ProgressCode.DEPRECATED
record.identification.abstract += dedent("""\

> [!WARNING]
> This item is deprecated and should not be used.
""")

# add related peers
record.identification.aggregations.extend(relate_records(record.file_identifier, groups=["lifecycle"]))
