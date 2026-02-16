from bas_metadata_library.standards.magic_administration.v1 import Permission

OPEN_ACCESS = Permission(
    directory="*",
    group="*",
    comment="For public release.",
)

BAS_STAFF = Permission(
    directory="~nerc",
    group="~bas-staff",
    comment="Restricted to staff employed at the British Antarctic Survey.",
)
