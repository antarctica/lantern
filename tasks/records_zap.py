import json
import logging
from collections.abc import Generator
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from environs import Env
from jwskate import Jwk

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.administration import Administration, Permission
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.aggregations import make_bas_cat_collection_member
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin, set_admin
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.record.const import CATALOGUE_NAMESPACE
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
    "2fc581f3-8c7c-4ea5-a4a2-b133a437ff41",  # BAS Map Catalogue
    "00203387-0840-447c-b9ae-f25088501031",  # BAS Air Operations Planning Maps
    "6793faf5-16c5-42dc-a835-b214db7f3e85",  # SCAR Air Operations Planning Maps
    "5dc748d4-0e6e-4cdc-acc8-f24283bc585c",  # BAS Operations Datasets
    "7ed4d15e-952f-4be6-893a-9a9fef197426",  # BAS Polar Estates Maps
    "b8b78c6c-fac2-402c-a772-9f518c7121e5",  # BAS MAGIC
    "cf6dee46-493f-464c-8380-c8b2c5356508",  # BAS Legacy Maps
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
        except RecordInvalidError as e:
            logger.warning(f"Record '{config['file_identifier']}' does not validate, skipping.")
            logger.info(e.validation_error)
            continue
        if not Record._config_supported(config, logger):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append(record)
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _dump_records(logger: logging.Logger, records: list[Record], output_path: Path) -> None:
    """Dump records to JSON files in a directory."""
    output_path.mkdir(parents=True, exist_ok=True)
    for record in records:
        record_path = output_path / f"{record.file_identifier}.json"
        with record_path.open("w") as f:
            f.write(record.dumps_json(strip_admin=False))
        logger.info(f"Dumped new or revised record '{record.file_identifier}' to '{record_path.resolve()}'")


def _clean_input_path(input_path: Path) -> None:
    """Remove imported zap authored files."""
    for json_path in input_path.glob("zap-*.json"):
        json_path.unlink(missing_ok=True)


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
            if record.dumps(strip_admin=False) != existing_record.dumps(strip_admin=False):
                logger.info(f"Record '{record.file_identifier}' is different to stored version, revising")
                _revise_record(record)
            else:
                logger.info(f"Record '{record.file_identifier}' unchanged, skipping revision")
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
        _update_record_collections(logger=logger, record=record, collections=collections_updated)

    for collection in collections:
        updated_collection = collections_updated[collection.file_identifier]
        if collection != updated_collection:
            logger.info(f"Collection '{collection.file_identifier}' updated, including with commit")
            additional_records.append(updated_collection)


def _get_gitlab_issues(logger: logging.Logger, record: Record) -> list[str] | None:
    """
    Get and remove GitLab issues from record identifiers if present.

    Return issue URLs to add to admin metadata instead.
    """
    glab_identifiers = record.identification.identifiers.filter(namespace="gitlab.data.bas.ac.uk")
    logger.info(f"Record '{record.file_identifier}' has {len(glab_identifiers)} GitLab issues")
    if len(glab_identifiers) == 0:
        logger.info("No GitLab issues to process, skipping.")
        return None

    issues = [i.identifier for i in glab_identifiers]
    count_before = len(record.identification.identifiers)
    non_glab_identifiers = [i for i in record.identification.identifiers if i.identifier not in issues]
    record.identification.identifiers.clear()
    record.identification.identifiers.extend(non_glab_identifiers)
    count_after = len(record.identification.identifiers)
    logger.info(f"Removed {count_before - count_after} GitLab issue identifiers from record '{record.file_identifier}'")

    logger.info(f"Will set {len(issues)} GitLab issues admin metadata for Record '{record.file_identifier}'")
    return issues


def _get_access_permissions(logger: logging.Logger, record: Record) -> list[Permission]:
    """
    Get access permissions from record access constraints.

    Zap ⚡️'s restricted options don't map to access permissions used in admin metadata so aren't supported.
    """
    constraints = record.identification.constraints.filter(types=ConstraintTypeCode.ACCESS)
    logger.info(f"Record '{record.file_identifier}' has {len(constraints)} access constraints")
    if len(constraints) == 1 and constraints[0].restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
        logger.info(f"Record '{record.file_identifier}' has unrestricted access constraint, setting to OPEN ACCESS")
        return [OPEN_ACCESS]
    logger.info(f"Record '{record.file_identifier}' has no supported access constraints, no access permissions set")
    return []


