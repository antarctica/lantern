from lantern.lib.metadata_library.models.record.elements.administration import Permission

OPEN_ACCESS = Permission(
    directory="*",
    group="~public",
    comments="For public release.",
)

BAS_STAFF = Permission(
    directory="~nerc",
    group="~bas-staff",
    comments="Restricted to staff employed by UKRI at BAS.",
)
