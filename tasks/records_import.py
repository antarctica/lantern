import json
import logging
from collections.abc import Generator
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import inquirer

from lantern.config import Config
from lantern.lib.metadata_library.models.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.aggregations import make_bas_cat_collection_member
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.item.base.const import CATALOGUE_NAMESPACE
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import GitLabStore

magic_collection_ids = [
    "0ed7da71-72e1-46e4-a482-064433d4c73d",  # SCAR Antarctic Digital Database (ADD) Supplemental Datasets
    "6f5102ae-dfae-4d72-ad07-6ce4c85f5db8",  # BAS Published Maps
    "8ff8240d-dcfa-4906-ad3b-507929842012",  # SCAR Antarctic Digital Database (ADD) Previous Datasets
    "d0d91e22-18c1-4c7f-8dfc-20e94cd2c107",  # BAS General Interest Maps
    "e74543c0-4c4e-4b41-aa33-5bb2f67df389",  # SCAR Antarctic Digital Database (ADD)
    "ef7bc35e-7ad8-4ae5-9ae8-dd708d6e966e",  # BAS Operations Maps
    "cf64dd21-545a-465b-9a67-c28bb4ce9024",  # BAS Basemaps
    "faaeca6f-e67a-45df-ad6d-10c3049daab3",  # BAS Geology Maps
]


def _parse_configs(search_path: Path) -> Generator[dict, None, None]:
    """
    Try to load any record configurations from JSON files from a directory.

    Subdirectories are NOT searched.
    """
    for json_path in search_path.glob("*.json"):
        with json_path.open("r") as f:
            yield json.load(f)


def _parse_records(logger: logging.Logger, search_path: Path) -> list[Record]:
    """
    Try to create Records from record configurations within a directory.

    Records must validate.
    """
    records = []
    configs = list(_parse_configs(search_path))
    for config in configs:
        try:
            record = Record.loads(config)
            record.validate()
        except RecordInvalidError:
            logger.warning(f"Record '{config['file_identifier']}' does not validate, skipping.")
            continue
        if not Record._config_supported(config):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append(record)
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _revise_collection(time: datetime, collection: Record) -> None:
    """Indicate collection change via edition and other relevant properties."""
    if collection.identification.dates.revision is None:
        collection.identification.dates.revision = Date(date=time)
    collection.identification.dates.revision.date = time
    collection.identification.edition = str(int(collection.identification.edition) + 1)


def _revise_record(record: Record) -> None:
    """Indicate record change via relevant properties."""
    now = datetime.now(tz=UTC).replace(microsecond=0)
    record.metadata.date_stamp = now.date()
    if record.hierarchy_level == HierarchyLevelCode.COLLECTION:
        _revise_collection(time=now, collection=record)


def _revise_records(logger: logging.Logger, records: list[Record], store: GitLabStore) -> None:
    """Indicate record change via relevant properties if needed."""
    for record in records:
        try:
            existing_record = store.get(record.file_identifier)
            if record != existing_record:
                logger.info(f"Record '{record.file_identifier}' is different to stored version, revising")
                _revise_record(record)
        except RecordNotFoundError:
            logger.info(f"Record '{record.file_identifier}' not found in store, skipping revision")
            continue


def _update_collection_aggregations(logger: logging.Logger, record: Record, collection: Record) -> None:
    """Add aggregation back-refs if missing to a collections a record is part of."""
    if (
        record.file_identifier
        in collection.identification.aggregations.filter(identifiers=record.file_identifier).identifiers()
    ):
        logger.debug(
            f"Record '{record.file_identifier}' already in collection '{collection.file_identifier}', skipping"
        )
        return
    collection.identification.aggregations.append(make_bas_cat_collection_member(record.file_identifier))
    logger.info(f"Added record '{record.file_identifier}' to collection '{collection.file_identifier}'")


def _update_collection_extent(logger: logging.Logger, record: Record, collection: Record) -> None:
    record_extent = record.identification.extents.filter(identifier="bounding")[0].geographic.bounding_box
    collection_extent = collection.identification.extents.filter(identifier="bounding")[0].geographic.bounding_box

    record_bbox = [
        record_extent.west_longitude,
        record_extent.east_longitude,
        record_extent.south_latitude,
        record_extent.north_latitude,
    ]
    collection_bbox = [
        deepcopy(collection_extent.west_longitude),
        deepcopy(collection_extent.east_longitude),
        deepcopy(collection_extent.south_latitude),
        deepcopy(collection_extent.north_latitude),
    ]
    bboxes = [record_bbox, collection_bbox]

    collection_extent.west_longitude = min([bbox[0] for bbox in bboxes])
    collection_extent.east_longitude = max([bbox[1] for bbox in bboxes])
    collection_extent.south_latitude = min([bbox[2] for bbox in bboxes])
    collection_extent.north_latitude = max([bbox[3] for bbox in bboxes])

    collection_bbox_updated: list[float] = [
        collection_extent.west_longitude,
        collection_extent.east_longitude,
        collection_extent.south_latitude,
        collection_extent.north_latitude,
    ]
    if collection_bbox_updated != collection_bbox:
        logger.debug(f"Collection extent '{collection.file_identifier}' updated")
        logger.debug(
            f"From: {', '.join([str(c) for c in collection_bbox])} to: {', '.join([str(c) for c in collection_bbox_updated])}"
        )
    else:
        logger.debug(f"Collection extent '{collection.file_identifier}' unchanged, skipping update")
        return


