import json
import logging
from argparse import ArgumentParser
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import requests
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from lxml.html import HTMLParser
from lxml.html import fragment_fromstring as html_fromstring
from lxml.html import tostring as html_tostring
from tasks._config import ExtraConfig
from tasks._record_utils import get_record, init
from tasks.record_esri import get_agol_item, get_agol_token

from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.dataclasses import ItemProperties as ArcGisItemProperties
from lantern.lib.arcgis.gis.enums import SharingLevel
from lantern.models.item.arcgis.item import ItemArcGis
from lantern.models.record.record import Record


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
    logger.info(f"AGOL item {item.id} dumped to {item_path.resolve()}")


def _snake_to_camel_case(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _normalise_arcgis_html(html: str) -> str:
    """
    Normalise HTML string between a catalogue record and an ArcGIS item.

    Converts between HTML generated:
    - from Markdown in the catalogue item
    - after having been submitted and processed by Arc

    Accounts for:
    - differences in syntax (`<a href='x'>` vs `<a href="x">`)
    - accounting for `rel="nofollow ugc"` being added to anchor elements
    """
    element = html_fromstring(html, create_parent=True, parser=HTMLParser())
    # add `rel="nofollow ugc"` to any anchor elements
    for a in element.iter("a"):
        relations = {t for t in a.get("rel", "").split() if t}
        relations.update({"nofollow", "ugc"})
        a.set("rel", " ".join(sorted(relations)))
    return html_tostring(doc=element, encoding="unicode")


def _diff_arcgis_items(source_item: ArcGisItem, target_item: ArcGisItem) -> dict:
    """
    Compare a source and target ArcGIS items and return a dict of any differences that need applying.

    In this case it's only the sharing level (access) and these item.properties that are relevant:
    - title
    - snippet
    - description
    - access_information (accessInformation) [attribution]
    - license_info (licenseInfo)
    - metadata
    """
    diff = {}
    if source_item.sharing_level != target_item.sharing_level:
        diff["sharing_level"] = source_item.sharing_level
    if source_item.properties.metadata not in target_item.properties.metadata:
        print(f"<x>{source_item.properties.metadata}</x>")
        print(target_item.properties.metadata)
        diff["metadata"] = source_item.properties.metadata
    for prop in ["snippet", "access_information"]:
        src_val = getattr(source_item.properties, prop, None)
        tgt_val = getattr(target_item.properties, prop, None)
        if src_val == tgt_val or src_val is None:
            continue
        diff[_snake_to_camel_case(prop)] = src_val
    for html_prop in ["snippet", "description", "license_info"]:
        src_val = _normalise_arcgis_html(getattr(source_item.properties, html_prop, ""))
        tgt_val = _normalise_arcgis_html(getattr(target_item.properties, html_prop, ""))
        if src_val == tgt_val or src_val == "":
            continue
        diff[_snake_to_camel_case(html_prop)] = src_val
    return diff


def _update_agol_metadata(logger: logging.Logger, base_url: str, token: str, item: ArcGisItem, metadata: str) -> None:
    """
    Update metadata for an ArcGIS Online item.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    Source: https://developers.arcgis.com/rest/users-groups-and-items/update-info/
    """
    logger.info(f"Updating metadata for item: {item.id}")
    logger.debug(metadata)
    req = requests.post(
        url=f"{base_url}/updateInfo",
        params={"folderName": "metadata", "token": token, "f": "json"},
        files={"file": ("metadata.xml", BytesIO(metadata.encode("utf-8")), "application/xml")},
        timeout=10,
    )
    req.raise_for_status()
    data = req.json()
    if not data.get("success"):
        msg = f"Error updating metadata for item {item.id} in AGOL: {data}"
        raise ValueError(msg)


def _update_agol_sharing(
    logger: logging.Logger, base_url: str, token: str, item: ArcGisItem, sharing_level: SharingLevel
) -> None:
    """
    Update sharing for an ArcGIS Online item.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    Source: https://developers.arcgis.com/rest/users-groups-and-items/share-item-as-item-owner/
    """
    logger.info(f"Updating sharing for item: {item.id}")
    sharing = {"everyone": False, "org": False}
    if sharing_level == SharingLevel.ORG:
        sharing["org"] = True
    elif sharing_level == SharingLevel.EVERYONE:
        sharing["everyone"] = True
        sharing["org"] = True
    files_sharing: dict[str, tuple] = {k: (None, v) for k, v in sharing.items()}
    logger.debug(sharing)

    # noinspection PyTypeChecker
    req = requests.post(
        url=f"{base_url}/share",
        params={"token": token, "f": "json"},
        files=files_sharing,
        timeout=10,
    )
    req.raise_for_status()
    data = req.json()
    if "error" in data:
        msg = f"Error updating sharing for item {item.id} in AGOL: {data['error']['message']}"
        raise ValueError(msg)


def _update_agol_properties(
    logger: logging.Logger, base_url: str, token: str, item: ArcGisItem, properties: dict
) -> None:
    """
    Update properties for an ArcGIS Online item.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    Source: https://developers.arcgis.com/rest/users-groups-and-items/update-item/
    """
    logger.info(f"Updating item: {item.id}")
    files_update: dict[str, tuple] = {k: (None, v) for k, v in properties.items()}
    files_update["metadataEditable"] = (None, "false")
    logger.debug(files_update)
    # noinspection PyTypeChecker
    req = requests.post(
        url=f"{base_url}/update",
        params={"f": "json", "token": token},
        files=files_update,
        timeout=10,
    )
    req.raise_for_status()
    data = req.json()
    if "error" in data:
        msg = f"Error updating item {item.id} in AGOL: {data['error']['message']}"
        raise ValueError(msg)


def _update_agol_item(logger: logging.Logger, config: ExtraConfig, item: ArcGisItem, properties: dict) -> None:
    """
    Update properties in an ArcGIS Online item.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    Source: https://developers.arcgis.com/rest/users-groups-and-items/update-item/
    """
    base_url = f"https://www.arcgis.com/sharing/rest/content/users/{item.owner}/items/{item.id}"
    access_token = get_agol_token(config=config)

    metadata = properties.pop("metadata", None)
    if isinstance(metadata, str):
        _update_agol_metadata(logger=logger, base_url=base_url, token=access_token, item=item, metadata=metadata)

    sharing = properties.pop("sharing", None)
    if isinstance(sharing, SharingLevel):
        _update_agol_sharing(logger=logger, base_url=base_url, token=access_token, item=item, sharing_level=sharing)

    _update_agol_properties(logger=logger, base_url=base_url, token=access_token, item=item, properties=properties)


def main() -> None:
    """Entrypoint."""
    logger, config, store, _s3 = init()
    args = _get_cli_args()

    source_record = get_record(logger=logger, store=store, identifier=args["source_id"])
    target_item = get_agol_item(logger=logger, config=config, item_ref=args["target_id"])
    source_item = _create_source_arcgis_item(
        source_record=Record.loads(source_record.dumps(strip_admin=False)),
        admin_keys=config.ADMIN_METADATA_KEYS,
        target_item=target_item,
    )

    diff = _diff_arcgis_items(source_item=source_item, target_item=target_item)
    if not diff:
        logger.info(f"Target item {target_item.id} == {source_record.file_identifier}, skipping.")
        return
    logger.info("Target item {target_item.id} != {source_record.file_identifier}, updating...")
    logger.info(diff)
    _dump_arcgis_item(logger=logger, output_path=Path("agol-item-backups"), item=target_item)
    _update_agol_item(logger=logger, config=config, item=target_item, properties=diff)


if __name__ == "__main__":
    main()
