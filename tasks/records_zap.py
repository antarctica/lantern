import logging
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._record_utils import dump_records, init, parse_records
from tasks.records_upgrade_2026_02 import RecordUpgrade

from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS as OPEN_ACCESS_PERMISSION
from lantern.lib.metadata_library.models.record.presets.aggregations import make_bas_cat_collection_member
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_ADMINISTRATION_V1
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin
from lantern.lib.metadata_library.models.record.utils.kv import get_kv, set_kv
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import GitLabStore

# c68df2de-d40c-459f-ad5a-1f4d4ab5d8b9 - Assets Tracking Service (externally managed, not included here)
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
    "8b60e3b1-ccbf-48de-acaf-adf74382d6ea",  # BAS Geomatics Catalogue
]


def clean_input_path(input_record_paths: list[tuple[Record, Path]], processed_ids: list[str]) -> None:
    """Remove processed zap authored files."""
    for record_path in input_record_paths:
        if record_path[0].file_identifier in processed_ids:
            record_path[1].unlink()


def _revise_collection(time: datetime, collection: Record) -> None:
    """Indicate collection change via edition and other relevant properties."""
    if collection.identification.dates.revision is None:
        collection.identification.dates.revision = Date(date=time)
    collection.identification.dates.revision.date = time
    collection.identification.edition = str(int(collection.identification.edition) + 1)  # ty:ignore[invalid-argument-type]


def _revise_record(record: Record) -> None:
    """Indicate record change via relevant properties."""
    now = datetime.now(tz=UTC).replace(microsecond=0)
    record.metadata.date_stamp = now.date()
    if record.hierarchy_level == HierarchyLevelCode.COLLECTION:
        _revise_collection(time=now, collection=record)


def _revise_records(logger: logging.Logger, records: list[Record], store: GitLabStore) -> None:
    """Indicate record change via relevant properties if needed."""
    for record in records:
        if record.file_identifier is None:
            msg = "Record missing file identifier."
            logger.error(msg)
            raise ValueError(msg) from None
        try:
            existing_record = store.select_one(record.file_identifier)
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
    if record.file_identifier is None:
        msg = "Record must have a file identifier to create back-refs."
        logger.error(msg)
        raise ValueError(msg) from None
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
    collection_ids = set()
    for record in records:
        # only select parent collections referenced in records
        parent_collections = record.identification.aggregations.filter(
            namespace=CATALOGUE_NAMESPACE,
            associations=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiatives=AggregationInitiativeCode.COLLECTION,
        )
        record_collection_ids = [c.identifier.identifier for c in parent_collections]
        filtered_record_collection_ids = set(record_collection_ids).intersection(set(magic_collection_ids))
        collection_ids.update(filtered_record_collection_ids)
    collections = [store.select_one(record_id) for record_id in collection_ids]
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

    issue_urls = [i.href for i in glab_identifiers if i.href is not None]
    if len(issue_urls) != len(issues):
        msg = f"Record {record.file_identifier} has GitLab identifiers without href values."
        raise ValueError(msg) from None

    logger.info(f"Will set {len(issue_urls)} GitLab issues in admin metadata for Record '{record.file_identifier}'")
    return issue_urls


def _get_access_permissions(logger: logging.Logger, record: Record) -> tuple[list[Permission], list[Permission]]:
    """
    Get metadata and resource access permissions from record access constraints.

    Zap ⚡ doesn't support metadata access restrictions so hard-codes to OPEN ACCESS.

    Zap ⚡️'s restricted options don't map to access permissions used in admin metadata so aren't supported.
    """
    metadata_permissions = [OPEN_ACCESS_PERMISSION]
    logger.info(f"Setting metadata access constraints for record '{record.file_identifier}' to OPEN ACCESS.")

    resource_permissions = []
    constraints = record.identification.constraints.filter(types=ConstraintTypeCode.ACCESS)
    logger.info(f"Record '{record.file_identifier}' has {len(constraints)} access constraints")
    if len(constraints) == 1 and constraints[0].restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
        logger.info(
            f"Record '{record.file_identifier}' has unrestricted resource access constraint, setting to OPEN ACCESS."
        )
        resource_permissions = [OPEN_ACCESS_PERMISSION]
    logger.warning(
        f"Record '{record.file_identifier}' has unsupported access constraints, no resource access permissions set."
    )

    return metadata_permissions, resource_permissions


def _process_admin_metadata(logger: logging.Logger, admin_keys: AdministrationKeys, records: list[Record]) -> None:
    """
    Add administrative metadata to record.

    Zap ⚡️ authored records do not support administrative metadata natively however, a mapping of discovery properties
    can be used, providing the input is trusted with a suitable chain of custody:

    - admin.access_permissions -> identification.constraints[type=access]
    - admin.gitlab_issues -> identification.identifiers[namespace=gitlab.data.bas.ac.uk]

    Note: This method assumes admin metadata is already present in the record.
    Note: This method replaces any existing admin metadata already present in the record.
    """
    for record in records:
        admin_meta = get_admin(keys=admin_keys, record=record)
        if admin_meta is None:
            msg = "Record must have administration metadata."
            logger.error(msg)
            raise ValueError(msg) from None

        gitlab_issues = _get_gitlab_issues(logger, record)
        if gitlab_issues:
            logger.info(
                f"GitLab issues in identifiers, setting in administrative record for '{record.file_identifier}'"
            )
            admin_meta.gitlab_issues = gitlab_issues

        metadata_permissions, resource_permissions = _get_access_permissions(logger, record)
        if len(metadata_permissions) > 0 and metadata_permissions != admin_meta.metadata_permissions:
            logger.info(
                f"Metadata access permissions different to administrative record for '{record.file_identifier}', updating"
            )
            admin_meta.metadata_permissions = metadata_permissions
        if len(resource_permissions) > 0 and resource_permissions != admin_meta.resource_permissions:
            logger.info(
                f"Resource access permissions different to administrative record for '{record.file_identifier}', updating"
            )
            admin_meta.resource_permissions = resource_permissions

        set_admin(keys=admin_keys, record=record, admin_meta=admin_meta)
        logger.debug(f"Administrative metadata for record '{record.file_identifier}':")
        logger.debug(admin_meta.dumps_json())
        logger.debug(record.identification.supplemental_information)


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
                    f"Updating distribution description for format '{distribution.format.format}' "  # ty: ignore[possibly-missing-attribute]
                    f"in Record '{record.file_identifier}'"
                )
                distribution.transfer_option.online_resource.description = format_descriptions[distribution.format.href]  # ty: ignore[possibly-missing-attribute]


