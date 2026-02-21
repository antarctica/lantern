import logging
import sys
from pathlib import Path

import inquirer
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission
from bas_metadata_library.standards.magic_administration.v1.utils import (
    AdministrationKeys,
    AdministrationMetadataSubjectMismatchError,
)
from tasks._record_utils import dump_records, init, parse_records, pick_records

from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin
from lantern.models.item.base.enums import AccessLevel


def _get_args(
    logger: logging.Logger, records: list[Record]
) -> tuple[list[Record], Permission | None, Permission | None]:
    """
    Get user input.

    Returns a list of records to set (the same) metadata and resource permissions for.
    """
    levels = [al.name for al in AccessLevel]
    levels.remove(AccessLevel.NONE.name)
    levels.remove(AccessLevel.UNKNOWN.name)
    logger.debug(f"Levels: {levels}")

    records_picked = pick_records(logger=logger, records=records)
    answers = inquirer.prompt(
        [
            inquirer.List("m_level", message="Metadata: access level", choices=levels, default=AccessLevel.PUBLIC),
            inquirer.Text("m_comment", message="Metadata: comment (Optional)", default=""),
            inquirer.List("r_level", message="Resource: access level", choices=levels, default=AccessLevel.PUBLIC),
            inquirer.Text("r_comment", message="Resource: comment (Optional)", default=""),
        ]
    )

    permissions: list[Permission | None] = [None, None]
    for i, prefix in enumerate(["m", "r"]):
        if answers[f"{prefix}_level"] == AccessLevel.PUBLIC.name:
            permissions[i] = OPEN_ACCESS
        elif answers[f"{prefix}_level"] == AccessLevel.BAS_STAFF.name:
            permissions[i] = BAS_STAFF
        if isinstance(permissions[i], Permission) and answers[f"{prefix}_comment"] != "":
            permissions[i].comment = answers[f"{prefix}_comment"]  # ty:ignore[invalid-assignment]
    logger.info(f"Selected metadata permission: {permissions[0]}")
    logger.info(f"Selected resource permission: {permissions[1]}")

    return records_picked, permissions[0], permissions[1]


def _set_permission(
    logger: logging.Logger,
    keys: AdministrationKeys,
    record: Record,
    metadata_permission: Permission | None,
    resource_permission: Permission | None,
) -> None:
    """Set single access permission in a record, overwriting any possible existing permissions."""
    admin = None
    if record.file_identifier is None:
        msg = "File identifier required."
        raise ValueError(msg) from None
    try:
        admin = get_admin(keys=keys, record=record)
    except AdministrationMetadataSubjectMismatchError as e:
        # prompt user whether to ignore mismatch by clearing existing admin metadata
        if inquirer.confirm(
            message=(
                "Existing administration metadata references the wrong record. Drop existing metadata (if record is cloned)?"
            ),
            default=False,
        ):
            pass
        else:
            raise e from e
    if admin is None:
        logger.warning("No or unsupported administration metadata found, creating new instance.")
        if not inquirer.confirm(
            message="Existing administration metadata missing or unsupported, reset?",
            default=False,
        ):
            logger.info("Aborting.")
            sys.exit(1)
        admin = AdministrationMetadata(id=record.file_identifier)
    admin.metadata_permissions = [metadata_permission] if metadata_permission else []
    admin.resource_permissions = [resource_permission] if resource_permission else []
    logger.debug(
        f"Setting access permissions for '{record.file_identifier}' as: {metadata_permission} (metadata), {resource_permission} (resource)"
    )
    set_admin(keys=keys, record=record, admin_meta=admin)


def _set_permissions(
    logger: logging.Logger,
    keys: AdministrationKeys,
    records: list[Record],
    metadata_permission: Permission | None,
    resource_permission: Permission | None,
) -> None:
    """Set single access permission in records, overwriting any possible existing permissions."""
    for record in records:
        _set_permission(logger, keys, record, metadata_permission, resource_permission)


def main() -> None:
    """Entrypoint."""
    logger, config, _store, _s3 = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW

    print("\nNote: This task does not support:")
    print("- setting expiry dates for permissions")
    print("- setting expiry arbitrary groups for permissions")
    print("\nWARNING: This task will overwrite any existing permissions in selected records.")

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=input_path)]

    selected_records, metadata_permission, resource_permission = _get_args(logger=logger, records=records)
    if not metadata_permission and not resource_permission:
        logger.info("No permissions selected, aborting.")
        sys.exit(0)

    for record in records:
        _set_permission(
            logger=logger,
            keys=admin_keys,
            record=record,
            metadata_permission=metadata_permission,
            resource_permission=resource_permission,
        )
    dump_records(logger=logger, records=selected_records, output_path=input_path)


if __name__ == "__main__":
    main()
