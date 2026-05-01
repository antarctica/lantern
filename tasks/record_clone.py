# Create a new record based on an existing record

import logging
from argparse import ArgumentParser
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import inquirer
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, get_gitlab_source, get_record, init

from lantern.catalogues.bas import BasCatalogue
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.record import Record as CatalogueRecord


def _get_cli_args() -> tuple[bool, Path, str | None, str | None, str | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Clone record from cache into import directory.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force save path, branch and target identifier to defaults, and source record selection to CLI argument.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to save cloned record to. Will use default if omitted.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        type=str,
        default=None,
        help="Optional Git branch/ref to read records from. Will prompt or use default if omitted.",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Optional source record identifier (file identifier, URL, or file name). Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Optional target record identifier. Will interactively prompt or use default new value if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.path, args.branch, args.source, args.target


def _get_args(
    logger: logging.Logger,
    cat: BasCatalogue,
    cli_args: tuple[bool, Path, str | None, str | None, str | None],
) -> tuple[Path, str, str, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_path, cli_branch, cli_source_ref, cli_target_id = cli_args

    path = cli_path
    branch = cli_branch if cli_branch else cat.repo.gitlab_default_branch
    source_ref = cli_source_ref
    target_id = cli_target_id if cli_target_id else str(uuid4())

    if not cli_force:
        path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=path))
        branch = get_gitlab_source(logger=logger, cat=cat, action="Fetching records from")
        source_ref = inquirer.text(message="Source record reference", default=source_ref)
        target_id = inquirer.text(message="Target record identifier (random default)", default=target_id)

    msg = "Target path, branch and source/target identifiers MUST be set for this task."
    if not isinstance(path, Path):
        raise TypeError(msg) from None
    if not isinstance(branch, str):
        raise TypeError(msg) from None
    if not isinstance(source_ref, str):
        raise TypeError(msg) from None
    if not isinstance(target_id, str):
        raise TypeError(msg) from None

    return path, branch, source_ref, target_id


def _get_new_identifier(identifier: str | None = None) -> str:
    if identifier is not None:
        return identifier
    return inquirer.text(message="File identifier (random default)", default=str(uuid4()))


def _clone_record(
    logger: logging.Logger, admin_keys: AdministrationKeys, source_record: Record, new_identifier: str
) -> Record:
    """
    Clone a record with a new identifier.

    Replaces the metadata datestamp, file identifier, catalogue identifier and administrative metadata identifier only.

    Other references to the original record such as other identifiers, citations, etc. are not changed.
    """
    logger.info(f"Cloning record [{source_record.file_identifier}] as [{new_identifier}]")
    cloned_record = deepcopy(source_record)

    # datestamp
    cloned_record.metadata.date_stamp = datetime.now(tz=UTC).date()

    # file identifier
    cloned_record.file_identifier = new_identifier

    # catalogue identifier
    for i, identifier in enumerate(source_record.identification.identifiers):
        if identifier.namespace == CATALOGUE_NAMESPACE:
            cloned_record.identification.identifiers[i] = make_bas_cat(cloned_record.file_identifier)

    # admin metadata
    admin_meta = get_admin(keys=admin_keys, record=source_record)  # can't use cloned record as ID will mismatch
    if admin_meta is None:
        logger.warning("Missing/unrecognised administrative metadata in source record, setting minimal instance.")
        admin_meta = AdministrationMetadata(id=cloned_record.file_identifier)
    admin_meta.id = cloned_record.file_identifier
    set_admin(keys=admin_keys, record=cloned_record, admin_meta=admin_meta)

    # validate against catalogue requirements
    record = CatalogueRecord.loads(cloned_record.dumps(strip_admin=False))
    record.validate()

    return cloned_record


def main() -> None:
    """Entrypoint."""
    logger, config, catalogue = init()

    cli_args = _get_cli_args()
    import_path, branch, source_ref, target_id = _get_args(logger=logger, cat=catalogue, cli_args=cli_args)

    source_record = get_record(logger=logger, cat=catalogue, reference=source_ref, branch=branch)
    target_identifier = _get_new_identifier(identifier=target_id)
    new_record = _clone_record(
        logger=logger,
        admin_keys=config.ADMIN_METADATA_KEYS_RW,
        source_record=source_record,
        new_identifier=target_identifier,
    )
    dump_records(logger=logger, output_path=import_path, records=[new_record])


if __name__ == "__main__":
    main()
