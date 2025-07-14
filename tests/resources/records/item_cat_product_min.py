from lantern.lib.metadata_library.models.record.elements.identification import Aggregations
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with minimum required fields for products.

record = make_record(
    file_identifier="3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product with minimum required fields",
    abstract="Item to test all minimal Product are supported and presented correctly.",
)
# un-set non-required fields set by `make_record()`
record.identification.contacts[0].role = [ContactRoleCode.POINT_OF_CONTACT]
record.identification.aggregations = Aggregations([])
