from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import (
    AdministrationKeys,
)
from bas_metadata_library.standards.magic_administration.v1.utils import (
    get_admin as _get_admin,
)
from bas_metadata_library.standards.magic_administration.v1.utils import (
    set_admin as _set_admin,
)

from lantern.lib.metadata_library.models.record.record import Record


def get_admin(keys: AdministrationKeys, record: Record) -> AdministrationMetadata | None:
    """
    Get administrative metadata for record if available.

    Checks loaded administrative metadata relates to parent discovery metadata record via resource (file) identifier.
    """
    return _get_admin(keys=keys, config=record.dumps(strip_admin=False))


def set_admin(keys: AdministrationKeys, record: Record, admin_meta: AdministrationMetadata) -> None:
    """Set administrative metadata for record."""
    config = record.dumps(strip_admin=False)
    _set_admin(keys=keys, config=config, admin_meta=admin_meta)
    record.identification.supplemental_information = config["identification"]["supplemental_information"]
