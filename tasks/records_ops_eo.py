import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._record_utils import _parse_configs, dump_records, init

from lantern.lib.metadata_library.models.record.elements.common import (
    Constraint,
    Constraints,
    Contact,
    ContactIdentity,
    Identifier,
    Identifiers,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, TransferOption
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS as OPEN_ACCESS_PERMISSION
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_ADMINISTRATION_V1, MAGIC_DISCOVERY_V2
from lantern.lib.metadata_library.models.record.presets.constraints import CC_BY_ND_V4, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record as RawRecord
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.record.record import Record

# Equivalent to records_zap task for Ops related EO records.


def load_stac(iso_path: Path) -> dict:
    """Load accompanying STAC metadata if it exists for additional context."""
    stac_path = iso_path.with_name(iso_path.stem.replace("_magic", "_stac") + iso_path.suffix)
    try:
        with stac_path.open() as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load(logger: logging.Logger, admin_keys: AdministrationKeys, search_path: Path) -> dict[Path, Record]:
    """
    Load records produced by the Ops EO notebook.

    Performs various transforms to fix and enhance records.

    Returned as a dict of {ConfigPath: Record} to allow targeted clean-up later.
    """
    logger.info(f"Loading notebook generated record configs from: '{search_path.resolve()}'")
    raw_objects = list(_parse_configs(search_path, glob_pattern="*_magic.json"))
    logger.info(f"Loaded {len(raw_objects)} record configs from '{search_path.resolve()}'.")

    # fix datestamp to allow loading as a record
    for i, obj_path in enumerate(raw_objects):
        obj, _path = obj_path
        raw_ds = datetime.fromisoformat(obj["metadata"]["date_stamp"])
        ds = raw_ds.date().isoformat()
        obj["metadata"]["date_stamp"] = ds
        logger.debug(f"Datestamp '{raw_ds}' changed to '{ds}' for record config in '{_path.name}'.")
        raw_objects[i] = (obj, _path)

    raw_record_paths: list[tuple[RawRecord, Path]] = [(RawRecord.loads(config), path) for config, path in raw_objects]
    for raw_record_path in raw_record_paths:
        raw_record_path[0].validate()
    logger.info(f"Loaded {len(raw_record_paths)} valid raw records from '{search_path.resolve()}'.")

    for i, raw_record_path in enumerate(raw_record_paths):
        raw_record, _path = raw_record_path

        # update file_identifier
        file_identifier = str(uuid4())
        logger.info(f"File identifier for '{raw_record.file_identifier}' changed to '{file_identifier}'.")
        raw_record.file_identifier = file_identifier

        # update identifiers
        image_id = raw_record.identification.identifiers[0].identifier
        raw_record.identification.identifiers = Identifiers(
            [
                make_bas_cat(item_id=raw_record.file_identifier),
                Identifier(identifier=image_id, namespace="MAGIC_EO_IMAGE_ID"),
            ]
        )
        logger.debug(f"Identifiers set for '{raw_record.file_identifier}'.")

        # set rights holder
        raw_record.identification.contacts.append(
            Contact(organisation=ContactIdentity(name="European Commission"), role={ContactRoleCode.RIGHTS_HOLDER})
        )
        logger.debug(f"Rights holder contact set for '{raw_record.file_identifier}'.")

        # update constraints
        raw_record.metadata.constraints = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.RESTRICTED,
                    statement="Closed Access",
                ),
                CC_BY_ND_V4,
            ]
        )
        raw_record.identification.constraints = Constraints(
            [
                OPEN_ACCESS,
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    href="https://cds.climate.copernicus.eu/licences/ec-sentinel",
                    statement="This information is licensed under the Copernicus Sentinel data licence (rev. 1).",
                ),
            ]
        )
        logger.debug(f"Constraints set for '{raw_record.file_identifier}'.")

        # set admin metadata
        admin_meta = AdministrationMetadata(
            id=raw_record.file_identifier,
            metadata_permissions=[
                Permission(
                    directory="~nerc",
                    group="53ad5a87-cd3a-4054-b91b-88f108d8ffda",
                    comment="Location of image is restricted to group members only..",
                )
            ],
            resource_permissions=[OPEN_ACCESS_PERMISSION],
        )
        set_admin(keys=admin_keys, record=raw_record, admin_meta=admin_meta)
        logger.debug(f"Admin meta set for '{raw_record.file_identifier}'.")

        # set profile conformance
        raw_record.data_quality.domain_consistency = [MAGIC_DISCOVERY_V2, MAGIC_ADMINISTRATION_V1]
        logger.debug(f"Profile conformance set for '{raw_record.file_identifier}'.")

        # set distribution URL from STAC if available
        stac = load_stac(_path)
        if "assets" in stac and "image" in stac["assets"] and "href" in stac["assets"]["image"]:
            href = "sftp://san.nerc-bas.ac.uk" + stac["assets"]["image"]["href"].replace("/mnt/c/DATA/", "/data/")
            raw_record.distribution.append(
                Distribution(
                    distributor=make_magic_role({ContactRoleCode.DISTRIBUTOR}),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            )
            logger.debug(f"SAN distribution added based on STAC metadata for '{raw_record.file_identifier}'.")

        # update record
        raw_record_paths[i] = (raw_record, _path)

    records: dict[Path, Record] = {
        path: Record.loads(json.loads(record.dumps_json(strip_admin=False))) for record, path in raw_record_paths
    }
    for record in records.values():
        record.validate()
    logger.info(f"Loaded {len(records)} valid catalogue records from '{search_path.resolve()}'.")
    return records


def list_(record_paths: dict[Path, Record]) -> None:
    """List loaded records and source files."""
    print("Loaded records:\n")
    for config_path, record in record_paths.items():
        print(
            f"- {record.file_identifier} ({record.identification.identifiers[1].identifier}) from {config_path.resolve()}"
        )
    print("")


def clean(logger: logging.Logger, record_paths: dict[Path, Record]) -> None:
    """Clean up input path."""
    targets = [t for r in record_paths for t in r.parent.glob(f"{r.stem.replace('_magic', '_*')}.json")]
    for target in targets:
        target.unlink()
        logger.info(f"Removed processed file: '{target.resolve()}'.")


def main() -> None:
    """Entrypoint."""
    logger, config, _store, _s3 = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW
    input_path = Path("./import")
    output_path = Path("./import")

    records = load(logger=logger, admin_keys=admin_keys, search_path=input_path)
    list_(record_paths=records)
    dump_records(logger=logger, records=list(records.values()), output_path=output_path)
    clean(logger=logger, record_paths=records)


if __name__ == "__main__":
    main()
