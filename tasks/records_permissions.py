import logging
import sys
from pathlib import Path

import inquirer
from tasks._record_utils import dump_records, init, parse_records

from lantern.lib.metadata_library.models.record.elements.administration import Administration, Permission
from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import (
    AdministrationKeys,
    AdministrativeMetadataSubjectMismatchError,
    get_admin,
    set_admin,
)
from lantern.models.item.base.enums import AccessLevel


def _get_args(logger: logging.Logger, records: list[Record]) -> tuple[list[Record], Permission | None]:
    """Get user input."""
    choices = {
        f"{r.file_identifier} ('{r.identification.title}' {r.hierarchy_level.value})": r.file_identifier
        for r in records
    }
    levels = [al.name for al in AccessLevel]
    levels.remove(AccessLevel.NONE.name)
    levels.remove(AccessLevel.UNKNOWN.name)
    logger.debug(f"Choices: {list(choices.keys())}")
    logger.debug(f"Levels: {levels}")

    answers = inquirer.prompt(
        [
            inquirer.Checkbox(
                "selections",
                message="Records",
                choices=list(choices.keys()),
            ),
            inquirer.List("level", message="Access level", choices=levels),
            inquirer.Text("comment", message="Comment (Optional)", default=""),
        ]
    )

    records_ = {r.file_identifier: r for r in records}
    selected_fids = [choices[k] for k in answers["selections"]]
    logger.info(f"Selected records: {selected_fids}")
    selected_records = [records_[fid] for fid in selected_fids]

    permission = None
    if answers["level"] == AccessLevel.PUBLIC.name:
        permission = OPEN_ACCESS
    elif answers["level"] == AccessLevel.BAS_STAFF.name:
        permission = BAS_STAFF
    if permission and answers["comment"] != "":
        permission.comment = answers["comment"]
    logger.info(f"Selected permission: {permission}")

    return selected_records, permission


def _set_permission(logger: logging.Logger, keys: AdministrationKeys, record: Record, permission: Permission) -> None:
    """Set single access permission in a record, overwriting any possible existing permissions."""
    admin = None
    try:
        admin = get_admin(keys=keys, record=record)
    except AdministrativeMetadataSubjectMismatchError as e:
        # prompt user whether to ignore mismatch by clearing existing admin metadata
        if inquirer.confirm(
            message=(
                "Existing administrative metadata references the wrong record. Drop existing metadata (if record is cloned)?"
            ),
            default=False,
        ):
            pass
        else:
            raise e from e
    if admin is None:
        admin = Administration(id=record.file_identifier)
    admin.access_permissions = [permission]
    logger.debug(f"Setting access permissions for '{record.file_identifier}' as: {permission}")
    set_admin(keys=keys, record=record, admin_meta=admin)


def _set_permissions(
    logger: logging.Logger, keys: AdministrationKeys, records: list[Record], permission: Permission
) -> None:
    """Set single access permission in records, overwriting any possible existing permissions."""
    for record in records:
        _set_permission(logger, keys, record, permission)


def main() -> None:
    """Entrypoint."""
    logger, _config, _store, _s3, keys = init()

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=input_path)]

    selected_records, permission = _get_args(logger=logger, records=records)
    if not permission:
        logger.info("No permission selected, aborting.")
        sys.exit(0)

    for record in records:
        _set_permission(logger, keys, record, permission)
    dump_records(logger=logger, records=selected_records, output_path=input_path)


if __name__ == "__main__":
    main()
