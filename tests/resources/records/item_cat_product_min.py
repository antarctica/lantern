from lantern.lib.metadata_library.models.record.elements.common import Constraints
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_minimal_open_record, make_record

# A record for an ItemCatalogue instance with absolute minimum required fields.

record = make_record(
    file_identifier="3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product with minimum required fields",
    abstract="Item to test all minimal Product are supported and presented correctly.",
)
make_minimal_open_record(record)

# un-set non-required fields set by `make_record()`
record.metadata.constraints = Constraints([])
record.identification.constraints = Constraints([])
record.identification.supplemental_information = None
