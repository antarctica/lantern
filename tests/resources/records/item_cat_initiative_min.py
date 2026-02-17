from lantern.lib.metadata_library.models.record.elements.identification import Aggregations
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with minimum required fields for open-access initiatives.

record = make_record(
    file_identifier="c31720da-8c10-496a-893d-f003f09151e9",
    hierarchy_level=HierarchyLevelCode.INITIATIVE,
    title="Test Resource - Initiative with minimum required fields",
    abstract="Item to test all minimal Initiative are supported and presented correctly.",
)

# un-set non-required fields set by `make_record()`
record.identification.contacts[0].role = [ContactRoleCode.POINT_OF_CONTACT]
record.identification.aggregations = Aggregations([])
record.identification.purpose = None
