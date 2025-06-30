from lantern.models.record.elements.identification import Constraint, Constraints
from lantern.models.record.enums import ConstraintRestrictionCode, ConstraintTypeCode, HierarchyLevelCode
from tests.resources.records.utils import make_record

# Records for all supported licence usage constraints.

abstract = """
Item to test all supported licences:

- OGL v3
- CC BY v4
- X Operations Mapping v1
- X All Rights Reversed v1
"""

ogl_record = make_record(
    file_identifier="589408f0-f46b-4609-b537-2f90a2f61243",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (OGL v3)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
ogl_record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
            statement="Open Access (Anonymous)",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            statement="This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
        ),
    ]
)

cc_record = make_record(
    file_identifier="4ba929ac-ca32-4932-a15f-38c1640c0b0f",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (CC BY v4)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
cc_record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
            statement="Open Access (Anonymous)",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://creativecommons.org/licenses/by/4.0/",
            statement="This information is licensed under the Create Commons Attribution 4.0 International Licence (CC BY 4.0). To view this licence, visit https://creativecommons.org/licenses/by/4.0/",
        ),
    ]
)

ops_record = make_record(
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

rights_reversed_record = make_record(
    file_identifier="c993ea2b-d44e-4ca0-9007-9a972f7dd117",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Item to test licences (All Rights Reversed v1)",
    abstract=abstract,
    purpose="Item to test all supported licence usage constraints are presented correctly.",
)
rights_reversed_record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
            statement="Open Access (Anonymous)",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
            statement="All rights for this information are reserved. View the (Local) All Rights Reserved v1 licence, https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/, for more information.",
        ),
    ]
)
