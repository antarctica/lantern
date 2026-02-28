from lantern.lib.metadata_library.models.record.elements.common import Constraints
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for testing absolutely minimum required fields.

record = make_record(
    open_access=False,
    file_identifier="3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product with minimum required fields",
    abstract="Item to test all minimal Product are supported and presented correctly.",
)

# Un-set non-required fields set by `make_record()`, except those needed for open-access
make_minimal_open_record(record)
# Un-set non-required fields needed for open-access
record.metadata.constraints = Constraints([])
record.identification.constraints = Constraints([])
record.identification.supplemental_information = None
