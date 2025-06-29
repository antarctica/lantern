import json
import logging
from collections.abc import Generator
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from bas_metadata_library import RecordValidationError

from lantern.config import Config
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.record import Record, RecordInvalidError
from lantern.models.record.enums import AggregationAssociationCode, AggregationInitiativeCode, HierarchyLevelCode
from lantern.models.record.presets.aggregations import make_bas_cat_collection_member
from lantern.stores.base_store import RecordNotFoundError
from lantern.stores.gitlab import GitLabStore


def _parse_configs(search_path: Path) -> Generator[dict, None, None]:
    for json_path in search_path.glob("*.json"):
        with json_path.open("r") as f:
            yield json.load(f)


def _parse_records(logger: logging.Logger, search_path: Path) -> list[Record]:
    records = []
    configs = list(_parse_configs(search_path))
    for config in configs:
        try:
            record = Record.loads(config)
            record.validate()
        except RecordValidationError:
            logger.warning(f"Record '{config['file_identifier']}' does not validate, skipping.")
            continue
        if not Record.config_supported(config):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append(record)
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _revise_collection(collection: Record) -> Record:
    """Indicate collection change via edition and relevant dates."""
    now = datetime.now(tz=UTC).replace(microsecond=0)
    collection.metadata.date = now.date().isoformat()
    collection.identification.dates.revision.date = now
    collection.identification.edition = str(int(collection.identification.edition) + 1)
    return collection


def _update_collection_aggregations(logger: logging.Logger, record: Record, collection: Record) -> None:
    """Add aggregation back-refs if missing to a collections a record is part of."""
    # TODO: Enhance aggregations.filter to add an identifier param to avoid checking all children
    collection_items = [
        item.identifier.identifier
        for item in collection.identification.aggregations.filter(
            namespace="data.bas.ac.uk",
            associations=AggregationAssociationCode.IS_COMPOSED_OF,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )
    ]
    if record.file_identifier in collection_items:
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


def _process_record_collections(logger: logging.Logger, record: Record, collections: dict[str, Record]) -> None:
    """Update in-scope collections a record is part of."""
    parent_collections = record.identification.aggregations.filter(
        namespace="data.bas.ac.uk",
        associations=AggregationAssociationCode.LARGER_WORK_CITATION,
        initiatives=AggregationInitiativeCode.COLLECTION,
    )
    record_collection_ids = [c.identifier.identifier for c in parent_collections]
    record_magic_collection_ids = set(record_collection_ids).intersection(
        set(file_identifier for file_identifier in collections)
    )
    logger.info(f"Record contains {len(record_magic_collection_ids)} in-scope magic collections")

    for collection_id in record_magic_collection_ids:
        collection = collections[collection_id]
        _update_collection_aggregations(logger=logger, record=record, collection=collection)
        _update_collection_extent(logger=logger, record=record, collection=collection)


def _process_magic_collections(
    logger: logging.Logger, records: list[Record], additional_records: list[Record], store: GitLabStore
) -> None:
    """
    Update in-scope MAGIC collections for records authored in Zap.

    Zap authored records can be added to one or more MAGIC collections, which adds a child to parent aggregation.
    For records to be shown correctly in the Catalogue, an inverse aggregation is needed in the relevant collection.
    Collections are also updated to reflect the new overall bounding extent of the items they contain.

    Some MAGIC collections are out-of-scope because they managed by another service or process:
    - b85852eb-c7fb-435f-8239-e13a28612ef4 (Assets Tracking Service) - externally managed
    - b8b78c6c-fac2-402c-a772-9f518c7121e5 (MAGIC team) - manually managed
    """
    magic_collection_ids = [
        "d0d91e22-18c1-4c7f-8dfc-20e94cd2c107",  # BAS General Interest Maps
        "ef7bc35e-7ad8-4ae5-9ae8-dd708d6e966e",  # BAS Operations Maps
        "6f5102ae-dfae-4d72-ad07-6ce4c85f5db8",  # BAS Published Maps
        "e74543c0-4c4e-4b41-aa33-5bb2f67df389",  # SCAR Antarctic Digital Database (ADD)
        "8ff8240d-dcfa-4906-ad3b-507929842012",  # SCAR Antarctic Digital Database (ADD) Previous Datasets
        "0ed7da71-72e1-46e4-a482-064433d4c73d",  # SCAR Antarctic Digital Database (ADD) Supplemental Datasets
    ]
    collections = [store.get(record_id) for record_id in magic_collection_ids]
    collections_updated = {c.file_identifier: deepcopy(c) for c in collections}

    for record in records:
        _process_record_collections(
            logger=logger,
            record=record,
            collections=collections_updated,
        )

    for collection in collections:
        updated_collection = collections_updated[collection.file_identifier]
        if collection != updated_collection:
            logger.info(f"Collection '{collection.file_identifier}' updated, including with commit")
            additional_records.append(_revise_collection(updated_collection))


def _process_published_maps_workaround(logger: logging.Logger, records: list[Record]) -> None:
    published_maps_collection_id = "6f5102ae-dfae-4d72-ad07-6ce4c85f5db8"
    open_access = Constraint(
        type=ConstraintTypeCode.ACCESS,
        restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
        statement="Open Access (Anonymous)",
    )
    x_all_rights_v1 = Constraint(
        type=ConstraintTypeCode.USAGE,
        restriction_code=ConstraintRestrictionCode.LICENSE,
        href="https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
        statement="This information is licensed under the (Local) All Rights Reserved v1 licence. To view this licence, visit https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/.",
    )

    for record in records:
        # TODO: Enhance aggregations.filter to add an identifier param to avoid checking all children
        record_collection_ids = [
            item.identifier.identifier
            for item in record.identification.aggregations.filter(
                namespace="data.bas.ac.uk",
                associations=AggregationAssociationCode.LARGER_WORK_CITATION,
                initiatives=AggregationInitiativeCode.COLLECTION,
            )
        ]
        paper_map_parent = record.identification.aggregations.filter(initiatives=AggregationInitiativeCode.PAPER_MAP)
        if published_maps_collection_id not in record_collection_ids and not paper_map_parent:
            logger.debug(f"Record '{record.file_identifier}' not in published maps collection, skipping")
            continue

        licence_result = record.identification.constraints.filter(href=x_all_rights_v1.href)
        if not licence_result:
            logger.debug(f"Record '{record.file_identifier}' not using 'All Rights Reserved' licence, skipping")
            continue

        logger.debug(f"Fixed incorrect access constraint for record '{record.file_identifier}'")
        record.identification.constraints = Constraints([open_access, x_all_rights_v1])


def _process_records(logger: logging.Logger, records: list[Record], store: GitLabStore) -> list[Record]:
    """
    Process records if needed.

    `additional_records` returns any other records created or modified during processing that should be included in the
    store (e.g. updated collections).
    """
    additional_records: list[Record] = []
    _process_magic_collections(logger=logger, records=records, additional_records=additional_records, store=store)
    _process_published_maps_workaround(logger=logger, records=records)
    return additional_records


def main() -> None:
    """Entrypoint."""
    # TODO: If a record is modified, update date_stamp
    input_path = Path("import")
    message = "Fixing published map records"
    author_name = "Felix Fennell"
    author_email = "felnne@bas.ac.uk"

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
    store.populate()

    records = _parse_records(logger=logger, search_path=input_path)
    records.extend(_process_records(logger=logger, records=records, store=store))
    store.push(records=records, message=message, author=(author_name, author_email))


if __name__ == "__main__":
    main()
