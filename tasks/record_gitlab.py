# Set gitlab issues in administration metadata in a record

import logging
from pathlib import Path

import inquirer
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._record_utils import confirm, dump_records, ensure_admin, init, parse_records

from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin


def _get_issues(logger: logging.Logger, keys: AdministrationKeys, record: Record) -> list[str]:
    """Get any GitLab issues set in a record."""
    admin = get_admin(keys=keys, record=record)
    if admin is None:
        logger.warning("No or unsupported administration metadata found, returning empty list.")
        return []
    return admin.gitlab_issues


def _set_issues(logger: logging.Logger, keys: AdministrationKeys, record: Record, issues: list[str]) -> None:
    """Set GitLab issues in a record via administration metadata, overwriting any existing issues."""
    for issue in issues:
        if "/-/issues/" not in issue:
            msg = f"URL '{issue}' is not a valid GitLab issue. Aborting."
            raise ValueError(msg) from None

    admin = ensure_admin(logger=logger, record=record, keys=keys)
    admin.gitlab_issues = issues
    logger.debug(f"Setting GitLab issues for '{record.file_identifier}' as {issues}")
    set_admin(keys=keys, record=record, admin_meta=admin)


def _get_args(logger: logging.Logger, records: list[Record], keys: AdministrationKeys) -> tuple[Record, list[str]]:
    """
    Get user input.

    Returns a record and list of GitLab issues.
    """
    choices = {
        f"{r.file_identifier} ('{r.identification.title}' {r.hierarchy_level.value})": r.file_identifier
        for r in records
    }
    logger.debug(f"Choices: {list(choices.keys())}")
    selection = inquirer.list_input(message="Record", choices=list(choices.keys()))
    file_identifier = choices[selection]

    logger.info(f"Selected file_identifier: {file_identifier}")
    record = {r.file_identifier: r for r in records}[file_identifier]

    existing_issues = "\n".join(_get_issues(logger=logger, keys=keys, record=record))
    issues_raw = inquirer.editor(message="Issues (separate by new lines)", default=existing_issues)
    issues = [i for i in [i.replace(" ", "").strip() for i in issues_raw.split("\n")] if i]
    logger.info("Selected issues:")
    for i in issues:
        logger.info(i)
    confirm(logger=logger, message="Correct issues?")

    return record, issues


def main() -> None:
    """Entrypoint."""
    logger, config, _store = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW

    print("\nWARNING: This task will overwrite any existing issues in the selected record.")

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=input_path)]

    selected_record, issues = _get_args(logger=logger, records=records, keys=admin_keys)
    _set_issues(logger=logger, keys=admin_keys, record=selected_record, issues=issues)
    dump_records(logger=logger, records=[selected_record], output_path=input_path)


if __name__ == "__main__":
    main()
