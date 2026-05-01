# Set gitlab issues in administration metadata in a record

import logging
from argparse import ArgumentParser
from pathlib import Path

import inquirer
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._shared import confirm, dump_records, ensure_admin, init, parse_records, pick_local_record

from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin


def _get_cli_args() -> tuple[bool, Path, Path | None, set[str]]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Set GitLab issues in administration metadata for a local record.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force path to local record and GitLab issues to set.",
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
        "-r",
        type=Path,
        help="Path to local record config to update. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "issues",
        nargs="*",
        help="Optional GitLab issue URL(s) as positional arguments.",
    )
    parser.add_argument(
        "--issue",
        action="append",
        help="Optional GitLab issue URL. Can be repeated.",
    )
    args = parser.parse_args()
    issues = set(list(args.issues or []) + list(args.issue or []))
    return args.force, args.path, args.record, issues


def _get_args(
    logger: logging.Logger, keys: AdministrationKeys, cli_args: tuple[bool, Path, Path | None, set[str]]
) -> tuple[Path, Record, set[str]]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_records_path, cli_record_path, cli_issues = cli_args

    import_path = cli_records_path
    record_path = cli_record_path
    issues = cli_issues

    if cli_force and not record_path:
        msg = "Record path must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if record_path:
        logger.info(f"Loading record from: '{record_path.resolve()}'")
        record = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]
        return import_path, record, issues

    logger.info(f"Loading records from: '{import_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=import_path)]
    record = pick_local_record(logger=logger, records=records)

    existing_issues = "\n".join(_get_issues(logger=logger, keys=keys, record=record))
    issues_raw = inquirer.editor(message="Issues (separate by new lines)", default=existing_issues)
    issues = {i for i in [i.replace(" ", "").strip() for i in issues_raw.split("\n")] if i}
    logger.info("Selected issues:")
    for i in issues:
        logger.info(i)
    confirm(logger=logger, message="Correct issues?")

    return import_path, record, issues


def _get_issues(logger: logging.Logger, keys: AdministrationKeys, record: Record) -> list[str]:
    """Get any GitLab issues set in a record."""
    admin = get_admin(keys=keys, record=record)
    if admin is None:
        logger.warning("No or unsupported administration metadata found, returning empty list.")
        return []
    return admin.gitlab_issues


def _set_issues(logger: logging.Logger, keys: AdministrationKeys, record: Record, issues: set[str]) -> None:
    """Set GitLab issues in a record via administration metadata, overwriting any existing issues."""
    for issue in issues:
        if "/-/issues/" not in issue:
            msg = f"URL '{issue}' is not a valid GitLab issue. Aborting."
            raise ValueError(msg) from None

    admin = ensure_admin(logger=logger, record=record, keys=keys)
    admin.gitlab_issues = list(issues)
    logger.debug(f"Setting GitLab issues for '{record.file_identifier}' as {issues}")
    set_admin(keys=keys, record=record, admin_meta=admin)


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW

    print("\nWARNING: This task will overwrite any existing issues in the selected record.")

    cli_args = _get_cli_args()
    import_path, record, issues = _get_args(logger=logger, keys=admin_keys, cli_args=cli_args)

    _set_issues(logger=logger, keys=admin_keys, record=record, issues=issues)
    dump_records(logger=logger, records=[record], output_path=import_path)


if __name__ == "__main__":
    main()
