# Indicate a record is a successor to an existing record
import logging
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, get_gitlab_source, get_record, init, parse_records, pick_local_record
from tasks.records_zap import revise_record

from lantern.catalogues.bas import BasCatalogue
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.identification import Aggregations
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.aggregations import make_bas_cat_revision_of
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat_item
from lantern.models.item.base.item import ItemBase
from lantern.models.record.record import Record


def _get_cli_args() -> tuple[bool, Path, str | None, str | None, Path | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Indicate a record is a successor to an existing record.")
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
        help="Directory to save current and successor records to. Will use default if omitted.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        type=str,
        default=None,
        help="Optional Git branch/ref to read records from. Will prompt or use default if omitted.",
    )
    parser.add_argument(
        "--current",
        type=str,
        help="Optional current record identifier (file identifier, URL, or file name). Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--successor",
        type=Path,
        help="Optional path to successor record config file. Will interactively prompt if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.path, args.branch, args.current, args.successor


def _get_args(
    logger: logging.Logger,
    cat: BasCatalogue,
    cli_args: tuple[bool, Path, str | None, str | None, Path | None],
) -> tuple[Path, str, str, Record]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_path, cli_branch, cli_current_ref, cli_successor_path = cli_args

    path = cli_path
    branch = cli_branch if cli_branch else cat.repo.gitlab_default_branch
    current_ref = cli_current_ref
    successor_path = cli_successor_path if cli_successor_path else None
    successor_record = None

    logger.info(f"Loading records from: '{path.resolve()}'")
    records_paths = parse_records(logger=logger, search_path=path, validate_catalogue=True)

    if not cli_force:
        path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=path))
        branch = get_gitlab_source(logger=logger, cat=cat, action="Fetching records from")
        current_ref = inquirer.text(message="Current record reference", default=current_ref)
        if not successor_path:
            successor_record = pick_local_record(logger=logger, records=[rp[0] for rp in records_paths])
    else:
        lookup = {rp[1].resolve(): rp[0] for rp in records_paths}
        if cli_successor_path is None:
            msg = "Successor record path must be set when using --force option for this task."
            raise RuntimeError(msg) from None
        try:
            successor_record = lookup[cli_successor_path.resolve()]
        except KeyError:
            raise FileNotFoundError() from None

    msg = "Target path, branch, current record identifier and successor record MUST be set for this task."
    if not isinstance(path, Path):
        raise TypeError(msg) from None
    if not isinstance(branch, str):
        raise TypeError(msg) from None
    if not isinstance(current_ref, str):
        raise TypeError(msg) from None
    if not isinstance(successor_record, Record):
        raise TypeError(msg) from None

    return path, branch, current_ref, successor_record


def _process_successor(logger: logging.Logger, record: Record, predecessor: Record) -> None:
    """
    Update successor record.

    Steps:
    - updates metadata datestamp
    - adds a 'revisionOf' aggregation referencing the predecessor record
    - copies over any collection aggregations from the predecessor record, if not already present
    - sanity checks the successor record has a different citation, edition and identifiers
    """
    revise_record(record)

    logger.info("Adding revisionOf aggregation")
    record.identification.aggregations.ensure(make_bas_cat_revision_of(item_id=predecessor.file_identifier))

    logger.info("Copying missing collection aggregations")
    collection_aggregations = predecessor.identification.aggregations.filter(
        associations=AggregationAssociationCode.LARGER_WORK_CITATION, initiatives=AggregationInitiativeCode.COLLECTION
    )
    for agg in collection_aggregations:
        record.identification.aggregations.ensure(agg)

    # Ensure edition, citation and any identifiers are different
    errors = []
    if record.identification.edition == predecessor.identification.edition:
        errors.append("Editions must be different.")
    if record.identification.other_citation_details == predecessor.identification.other_citation_details:
        errors.append("Citations must be different.")
    for identifier in record.identification.identifiers:
        if identifier in predecessor.identification.identifiers:
            errors.append("Identifiers must be different.")
    if errors:
        raise ValueError(" ".join(errors)) from None


