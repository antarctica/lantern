# Indicate a record is a successor to an existing record

from __future__ import annotations

import logging
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, get_record, init, parse_records, pick_local_record
from tasks.records_zap import revise_record

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.aggregations import make_bas_cat_revision_of
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat_item
from lantern.models.item.base.item import ItemBase
from lantern.models.record.const import ALIAS_NAMESPACE
from lantern.models.record.record import Record

if TYPE_CHECKING:
    from lantern.catalogues.bas import BasCatalogue


def _get_cli_args() -> tuple[bool, bool, bool, Path, str | None, str | None, Path | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Indicate a record is a successor to an existing record.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force save path, branch and current identifier to defaults, and successor record selection to CLI argument.",
    )
    parser.add_argument(
        "--replace-in-collections",
        "-rc",
        action="store_true",
        help="Replace references to current record in collections with successor Will keep both if omitted.",
    )
    parser.add_argument(
        "--replace-aliases",
        "-ra",
        action="store_true",
        help="Move aliases from current record to successor Will keep both if omitted.",
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
        "-c",
        type=str,
        help="Optional current record identifier (file identifier, URL, or file name). Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--successor",
        "-s",
        type=Path,
        help="Optional path to successor record config file. Will interactively prompt if omitted.",
    )
    args = parser.parse_args()
    return (
        args.force,
        args.replace_in_collections,
        args.replace_aliases,
        args.path,
        args.branch,
        args.current,
        args.successor,
    )


def _get_args(
    logger: logging.Logger,
    cat: BasCatalogue,
    cli_args: tuple[bool, bool, bool, Path, str | None, str | None, Path | None],
) -> tuple[Path, str, str, Record, bool, bool, str]:
    """Get task inputs, interactively if needed/allowed."""
    (
        cli_force,
        cli_replace_collections,
        cli_replace_aliases,
        cli_path,
        cli_branch,
        cli_current_ref,
        cli_successor_path,
    ) = cli_args

    path = cli_path
    replace_collections = cli_replace_collections
    replace_aliases = cli_replace_aliases
    branch = cli_branch or cat.repo.gitlab_default_branch
    current_ref = cli_current_ref
    successor_path = cli_successor_path or None
    successor_record = None

    logger.info("Loading records from: '%s'", path.resolve())
    _record_paths = parse_records(logger=logger, search_path=path, validate_catalogue=True)
    _record_lookup = {rp[1].resolve(): rp[0] for rp in _record_paths}
    _path_lookup = {rp[0].file_identifier: rp[1] for rp in _record_paths}

    if not cli_force:
        path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=path))
        branch = inquirer.list_input(message="Branch", choices=cat.repo.select_branches())
        current_ref = inquirer.text(message="Current record reference", default=current_ref)
        if not successor_path:
            successor_record = pick_local_record(logger=logger, records=[rp[0] for rp in _record_paths])
        replace_collections: bool = (
            inquirer.list_input("Replace references to current record?", choices=["Yes", "No"], default="Yes") == "Yes"
        )
        replace_aliases: bool = (
            inquirer.list_input("Move aliases from current record to successor?", choices=["Yes", "No"], default="Yes")
            == "Yes"
        )
    else:
        if cli_successor_path is None:
            msg = "Successor record path must be set when using --force option for this task."
            raise RuntimeError(msg) from None
        try:
            successor_record = _record_lookup[cli_successor_path.resolve()]
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

    try:
        successor_path = _path_lookup[successor_record.file_identifier]
    except KeyError:
        msg = f"File for record '{successor_record.file_identifier}' not found"
        raise FileNotFoundError(msg) from None
    _replace_c = " --replace-in-collections" if replace_collections else ""
    _replace_a = " --replace-aliases" if replace_aliases else ""
    params = f"task supersede-record --force{_replace_c}{_replace_a} --path {path.resolve()} --branch {branch} --current {current_ref} --successor {successor_path.resolve()}"

    return path, branch, current_ref, successor_record, replace_collections, replace_aliases, params


