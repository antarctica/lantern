# Set access permissions in a record's administration metadata

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
from tasks._shared import dump_records, ensure_admin, init, parse_records, pick_local_record

from lantern.lib.metadata_library.models.record.enums import MagicAccessFrameworkPermission
from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import set_admin

if TYPE_CHECKING:
    import logging

    from bas_metadata_library.standards.magic_administration.v1 import Permission
    from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

    from lantern.lib.metadata_library.models.record.record import Record

access_presets = [MagicAccessFrameworkPermission.OPEN_ACCESS, MagicAccessFrameworkPermission.BAS_STAFF]


def _make_permission(preset: MagicAccessFrameworkPermission, comment: str | None) -> Permission:
    """
    Create permission from present name if not None and optional comment.

    If preset is None or special 'NONE' name is used, return None (no permission).
    """
    permission = (
        BAS_STAFF
        if preset == MagicAccessFrameworkPermission.BAS_STAFF
        else OPEN_ACCESS
        if preset == MagicAccessFrameworkPermission.OPEN_ACCESS
        else None
    )
    if not permission:
        msg = "No supported permission selected."
        raise RuntimeError(msg) from None
    if permission and comment:
        permission.comment = comment
    return permission


def _get_cli_args() -> tuple[
    bool,
    Path,
    Path | None,
    MagicAccessFrameworkPermission,
    str | None,
    MagicAccessFrameworkPermission | None,
    str | None,
]:
    """
    Get command line arguments.

    Metadata and resource access permissions are based on the MAGIC Access Permissions Framework (v1) supported presets
    specifically (not the catalouge's AccessLevel enum which is similiar but not controlled across projects).

    The MagicAccessFrameworkPermission.CUSTOM_GROUPS permissions preset is not supported.

    Metadata access permissions are locked to open access, as the catalogue does not enforce metadata access
    permissions so will always evaluate to open access (unrestricted), which would be misleading if other values were
    allowed.
    """
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
        "--metadata-preset",
        "-mp",
        type=str,
        choices=[MagicAccessFrameworkPermission.OPEN_ACCESS.name],
        help="Metadata access constraint. Locked to OPEN-ACCESS.",
    )
    parser.add_argument(
        "--metadata-comment",
        "-mc",
        type=str,
        help="Optional metadata access comment. Will prompt if omitted.",
    )
    parser.add_argument(
        "--resource-preset",
        "-rp",
        type=str,
        choices=[a.name for a in access_presets],
        help="Optional resource access constraint. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--resource-comment",
        "-rc",
        type=str,
        help="Optional resource access comment. Will prompt if omitted.",
    )
    args = parser.parse_args()

    metadata_access = MagicAccessFrameworkPermission.OPEN_ACCESS
    resource_access = MagicAccessFrameworkPermission[args.resource_preset] if args.resource_preset else None

    return (
        args.force,
        args.path,
        args.record,
        metadata_access,
        args.metadata_comment,
        resource_access,
        args.resource_comment,
    )


def _return_args(
    import_path: Path,
    record_path: Path,
    record: Record,
    metadata_permission_t: MagicAccessFrameworkPermission,
    metadata_comment: str | None,
    resource_permission_t: MagicAccessFrameworkPermission,
    resource_comment: str | None,
) -> tuple[Path, Record, Permission | None, Permission | None, str]:
    _mps = f"--metadata-preset {metadata_permission_t}"
    _mc = f"--metadata-comment {metadata_comment}" if metadata_comment else ""
    _rps = f"--resource-preset {resource_permission_t.name}"
    _rc = f"--resource-comment {resource_comment}" if resource_comment else ""
    params = f"task restrict-record --force --path {import_path.resolve()} --record {record_path.resolve()} {_mps} {_mc} {_rps} {_rc}"

    return (
        import_path,
        record,
        _make_permission(metadata_permission_t, metadata_comment),
        _make_permission(resource_permission_t, resource_comment),
        params,
    )


def _get_args(
    logger: logging.Logger,
    cli_args: tuple[
        bool,
        Path,
        Path | None,
        MagicAccessFrameworkPermission,
        str | None,
        MagicAccessFrameworkPermission | None,
        str | None,
    ],
) -> tuple[Path, Record, Permission | None, Permission | None, str]:
    """Get task inputs, interactively if needed/allowed."""
    (
        cli_force,
        cli_records_path,
        cli_record_path,
        cli_metadata_preset_t,
        cli_metadata_comment,
        cli_resource_preset_t,
        cli_resource_comment,
    ) = cli_args

    import_path = cli_records_path
    record_path = cli_record_path
    metadata_permission_t = cli_metadata_preset_t
    metadata_comment = cli_metadata_comment
    resource_permission_t = cli_resource_preset_t
    resource_comment = cli_resource_comment

    if cli_force and not record_path:
        msg = "Record path must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if cli_force and not resource_permission_t:
        msg = "Resource permission preset must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if record_path:
        logger.info("Loading record from: %s'", record_path.resolve())
        record = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]

        return _return_args(
            import_path=import_path,
            record_path=record_path,
            record=record,
            metadata_permission_t=metadata_permission_t,
            metadata_comment=metadata_comment,
            resource_permission_t=resource_permission_t,  # ty: ignore[invalid-argument-type]
            resource_comment=resource_comment,
        )

    logger.info("Loading records from: '%s'", import_path.resolve())
    _record_paths = parse_records(logger=logger, search_path=import_path, validate_catalogue=True)
    record = pick_local_record(logger=logger, records=[rp[0] for rp in _record_paths])

    print("[=] Metadata access permission: OPEN_ACCESS (locked)")
    metadata_comment = inquirer.text("Metadata comment (optional)", default=cli_metadata_comment or "")
    resource_permission_n = inquirer.list_input(
        message="Resource access permission", choices=[a.name for a in access_presets], default=resource_permission_t
    )
    resource_permission_t = MagicAccessFrameworkPermission[resource_permission_n]
    resource_comment = inquirer.text("Resource comment (optional)", default=resource_comment or "")

    for rp in _record_paths:
        if record.file_identifier == rp[0].file_identifier:
            record_path = rp[1]
            break
    if not record_path:
        msg = f"File for record '{record.file_identifier}' not found"
        raise FileNotFoundError(msg) from None
    return _return_args(
        import_path=import_path,
        record_path=record_path,
        record=record,
        metadata_permission_t=metadata_permission_t,
        metadata_comment=metadata_comment,
        resource_permission_t=resource_permission_t,
        resource_comment=resource_comment,
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
        "Setting access permissions for '%a' as: %s (metadata), %s (resource)",
        record.file_identifier,
        metadata_permission,
        resource_permission,
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
    import_path, record, metadata_permission, resource_permission, params = _get_args(logger, cli_args)

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

    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