def _process_predecessor(logger: logging.Logger, record: Record, successor: Record) -> None:
    """
    Update predecessor record.

    Steps:
    - removes collection aggregations which now belong to the successor
    - sets resource maintenance progress to superseded
    - sets a superseded date
    - appends a free text note to the abstract that the item has been superseded
    - updates metadata datestamp if changes are made

    Note:
    - there isn't a 'revisedBy' inverse aggregation type that can be used
    - removing collection aggregations means the record is effectively orphaned and can only be accessed via its
    direct URL, unless linked to elsewhere.
    """
    changed = False
    successor_item = ItemBase(record=successor)

    # Filter out collection_aggregations
    collection_aggregations = record.identification.aggregations.filter(
        associations=AggregationAssociationCode.LARGER_WORK_CITATION, initiatives=AggregationInitiativeCode.COLLECTION
    )
    if collection_aggregations:
        changed = True
        logger.info("Removing collection aggregations from predecessor")
        record.identification.aggregations = Aggregations(
            [r for r in record.identification.aggregations if r not in collection_aggregations]
        )
        logger.info(f"Predecessor contained {len(collection_aggregations)} collection aggregations")

    # Set superseded status
    if record.identification.dates.superseded is None:
        changed = True
        logger.info("Adding superseded date")
        record.identification.dates.superseded = Date(date=datetime.now(tz=UTC))
    if record.identification.maintenance.progress != ProgressCode.SUPERSEDED:
        changed = True
        logger.info("Predecessor maintenance progress updated")
        record.identification.maintenance.progress = ProgressCode.SUPERSEDED

    # Add note to abstract
    _sigil = "[!NOTE] A new edition of this item is available"
    if _sigil not in record.identification.abstract:
        changed = True
        logger.info("Appending note to predecessor abstract")
        record.identification.abstract += dedent(f"""\

            > {_sigil}
            >
            > Please see [{successor_item.title_md}](/items/{successor_item.resource_id}), edition **{successor_item.edition}**.
         """)

    if not changed:
        logger.info("Predecessor record not updated")
    revise_record(record)


def _process_collections(
    logger: logging.Logger, catalogue: BasCatalogue, branch: str, record: Record, predecessor: Record
) -> list[Record]:
    """
    Replace references to predecessor record in collections.

    To ensure referential integrity between parent:children and children:parent relationships.
    """
    collection_ids = [
        c.identifier.identifier
        for c in record.identification.aggregations.filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )
    ]
    logger.info(f"Predecessor belonged to {len(collection_ids)} collections")
    if logger.isEnabledFor(logging.DEBUG):
        for collection_id in collection_ids:
            logger.debug(f"- {collection_id}")

    collections = [get_record(logger=logger, cat=catalogue, reference=cid, branch=branch) for cid in collection_ids]
    for collection in collections:
        revise_record(collection)
        for agg in collection.identification.aggregations:
            if agg.identifier.identifier == predecessor.file_identifier:
                agg.identifier = make_bas_cat_item(record.file_identifier)

    return [Record.loads(value=c.dumps(strip_admin=False)) for c in collections]  # return as catalogue records


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()

    cli_args = _get_cli_args()
    import_path, branch, current_ref, successor = _get_args(logger=logger, cat=catalogue, cli_args=cli_args)
    _predecessor = get_record(logger=logger, cat=catalogue, reference=current_ref, branch=branch)
    predecessor = Record.loads(value=_predecessor.dumps(strip_admin=False))

    # order is significant as collection aggregations are moved from predecessor to successor
    _process_successor(logger=logger, record=successor, predecessor=predecessor)
    _process_predecessor(logger=logger, record=predecessor, successor=successor)
    collections = _process_collections(
        logger=logger, catalogue=catalogue, branch=branch, record=successor, predecessor=predecessor
    )

    dump_records(logger=logger, output_path=import_path, records=[predecessor, successor, *collections])


if __name__ == "__main__":
    main()