def process_successor(
    logger: logging.Logger, record: Record, predecessor: Record, replace_collections: bool, replace_aliases: bool
) -> None:
    """
    Update successor record.

    Steps:
    - updates metadata datestamp
    - adds a 'revisionOf' aggregation referencing the predecessor record
    - copies over any collection aggregations from the predecessor record, if not already present
    - copies over any alias identifiers from the predecessor record, if not already present
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

    if replace_aliases:
        logger.info("Copying missing alias identifiers")
        for alias in predecessor.identification.identifiers.filter(namespace=ALIAS_NAMESPACE):
            record.identification.identifiers.ensure(alias)


def process_predecessor(
    logger: logging.Logger, record: Record, successor: Record, replace_collections: bool, replace_aliases: bool
) -> None:
    """
    Update predecessor record.

    Steps:
    - if collections replaced, removes collection aggregations which now belong to the successor
    - if aliases replaced, removes alias identifiers which now belong to the successor
    - sets resource maintenance progress to superseded
    - sets a superseded date
    - appends a free text note to the abstract that the item has been superseded
    - updates metadata datestamp if changes are made

    Note:
    - there isn't a 'revisedBy' inverse aggregation type that can be used
    - removing collection aggregations (replace=True) means the record is effectively orphaned and can only be
      accessed via search results or its direct URL
    """
    changed = False
    successor_item = ItemBase(record=successor)

    # Filter out collection aggregations
    collection_aggregations = record.identification.aggregations.filter(
        associations=AggregationAssociationCode.LARGER_WORK_CITATION, initiatives=AggregationInitiativeCode.COLLECTION
    )
    if replace_collections and collection_aggregations:
        changed = True
        logger.info("Removing collection aggregations from predecessor")
        logger.info("Predecessor contained %s collection aggregations", len(collection_aggregations))
        record.identification.aggregations = record.identification.aggregations.without(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )

    # Filter out aliases
    aliases = record.identification.identifiers.filter(namespace=ALIAS_NAMESPACE)
    if replace_aliases and aliases:
        changed = True
        logger.info("Removing alias identifiers from predecessor")
        logger.info("Predecessor contained %s alias identifiers", len(aliases))
        record.identification.identifiers = record.identification.identifiers.without(namespace=ALIAS_NAMESPACE)

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
    logger: logging.Logger, catalogue: BasCatalogue, branch: str, record: Record, predecessor: Record, replace: bool
) -> list[Record]:
    """
    Append or replace references to predecessor record in collections.

    - where replace=True : collection aggregations referencing the predecessor record are replaced with the successor.
    - where replace=False: collection aggregations referencing the predecessor are cloned to reference the successor
                            and prepended (to appear before the predecessor)

    I.e.: For a current/predecessor record A, with aggregations in collection C, replaced by record B:

    - aggregations in C, before:
        - ...
        - A (predecessor)
        - ...
    - where replace=True, aggregations become:
        - ...
        - B (successor)
        - ...
    - where replace=False, aggregations become:
        - ...
        - B (successor)
        - A (predecessor)
        - ...


    To ensure referential integrity between parent:children and children:parent relationships.
    """
    collection_ids = [
        c.identifier.identifier
        for c in record.identification.aggregations.filter(
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )
    ]
    logger.info("Predecessor belonged to %s collections", len(collection_ids))
    if logger.isEnabledFor(logging.DEBUG):
        for collection_id in collection_ids:
            logger.debug("- %s", collection_id)

    collections = [get_record(logger=logger, cat=catalogue, reference=cid, branch=branch) for cid in collection_ids]
    for collection in collections:
        if replace:
            revise = False
            # Update existing aggregations to reference successor
            for agg in collection.identification.aggregations:
                if agg.identifier.identifier == predecessor.file_identifier:
                    agg.identifier = make_bas_cat_item(record.file_identifier)
                    revise = True
            if revise:
                revise_record(collection)
        else:
            # Clone aggregations referencing predecessor to reference successor instead and prepend before existing
            new_aggs = [
                (
                    i,
                    Aggregation(
                        identifier=make_bas_cat_item(record.file_identifier),
                        association_type=agg.association_type,
                        initiative_type=agg.initiative_type,
                    ),
                )
                for i, agg in enumerate(collection.identification.aggregations)
                if agg.identifier.identifier == predecessor.file_identifier
                and Aggregation(
                    identifier=make_bas_cat_item(record.file_identifier),
                    association_type=agg.association_type,
                    initiative_type=agg.initiative_type,
                )
                not in collection.identification.aggregations
            ]
            if new_aggs:
                for i, new_agg in reversed(new_aggs):
                    collection.identification.aggregations.insert(i, new_agg)
                revise_record(collection)

    return [Record.loads(value=c.dumps(strip_admin=False)) for c in collections]  # return as catalogue records


def _check_unique(predecessor: Record, successor: Record, replace_collections: bool) -> None:
    """Ensure edition (if replaced), citation and any identifiers are different."""
    errors = []
    if replace_collections and successor.identification.edition == predecessor.identification.edition:
        errors.append("Editions must be different.")
    if successor.identification.other_citation_details == predecessor.identification.other_citation_details:
        errors.append("Citations must be different.")
    if any(identifier in predecessor.identification.identifiers for identifier in successor.identification.identifiers):
        errors.append("Identifiers must be different.")
    if errors:
        raise ValueError(" ".join(errors)) from None


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()

    cli_args = _get_cli_args()
    import_path, branch, current_ref, successor, replace_collections, replace_aliases, params = _get_args(
        logger=logger, cat=catalogue, cli_args=cli_args
    )
    _predecessor = get_record(logger=logger, cat=catalogue, reference=current_ref, branch=branch)
    predecessor = Record.loads(value=_predecessor.dumps(strip_admin=False))

    # update order is significant as collection aggregations may be moved from predecessor to successor
    process_successor(
        logger=logger,
        record=successor,
        predecessor=predecessor,
        replace_collections=replace_collections,
        replace_aliases=replace_aliases,
    )
    process_predecessor(
        logger=logger,
        record=predecessor,
        successor=successor,
        replace_collections=replace_collections,
        replace_aliases=replace_aliases,
    )
    collections = _process_collections(
        logger=logger,
        catalogue=catalogue,
        branch=branch,
        record=successor,
        predecessor=predecessor,
        replace=replace_collections,
    )

    _check_unique(predecessor=predecessor, successor=successor, replace_collections=replace_collections)
    dump_records(logger=logger, output_path=import_path, records=[predecessor, successor, *collections])

    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
