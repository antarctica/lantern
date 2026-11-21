# Update an ArcGIS Online item based on a record

from __future__ import annotations

import json
from argparse import ArgumentParser
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
from tasks._shared import confirm, get_record, init

from lantern.lib.magic_distribution.arcgis.client import ArcGisClient
from lantern.lib.magic_distribution.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.magic_distribution.arcgis.gis.dataclasses import ItemProperties as ArcGisItemProperties
from lantern.lib.magic_distribution.arcgis.gis.enums import SharingLevel as ArcGisSharingLevel
from lantern.models.item.arcgis.item import ItemArcGis
from lantern.models.record.record import Record

if TYPE_CHECKING:
    import logging

    from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

    from lantern.catalogues.bas import BasCatalogue


def _get_cli_args() -> dict:
    """Get command line arguments."""
    parser = ArgumentParser(description="Sync record details to an Esri item.")
    parser.add_argument(
        "--source",
        type=str,
        help="Source catalogue record ID (file identifier, URL, or file name).",
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Target AGOL item ID.",
    )
    if not parser.parse_args().source:
        msg = "Source record identifier required."
        raise ValueError(msg) from None
    if not parser.parse_args().target:
        msg = "Target item identifier required."
        raise ValueError(msg) from None
    return {"source_id": parser.parse_args().source, "target_id": parser.parse_args().target}


def _create_source_arcgis_item(
    source_record: Record, admin_keys: AdministrationKeys, target_item: ArcGisItem
) -> ArcGisItem:
    """
    Create a ArcGIS item from a source record and target ArcGIS item.

    Returns a new prospective ArcGIS Item with properties based on the source record.

    This can be compared against the target item to determine which (if any) properties require updating.

    Uses a ItemArcGis instance to construct a ArcGIS Item (i.e. following the ArcGIS information model), which requires
    a source Record and an ArcGIS Item (for properties not held in the ISO model used by the Record).

    In this case we are updating an existing Arc Item, and so can use this as the input item. Most item values will not
    change (as they have no equivalent in the source record). Values that may change are:
    - `properties.title` (based on `identification.title` in the record)
    - `sharing_level` (based on admin metadata `access_permissions` in the record)
    """
    source_item = ArcGisItem(
        id=target_item.id,
        owner=target_item.owner,
        org_id=target_item.org_id,
        url=target_item.url,
        properties=ArcGisItemProperties(
            title=target_item.properties.title, item_type=target_item.properties.item_type, metadata="x"
        ),
        sharing_level=target_item.sharing_level,
    )
    return ItemArcGis(record=source_record, arcgis_item=source_item, admin_meta_keys=admin_keys).item


def _dump_arcgis_item(logger: logging.Logger, output_path: Path, item: ArcGisItem) -> None:
    """Dump raw ArcGIS item metadata to a JSON file."""
    suffix = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z").replace(":", "-")
    item_path = output_path / f"{item.id}_{suffix}.json"
    item_path.parent.mkdir(parents=True, exist_ok=True)
    with item_path.open("w") as f:
        json.dump(item.raw_item, f, indent=2)
    logger.info("AGOL item %s dumped to %s", item.id, item_path.resolve())


def _sync_item(
    logger: logging.Logger,
    cat: BasCatalogue,
    arc: ArcGisClient,
    admin_keys: AdministrationKeys,
    item_id: str,
    file_identifier: str,
    branch: str | None = None,
) -> None:
    """Apply a source catalogue record to a target ArcGIS item."""
    source_record = get_record(logger=logger, cat=cat, reference=file_identifier, branch=branch)
    target_item = arc.get_item(item_id)
    source_item = _create_source_arcgis_item(
        source_record=Record.loads(source_record.dumps(strip_admin=False)),
        admin_keys=admin_keys,
        target_item=target_item,
    )
    original_target = deepcopy(target_item)

    if source_item.sharing_level != target_item.sharing_level:
        confirm(logger, f"Update sharing level to {source_item.sharing_level.name}?")

    diff = arc.diff_items(item=source_item, other=target_item)
    if not diff:
        logger.info("Target item %s == %s, skipping.", target_item.id, source_record.file_identifier)
        return
    logger.info("Target item {target_item.id} != {source_record.file_identifier}, updating...")
    logger.info(list(diff.keys()))

    changed = arc.sync_item(source=source_item, target=target_item, allow_sharing_change=True)
    if changed:
        _dump_arcgis_item(logger=logger, output_path=Path("agol-item-backups"), item=original_target)

    if target_item.sharing_level != ArcGisSharingLevel.EVERYONE:
        return
    if not inquirer.confirm(message="Target is public, reassign to publishing user?", default=True):
        return
    arc.reassign_item(owner_id=target_item.owner, item_id=target_item.id, new_owner_id="BritishAntarcticSurvey")


def main() -> None:
    """Entrypoint."""
    logger, config, catalogue = init()
    args = _get_cli_args()
    arc_client = ArcGisClient(
        logger=logger, app_client_id=config.AGOL_CLIENT_ID, app_client_secret=config.AGOL_CLIENT_SECRET
    )

    _sync_item(
        logger=logger,
        cat=catalogue,
        arc=arc_client,
        admin_keys=config.ADMIN_METADATA_KEYS,
        item_id=args["target_id"],
        file_identifier=args["source_id"],
        branch="changeset/MAGIC/data-management.84",
    )

    params = f"task esri-item --source {args['source_id']} --target {args['target_id']}"
    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