def _create_admin_metadata(logger: logging.Logger, admin_keys: AdministrationKeys, record: Record) -> None:
    """
    Add administrative metadata to record.

    The input record is not modified.

    Zap ⚡️ authored records do not support administrative metadata natively however a mapping of discovery properties
    can be used:

    - admin.access_permissions -> identification.constraints[type=access]
    - admin.gitlab_issues -> identification.identifiers[namespace=gitlab.data.bas.ac.uk]

    Note: This assumes discovery metadata is trustworthy and requires a suitable chain of custody.
    Note: This method clobbers any existing admin metadata if already present in the record.
    """
    admin_meta = get_admin(keys=admin_keys, record=record)
    if admin_meta:
        logger.info(f"Existing administrative metadata loaded for record '{record.file_identifier}'")
    else:
        logger.info(f"No administrative metadata found for record '{record.file_identifier}', creating")
        admin_meta = Administration(id=record.file_identifier)

    gitlab_issues = _get_gitlab_issues(logger, record)
    if gitlab_issues:
        logger.info(f"GitLab issues in identifiers, setting in administrative record for '{record.file_identifier}'")
        admin_meta.gitlab_issues = gitlab_issues

    access_permissions = _get_access_permissions(logger, record)
    if len(access_permissions) > 0 and access_permissions != admin_meta.access_permissions:
        logger.info(f"Access permissions different to administrative record for '{record.file_identifier}', updating")
        admin_meta.access_permissions = access_permissions

    set_admin(keys=admin_keys, record=record, admin_meta=admin_meta)
    logger.info(f"Administrative metadata for record '{record.file_identifier}':")
    logger.info(admin_meta.dumps_json())
    logger.info(record.identification.supplemental_information)


def _process_admin_metadata(logger: logging.Logger, admin_keys: AdministrationKeys, records: list[Record]) -> None:
    """
    Add administrative metadata to records.

    Requires private signing key to author admin metadata instances.
    """
    for record in records:
        _create_admin_metadata(logger=logger, admin_keys=admin_keys, record=record)


def _process_distribution_descriptions(logger: logging.Logger, records: list[Record]) -> None:
    """Remove unnecessary online resource descriptions for simple distributions or align values."""
    format_descriptions = {
        "https://www.iana.org/assignments/media-types/application/geo+json": None,
        "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3": None,
        "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip": "Download information as a GeoPackage file compressed as a Zip archive.",
        "https://www.iana.org/assignments/media-types/image/jpeg": None,
        "https://www.iana.org/assignments/media-types/application/vnd.mapbox-vector-tile": None,
        "https://www.iana.org/assignments/media-types/application/pdf": None,
        "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo": "Download information as a PDF file with embedded georeferencing.",
        "https://www.iana.org/assignments/media-types/image/png": None,
        "https://metadata-resources.data.bas.ac.uk/media-types/application/shapefile+zip": "Download information as a Shapefile compressed as a Zip archive.",
    }
    for record in records:
        for distribution in record.distribution:
            format_href = None if distribution.format is None else distribution.format.href
            if (
                distribution.transfer_option.online_resource.description is not None
                and format_href in format_descriptions
            ):
                logger.info(
                    f"Updating distribution description for format '{distribution.format.format}' in Record '{record.file_identifier}'"
                )
                distribution.transfer_option.online_resource.description = format_descriptions[distribution.format.href]


def _process_records(
    logger: logging.Logger, records: list[Record], store: GitLabStore, admin_keys: AdministrationKeys
) -> list[Record]:
    """
    Process records as needed.

    `additional_records` returns any other records created or modified during processing that should be included.

    Where any of these records are modified, the date_stamp and other relevant properties are revised.
    """
    additional_records: list[Record] = []
    _process_distribution_descriptions(logger=logger, records=records)
    _process_admin_metadata(logger=logger, admin_keys=admin_keys, records=records)
    _process_magic_collections(logger=logger, records=records, additional_records=additional_records, store=store)
    _revise_records(logger=logger, records=[*records, *additional_records], store=store)
    return additional_records


def main() -> None:
    """Entrypoint."""
    env = Env()  # needed for loading private signing key for admin metadata
    env.read_env()
    config = Config()

    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )

    admin_keys = AdministrationKeys(
        encryption_private=config.ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE,
        signing_private=Jwk(env.json("X_ADMIN_METADATA_SIGNING_KEY_PUBLIC")),
        signing_public=config.ADMIN_METADATA_SIGNING_KEY_PUBLIC,
    )

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    store.populate()
    records = _parse_records(logger=logger, search_path=input_path)
    records.extend(_process_records(logger=logger, records=records, store=store, admin_keys=admin_keys))
    _dump_records(logger=logger, records=records, output_path=input_path)
    _clean_input_path(input_path=input_path)


if __name__ == "__main__":
    main()
