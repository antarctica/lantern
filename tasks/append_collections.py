"""Append local records to their parent catalogue collections for later import."""

from __future__ import annotations

from argparse import ArgumentParser
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, init, parse_records, pick_local_records
from tasks.records_zap import revise_record, update_collection_aggregations, update_collection_extent

from lantern.lib.metadata_library.models.record.enums import AggregationAssociationCode, AggregationInitiativeCode
from lantern.models.record.const import CATALOGUE_NAMESPACE

if TYPE_CHECKING:
    import logging

    from lantern.catalogues.bas import BasCatalogue
    from lantern.lib.metadata_library.models.record.record import Record
    from lantern.models.record.revision import RecordRevision


def _get_cli_args() -> tuple[bool, Path, str | None, list[Path]]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Append records to any parent collections.")
    parser.add_argument("--force", "-f", action="store_true", help="Use CLI paths without prompting.")
    parser.add_argument(
        "--import-path",
        "-i",
        type=Path,
        default=Path("./import"),
        help="Import directory for source record and updated collections.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        type=str,
        default=None,
        help="branch to read collections from. Will prompt or use default if omitted.",
    )
    parser.add_argument("--path", "-p", type=Path, action="append", help="Record config files to process")
    args = parser.parse_args()
    return args.force, args.import_path, args.branch, args.path or []


def _get_args(
    logger: logging.Logger, cat: BasCatalogue, cli_args: tuple[bool, Path, str | None, list[Path]]
) -> tuple[Path, str, list[Record], str]:
    """Resolve selected record config, interactively unless forced."""
    force, import_path, cli_branch, paths = cli_args
    branch = cli_branch or cat.repo.gitlab_default_branch
    if force and not paths:
        msg = "At least one record path must be set when using --force."
        raise RuntimeError(msg)

    if not force:
        import_path = Path(
            inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=import_path)
        )
        branch = inquirer.list_input(message="Branch", choices=cat.repo.select_branches(), default=branch)
        logger.info("Loading records from: '%s'", import_path.resolve())
        candidates = parse_records(logger=logger, search_path=import_path, validate_catalogue=True)
        selected = pick_local_records(logger=logger, records=[record for record, _ in candidates])
        selected_ids = {record.file_identifier for record in selected}
        paths = [path for record, path in candidates if record.file_identifier in selected_ids]

    records: list[Record] = []
    for path in paths:
        if not path.is_file():
            msg = f"Record config not found: '{path.resolve()}'"
            raise FileNotFoundError(msg)
        logger.info("Loading record from: '%s'", path.resolve())
        matches = parse_records(logger=logger, search_path=path.parent, glob_pattern=path.name, validate_catalogue=True)
        if not matches:
            msg = f"No valid record for selection '{path.resolve()}'."
            raise RuntimeError(msg)
        records.append(matches[0][0])

    path_args = " ".join(f"--path {path.resolve()}" for path in paths)
    params = f"task append-collections --force --import-path {import_path.resolve()} --branch {branch} {path_args}"
    return import_path, branch, records, params


def append_collection(
    logger: logging.Logger, collection: RecordRevision, records: list[Record]
) -> RecordRevision | None:
    """Append records to a collection, returning a revised copy only if it changed."""
    updated = deepcopy(collection)
    for record in records:
        if update_collection_aggregations(logger=logger, record=record, collection=updated):
            update_collection_extent(logger=logger, record=record, collection=updated)
    if updated == collection:
        logger.info("Collection '%s' unchanged, skipping", collection.file_identifier)
        return None
    revise_record(updated)
    updated.validate()
    logger.info("Collection '%s' updated", collection.file_identifier)
    return updated


def append_collections(
    logger: logging.Logger, cat: BasCatalogue, branch: str, records: list[Record]
) -> list[RecordRevision]:
    """Fetch parent collections and append matching records to each one."""
    parents: dict[str, list[Record]] = {}
    for record in records:
        aggregations = record.identification.aggregations.filter(
            namespace=CATALOGUE_NAMESPACE,
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )
        for aggregation in aggregations:
            parents.setdefault(aggregation.identifier.identifier, []).append(record)

    updated: list[RecordRevision] = []
    for identifier, members in parents.items():
        collection = cat.repo.select_record(identifier, branch=branch)
        result = append_collection(logger=logger, collection=collection, records=members)
        if result is not None:
            updated.append(result)
    return updated


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()
    cli_args = _get_cli_args()
    import_path, branch, records, params = _get_args(logger=logger, cat=catalogue, cli_args=cli_args)
    collections = append_collections(logger=logger, cat=catalogue, branch=branch, records=records)
    dump_records(logger=logger, output_path=import_path, records=collections)
    logger.info("Wrote %s updated collections to '%s'", len(collections), import_path.resolve())
    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
