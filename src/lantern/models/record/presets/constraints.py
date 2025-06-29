from lantern.models.record.elements.identification import Constraint
from lantern.models.record.enums import ConstraintRestrictionCode, ConstraintTypeCode

OPEN_ACCESS = Constraint(
    type=ConstraintTypeCode.ACCESS,
    restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
    statement="Open Access (Anonymous)",
)

OGL_V3 = Constraint(
    type=ConstraintTypeCode.USAGE,
    restriction_code=ConstraintRestrictionCode.LICENSE,
    href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    statement="This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
)
