from lantern.lib.metadata_library.models.record.elements.common import (
    Constraint,
    Constraints,
    Contact,
    ContactIdentity,
    Contacts,
)
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.constraints import OGL_V3, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role
from tests.resources.records.utils import make_record

# Open-access records to test all supported licences.

abstract = """
Item to test all supported resource licences:

- OGL v3
- CC BY v4
- Copernicus Sentinel data v1
- X Operations Mapping v1
- X MAGIC Products v1
- X All Rights Reversed v1
"""

ogl_record = make_record(
    open_access=True,
    file_identifier="589408f0-f46b-4609-b537-2f90a2f61243",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (OGL v3)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
ogl_record.identification.constraints = Constraints(
    [
        OPEN_ACCESS,
        OGL_V3,
    ]
)

cc_record = make_record(
    open_access=True,
    file_identifier="4ba929ac-ca32-4932-a15f-38c1640c0b0f",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (CC BY v4)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
cc_record.identification.constraints = Constraints(
    [
        OPEN_ACCESS,
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://creativecommons.org/licenses/by/4.0/",
            statement="This information is licensed under the Creative Commons Attribution 4.0 International Licence (CC BY 4.0). To view this licence, visit https://creativecommons.org/licenses/by/4.0/",
        ),
    ]
)

ops_record = make_record(
    open_access=False,
    file_identifier="5ab58461-5ba7-404d-a904-2b4efcb7556e",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (Operations Mapping v1)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
ops_record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.RESTRICTED,
            statement="Closed Access",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/",
            statement="This information is licensed under the (Local) Operations Mapping v1 licence. To view this licence, visit https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/.",
        ),
    ]
)

magic_products_record = make_record(
    open_access=False,
    file_identifier="60c05109-d15e-4b43-9e36-d4fd9d7c606b",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (MAGIC Products v1)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
magic_products_record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.RESTRICTED,
            statement="Closed Access",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/magic-products-v1/",
            statement="This information is licensed under the (Local) MAGIC Products v1 licence. To view this licence, visit https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/.",
        ),
    ]
)

rights_reversed_record = make_record(
    open_access=True,
    file_identifier="c993ea2b-d44e-4ca0-9007-9a972f7dd117",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (All Rights Reversed v1)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
rights_reversed_record.identification.constraints = Constraints(
    [
        OPEN_ACCESS,
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
            statement="All rights for this information are reserved. View the (Local) All Rights Reserved v1 licence, https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/, for more information.",
        ),
    ]
)

copernicus_sentinel_record = make_record(
    open_access=True,
    file_identifier="43287219-40aa-47fd-809e-21b50773a052",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (Copernicus Sentinel v1)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
copernicus_sentinel_record.identification.constraints = Constraints(
    [
        OPEN_ACCESS,
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://cds.climate.copernicus.eu/licences/ec-sentinel",
            statement="This information is licensed under the Copernicus Sentinel data licence (rev. 1).",
        ),
    ]
)
copernicus_sentinel_record.identification.contacts = Contacts(
    [
        make_magic_role({ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER}),
        Contact(organisation=ContactIdentity(name="European Commission"), role={ContactRoleCode.RIGHTS_HOLDER}),
    ]
)
