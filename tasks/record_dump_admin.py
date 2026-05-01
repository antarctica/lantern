# Display administration metadata set in a record

import json
import logging
from argparse import ArgumentParser
from pathlib import Path

import cattrs
import inquirer
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from inquirer import Path as InquirerPath
from tasks._shared import init, parse_records, pick_local_record

from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


def _get_cli_args() -> tuple[bool, Path, Path | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Dump administrative metadata from a record.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force import path to default or set value, and record path from which to dump administration metadata.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to select records from. Will use default if omitted.",
    )
    parser.add_argument(
        "--record",
        "-r",
        type=Path,
        help="Set specific record config file to preview. Will prompt for available files in local records directory if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.path, args.record


def _get_args(logger: logging.Logger, cli_args: tuple[bool, Path, Path | None]) -> Record:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_import_path, cli_record_path = cli_args

    import_path = cli_import_path
    record_path = cli_record_path

    if cli_force and not record_path:
        msg = "Record path must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if record_path:
        logger.info(f"Loading record from: '{record_path.resolve()}'")
        return parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]

    import_path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=import_path))
    logger.info(f"Loading records from: '{import_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=import_path)]
    return pick_local_record(logger=logger, records=records)


def _dumps_admin_meta(logger: logging.Logger, admin_keys: AdministrationKeys, record: Record) -> None:
    """
    Get and display admin metadata.

    Replaces the metadata datestamp, file identifier, catalogue identifier and administrative metadata identifier only.

    Other references to the original record such as other identifiers, citations, etc. are not changed.
    """
    admin_meta = get_admin(keys=admin_keys, record=record)
    if admin_meta is None:
        msg = "Missing administrative metadata in source record."
        raise ValueError(msg) from None
    converter = cattrs.Converter()
    converter.register_unstructure_hook(AdministrationMetadata, lambda d: d.unstructure())
    result = clean_dict(converter.unstructure(admin_meta))
    logger.info("Admin metadata:")
    logger.info(json.dumps(result, indent=2))


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    cli_args = _get_cli_args()
    record = _get_args(logger=logger, cli_args=cli_args)
    _dumps_admin_meta(logger=logger, admin_keys=config.ADMIN_METADATA_KEYS, record=record)


if __name__ == "__main__":
    main()