def _process_sheet_number(logger: logging.Logger, records: list[Record]) -> None:
    """Workaround mega-zap's now outdated broken schema workaround."""
    for record in records:
        kv = get_kv(record)
        sheet_number = kv.get("sheet_number", None)
        if not sheet_number:
            logger.info(f"Sheet number not found in KV for record [{record.file_identifier}], skipping.")
            continue

        pop_sheet_number = False
        logger.info(f"Sheet number found in KV for record [{record.file_identifier}].")
        if record.identification.series and record.identification.series.page:
            if record.identification.series.page == sheet_number:
                logger.info("Sheet number found in KV and descriptive series with matching value, removing from KV.")
                pop_sheet_number = True
            else:
                logger.warning(
                    "Sheet number found in KV and descriptive series with different values, resolve manually."
                )
        elif record.identification.series and not record.identification.series.page:
            logger.info("Sheet number found in KV but not in descriptive series, moving to descriptive series.")
            record.identification.series.page = sheet_number
            pop_sheet_number = True
        elif not record.identification.series:
            logger.warning("Sheet number found in KV but no descriptive series, resolve manually.")

        if pop_sheet_number:
            kv.pop("sheet_number", None)
            set_kv(kv, record, replace=True)
            logger.info("Sheet number removed from KV.")


def process_zap_records(
    logger: logging.Logger, records: list[Record], store: GitLabStore, admin_keys: AdministrationKeys
) -> list[Record]:
    """
    Process records as needed.

    `additional_records` returns any other records created or modified during processing that should be included.

    Where any of these records are modified, the date_stamp and other relevant properties are revised.
    """
    additional_records: list[Record] = []
    _process_sheet_number(logger=logger, records=records)
    _process_distribution_descriptions(logger=logger, records=records)
    _process_admin_metadata(logger=logger, admin_keys=admin_keys, records=records)
    _process_magic_collections(logger=logger, records=records, additional_records=additional_records, store=store)
    _revise_records(logger=logger, records=[*records, *additional_records], store=store)
    return additional_records


def parse_zap_records(
    logger: logging.Logger, admin_keys: AdministrationKeys, input_path: Path
) -> list[tuple[Record, Path]]:
    """
    Wrapper for records parsing logic to support MAGIC discovery profile change.

    The V2 discovery profile supports additional hierarchy levels the V1 schema rejects but which may be manually set
    in records after exporting from Zap ⚡, preventing their use. The catalogue will reject the V1 profile.

    This wrapper loads records without profile validation first, upgrades them to the V2 schema, adds minimal
    administration metadata, then calls the normal `parse_records()` logic.
    """
    record_paths = parse_records(
        logger=logger, search_path=input_path, validate_profiles=False, glob_pattern="zap-*.json"
    )
    for record, record_path in record_paths:
        original_record = deepcopy(record)
        # Add minimal admin metadata for future use
        if not record.file_identifier:
            msg = "Record must have a file identifier."
            raise ValueError(msg) from None
        admin = AdministrationMetadata(id=record.file_identifier)
        set_admin(keys=admin_keys, record=record, admin_meta=admin)
        add_conformance = True
        for dc in record.data_quality.domain_consistency:
            if dc.specification.href == MAGIC_ADMINISTRATION_V1.specification.href:
                add_conformance = False
                break
        if add_conformance:
            record.data_quality.domain_consistency.append(MAGIC_ADMINISTRATION_V1)

        up = RecordUpgrade(record=record, original_sha1=original_record.sha1)
        up.upgrade(logger=logger, keys=admin_keys)
        up.validate()
        logger.info(f"Saving upgraded record '{record.file_identifier}' to '{record_path}'")
        with record_path.open("w") as f:
            f.write(record.dumps_json(strip_admin=False))

    return parse_records(logger=logger, search_path=input_path, glob_pattern="zap-*.json")


def main() -> None:
    """Entrypoint."""
    logger, config, store, _s3 = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    record_paths = parse_zap_records(logger=logger, admin_keys=admin_keys, input_path=input_path)
    records = [record_path[0] for record_path in record_paths]
    records.extend(process_zap_records(logger=logger, records=records, store=store, admin_keys=admin_keys))
    dump_records(logger=logger, records=records, output_path=input_path)
    clean_input_path(input_record_paths=record_paths, processed_ids=[r.file_identifier for r in records])  # ty:ignore[invalid-argument-type]


if __name__ == "__main__":
    main()