def _update_record_collections(logger: logging.Logger, record: Record, collections: dict[str, Record]) -> None:
    """
    Update in-scope collections a record is part of.

    Where in-scope `collections` is a file identifier indexed dict of in-scope collection records.

    The input record is not modified, any matched collections are updated in-place.

    Steps:
    - get record collection identifiers via aggregations
    - get the intersection between these identifiers and in-scope collections
    - update relevant properties for each of these collections via sub-methods
    """
    parent_collections = record.identification.aggregations.filter(
        namespace=CATALOGUE_NAMESPACE,
        associations=AggregationAssociationCode.LARGER_WORK_CITATION,
        initiatives=AggregationInitiativeCode.COLLECTION,
    )
    record_collection_ids = [c.identifier.identifier for c in parent_collections]
    filtered_record_collection_ids = set(record_collection_ids).intersection(set(collections.keys()))
    logger.info(f"Record contains {len(filtered_record_collection_ids)} in-scope collections to update")

    for collection_id in filtered_record_collection_ids:
        collection = collections[collection_id]
        _update_collection_aggregations(logger=logger, record=record, collection=collection)
        _update_collection_extent(logger=logger, record=record, collection=collection)


def _process_magic_collections(
    logger: logging.Logger, records: list[Record], additional_records: list[Record], store: GitLabStore
) -> None:
    """
    Update in-scope MAGIC collections for records authored in Zap and other MAGIC workflows.

    Zap authored records can be added to one or more MAGIC collections, which adds a child to parent aggregation.
    For records to be shown correctly in the Catalogue, an inverse aggregation is needed in the relevant collection.
    Collections are also updated to reflect the new overall bounding extent of the items they contain.

    Some MAGIC collections are out-of-scope because they managed by another service or process:
    - b85852eb-c7fb-435f-8239-e13a28612ef4 (Assets Tracking Service) - externally managed
    - b8b78c6c-fac2-402c-a772-9f518c7121e5 (MAGIC team) - manually managed
    """
    collections = [store.get(record_id) for record_id in magic_collection_ids]
    collections_updated = {c.file_identifier: deepcopy(c) for c in collections}

    for record in records:
        _update_record_collections(
            logger=logger,
            record=record,
            collections=collections_updated,
        )

    for collection in collections:
        updated_collection = collections_updated[collection.file_identifier]
        if collection != updated_collection:
            logger.info(f"Collection '{collection.file_identifier}' updated, including with commit")
            additional_records.append(updated_collection)


def _process_records(logger: logging.Logger, records: list[Record], store: GitLabStore) -> list[Record]:
    """
    Process records as needed.

    `additional_records` returns any other records created or modified during processing that should be included.

    Where any of these records are modified, the date_stamp and other relevant properties are revised.
    """
    additional_records: list[Record] = []
    _process_magic_collections(logger=logger, records=records, additional_records=additional_records, store=store)
    _revise_records(logger=logger, records=[*records, *additional_records], store=store)
    return additional_records


def _clean_input_path(input_path: Path) -> None:
    """Remove imported files."""
    for json_path in input_path.glob("*.json"):
        json_path.unlink(missing_ok=True)


def _get_args() -> tuple[str, str, str, str]:
    """Get user input."""
    answers = inquirer.prompt(
        [
            inquirer.Text("title", message="Changeset summary"),
            inquirer.Editor("message", message="Changeset detail"),
            inquirer.Text("name", message="Author name", default="Felix Fennell"),
            inquirer.Text("email", message="Author email", default="felnne@bas.ac.uk"),
        ]
    )
    return answers["title"], answers["message"], answers["name"], answers["email"]


def main() -> None:
    """Entrypoint."""
    init_logging()
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    config = Config()
    store = GitLabStore(
        logger=logger,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    title, message, author_name, author_email = _get_args()
    store.populate()
    records = _parse_records(logger=logger, search_path=input_path)
    records.extend(_process_records(logger=logger, records=records, store=store))
    store.push(records=records, title=title, message=message, author=(author_name, author_email))
    _clean_input_path(input_path=input_path)


if __name__ == "__main__":
    main()
