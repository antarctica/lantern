# Indicate a record is retired and no longer available

from __future__ import annotations

from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, init, parse_records, pick_local_record
from tasks.records_zap import revise_record

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.enums import ProgressCode
from lantern.models.record.record import Record

if TYPE_CHECKING:
    import logging


def _get_cli_args() -> tuple[bool, Path, Path | None, str | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Indicate a record is retired and no longer available.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force save path, branch and current identifier to defaults, and successor record selection to CLI argument.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to save records to. Will use default if omitted.",
    )
    parser.add_argument(
        "--record",
        "-r",
        type=Path,
        help="Optional path to record config file. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        help="Optional message to include in to caution admonition.",
    )
    args = parser.parse_args()
    return args.force, args.path, args.record, args.message


def _get_args(
    logger: logging.Logger, cli_args: tuple[bool, Path, Path | None, str | None]
) -> tuple[Path, Record, str | None, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_path, cli_record_path, cli_message = cli_args

    path = cli_path
    record_path = cli_record_path or None
    record = None
    message = cli_message

    logger.info("Loading records from: '%s'", path.resolve())
    _record_paths = parse_records(logger=logger, search_path=path, validate_catalogue=True)
    _record_lookup = {rp[1].resolve(): rp[0] for rp in _record_paths}
    _path_lookup = {rp[0].file_identifier: rp[1] for rp in _record_paths}

    if not cli_force:
        path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=path))
        if not record_path:
            record = pick_local_record(logger=logger, records=[rp[0] for rp in _record_paths])
        message = inquirer.text(message="Optional message to include in caution admonition.", default=message or "")
        message = message or None
    else:
        if cli_record_path is None:
            msg = "Record path must be set when using --force option for this task."
            raise RuntimeError(msg) from None
        try:
            record = _record_lookup[cli_record_path.resolve()]
        except KeyError:
            raise FileNotFoundError() from None

    msg = "Records and record paths MUST be set for this task."
    if not isinstance(path, Path):
        raise TypeError(msg) from None
    if not isinstance(record, Record):
        raise TypeError(msg) from None

    try:
        record_path = _path_lookup[record.file_identifier]
    except KeyError:
        msg = f"File for record '{record.file_identifier}' not found"
        raise FileNotFoundError(msg) from None

    _message_flag = f" --message '{message}'" if message else ""
    params = f"task retire-record --force --path {path.resolve()} --record {record_path.resolve()}{_message_flag}"

    return path, record, message, params


def process_record(logger: logging.Logger, record: Record, message: str | None = None) -> None:
    """
    Update record.

    Steps:
    - sets resource maintenance progress to retired
    - sets an unavailable date
    - appends a free text caution to the abstract that the item is retired
    - removes any distribution options
    - updates metadata datestamp if changes are made
    """
    changed = False

    # Set retired status
    if record.identification.dates.unavailable is None:
        changed = True
        logger.info("Adding unavailable date")
        record.identification.dates.unavailable = Date(date=datetime.now(tz=UTC))
    if record.identification.maintenance.progress != ProgressCode.RETIRED:
        changed = True
        logger.info("Record maintenance progress updated")
        record.identification.maintenance.progress = ProgressCode.RETIRED

    # Add note to abstract
    _sigil = "This item is retired and can no longer be used."
    if _sigil not in record.identification.abstract:
        changed = True
        logger.info("Appending caution to abstract")
        if message:
            record.identification.abstract += dedent(f"""\

                > [!CAUTION] {_sigil}
                > {message}
            """)
        else:
            record.identification.abstract += dedent(f"""\

                > [!CAUTION]
                > {_sigil}
            """)

    # Clear distribution options
    record.distribution.clear()

    if not changed:
        logger.info("Record not updated")
    revise_record(record)


def main() -> None:
    """Entrypoint."""
    logger, _config, _catalogue = init()

    cli_args = _get_cli_args()
    import_path, record, message, params = _get_args(logger=logger, cli_args=cli_args)

    process_record(logger=logger, record=record, message=message)
    dump_records(logger=logger, output_path=import_path, records=[record])

    logger.info('Re-run as: "%s"', params)


if __name__ == "__main__":
    main()
