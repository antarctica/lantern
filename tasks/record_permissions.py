# Set access permissions in a record's administration metadata

import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Literal, get_args

import inquirer
from bas_metadata_library.standards.magic_administration.v1 import Permission
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._shared import dump_records, ensure_admin, init, parse_records, pick_local_record

from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import set_admin

AccessPreset = Literal["OPEN_ACCESS", "BAS_STAFF", "NONE"]


def _match_preset(permission: Permission | None) -> AccessPreset:
    """Try to match permission to present name."""
    if permission == OPEN_ACCESS:
        return "OPEN_ACCESS"
    if permission == BAS_STAFF:
        return "BAS_STAFF"
    return "NONE"


def _make_permission(preset: AccessPreset | None, comment: str | None) -> Permission | None:
    """
    Create permission from present name if not None and optional comment.

    If preset is None or special 'NONE' name is used, return None (no permission).
    """
    permission = BAS_STAFF if preset == "BAS_STAFF" else OPEN_ACCESS if preset == "OPEN_ACCESS" else None
    if permission and comment:
        permission.comment = comment
    return permission


def _get_cli_args() -> tuple[bool, Path, Path | None, AccessPreset | None, str | None, AccessPreset | None, str | None]:
    """Get command line arguments."""
    parser = ArgumentParser(
        description="Set resource and metadata administration access permissions for a local record."
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force path to local record and resource/metadata access permissions to set.",
    )
    parser.add_argument(
        "--path",
        "-d",
        type=Path,
        default=Path("./import"),
        help="Directory to local records. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--record",
        "-c",
        type=Path,
        help="Path to local record config to update. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--resource-preset",
        "-rp",
        type=str,
        choices=get_args(AccessPreset),
        help="Optional resource access constraint. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--resource-comment",
        "-rc",
        type=str,
        help="Optional resource access comment. Will prompt if omitted.",
    )
    parser.add_argument(
        "--metadata-preset",
        "-mp",
        type=str,
        choices=get_args(AccessPreset),
        help="Optional metadata access constraint. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--metadata-comment",
        "-mc",
        type=str,
        help="Optional metadata access comment. Will prompt if omitted.",
    )
    args = parser.parse_args()
    return (
        args.force,
        args.path,
        args.record,
        args.resource_preset,
        args.resource_comment,
        args.metadata_preset,
        args.metadata_comment,
    )


def _get_args(
    logger: logging.Logger,
    cli_args: tuple[bool, Path, Path | None, AccessPreset | None, str | None, AccessPreset | None, str | None],
) -> tuple[Path, Record, Permission | None, Permission | None]:
    """Get task inputs, interactively if needed/allowed."""
    (
        cli_force,
        cli_records_path,
        cli_record_path,
        cli_resource_preset_t,
        cli_resource_comment,
        cli_metadata_preset_t,
        cli_metadata_comment,
    ) = cli_args

    import_path = cli_records_path
    record_path = cli_record_path
    resource_permission_t = cli_resource_preset_t
    resource_comment = cli_resource_comment
    metadata_permission_t = cli_metadata_preset_t
    metadata_comment = cli_metadata_comment

    if cli_force and not record_path:
        msg = "Record path must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if record_path:
        logger.info(f"Loading record from: '{record_path.resolve()}'")
        record = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]
        return (
            import_path,
            record,
            _make_permission(resource_permission_t, resource_comment),
            _make_permission(metadata_permission_t, metadata_comment),
        )

    logger.info(f"Loading records from: '{import_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=import_path)]
    record = pick_local_record(logger=logger, records=records)

    resource_permission_t = inquirer.list_input(
        message="Resource access permission", choices=get_args(AccessPreset), default=resource_permission_t
    )
    resource_comment = inquirer.text("Resource comment (optional)", default=resource_comment or "")
    metadata_permission_t = inquirer.list_input(
        message="Resource access permission", choices=get_args(AccessPreset), default=resource_permission_t
    )
    metadata_comment = inquirer.text("Metadata comment (optional)", default=cli_metadata_comment or "")

    return (
        import_path,
        record,
        _make_permission(resource_permission_t, resource_comment),
        _make_permission(metadata_permission_t, metadata_comment),
    )


def _set_permission(
    logger: logging.Logger,
    keys: AdministrationKeys,
    record: Record,
    metadata_permission: Permission | None,
    resource_permission: Permission | None,
) -> None:
    """Set single access permission in a record, overwriting any possible existing permissions."""
    admin = ensure_admin(logger=logger, record=record, keys=keys)
    admin.metadata_permissions = [metadata_permission] if metadata_permission else []
    admin.resource_permissions = [resource_permission] if resource_permission else []
    logger.debug(
        f"Setting access permissions for '{record.file_identifier}' as: {metadata_permission} (metadata), {resource_permission} (resource)"
    )
    set_admin(keys=keys, record=record, admin_meta=admin)


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW

    print("\nNote: This task does not support:")
    print("- setting expiry dates for permissions")
    print("- setting expiry arbitrary groups for permissions")
    print("\nWARNING: This task will overwrite any existing permissions in selected records.")

    cli_args = _get_cli_args()
    import_path, record, resource_permission, metadata_permission = _get_args(logger, cli_args)

    if not metadata_permission and not resource_permission:
        logger.info("No permissions selected, aborting.")
        sys.exit(0)

    _set_permission(
        logger=logger,
        keys=admin_keys,
        record=record,
        metadata_permission=metadata_permission,
        resource_permission=resource_permission,
    )
    dump_records(logger=logger, records=[record], output_path=import_path)


if __name__ == "__main__":
    main()
