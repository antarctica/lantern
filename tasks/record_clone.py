import logging
from argparse import ArgumentParser
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import inquirer
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._record_utils import dump_records, init, process_record_selections

from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.record import Record as CatalogueRecord
from lantern.stores.gitlab import GitLabStore


def _get_cli_args() -> dict:
    """
    Get optional command line arguments.

    Missing arguments will be prompted for interactively and return as None here.
    """
    parser = ArgumentParser(description="Clone record from cache into import directory.")
    parser.add_argument(
        "--source",
        type=str,
        help="Optional source record identifier (file identifier, URL, or file name). Will interactively prompt if missing.",
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Optional target record identifier. Will interactively prompt if missing.",
    )
    return {"source_id": parser.parse_args().source, "target_id": parser.parse_args().target}


def _get_record(logger: logging.Logger, store: GitLabStore, identifier: str | None = None) -> Record:
    """Get record from store using flexible, and optionally preset, identifier."""
    if identifier is None:
        identifier = inquirer.prompt([inquirer.Text("id", message="Record identifier")])["id"]
    file_identifier = next(iter(process_record_selections(logger=logger, identifiers=[identifier])))
    return store.select_one(file_identifier=file_identifier)


def _get_new_identifier(identifier: str | None = None) -> str:
    if identifier is not None:
        return identifier
    return inquirer.prompt(
        [
            inquirer.Text("id", message="File identifier (random default)", default=str(uuid4())),
        ]
    )["id"]


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
        msg = "Missing administrative metadata in source record."
        raise ValueError(msg) from None
    admin_meta.id = cloned_record.file_identifier
    set_admin(keys=admin_keys, record=cloned_record, admin_meta=admin_meta)

    # validate against catalogue requirements
    record = CatalogueRecord.loads(cloned_record.dumps(strip_admin=False))
    record.validate()

    return cloned_record


def main() -> None:
    """Entrypoint."""
    logger, config, store, _s3 = init()

    input_path = Path("./import")
    args = _get_cli_args()

    source_record = _get_record(logger=logger, store=store, identifier=args["source_id"])
    target_identifier = _get_new_identifier(identifier=args["target_id"])
    new_record = _clone_record(
        logger=logger,
        admin_keys=config.ADMIN_METADATA_KEYS,
        source_record=source_record,
        new_identifier=target_identifier,
    )
    dump_records(logger=logger, output_path=input_path, records=[new_record])


if __name__ == "__main__":
    main()
