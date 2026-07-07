# Update record to include distribution options for an ArcGIS Online item

import hashlib
import logging
from argparse import ArgumentParser
from json import JSONDecodeError
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import inquirer
import requests
from authlib.integrations.requests_client.oauth2_session import OAuth2Session
from authlib.oauth2.rfc7523 import ClientSecretJWT
from requests import Response
from tasks._config import ExtraConfig
from tasks._shared import dump_records, init, parse_records, pick_local_record

from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.enums import ItemType as ArcGisItemType
from lantern.lib.arcgis.gis.enums import SharingLevel
from lantern.lib.metadata_library.models.record.elements.common import OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR
from lantern.lib.metadata_library.models.record.record import Record
from lantern.models.item.catalogue.enums import DistributionType


def _get_cli_args() -> tuple[bool, Path, Path | None, str | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Add distribution options to a record for an Esri ArcGIS item.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force path to local record and ArcGIS item to set.",
    )
    parser.add_argument(
        "--path",
        "-d",
        type=Path,
        default=Path("./import"),
        help="Directory to local records. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--record",
        "-r",
        type=Path,
        help="Path to local record config to update. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--item",
        "-i",
        type=str,
        help="ArcGIS item URL.",
    )
    args = parser.parse_args()
    return args.force, args.path, args.record, args.item


def _get_args(
    logger: logging.Logger, cli_args: tuple[bool, Path, Path | None, str | None]
) -> tuple[Path, Record, str, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_records_path, cli_record_path, cli_item = cli_args

    import_path = cli_records_path
    record_path = cli_record_path
    item = cli_item

    if cli_force and (not record_path or not item):
        msg = "Record path and item MUST be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if record_path and item:
        logger.info(f"Loading record from: '{record_path.resolve()}'")
        record = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]

        params = (
            f"task esri-record --force --path {import_path.resolve()} --record {record_path.resolve()} --item {item}"
        )
        return import_path, record, item, params

    logger.info(f"Loading records from: '{import_path.resolve()}'")
    _record_paths = parse_records(logger=logger, search_path=import_path)
    record = pick_local_record(logger=logger, records=[rp[0] for rp in _record_paths])
    item = inquirer.text(message="ArcGIS item URL", default=item)

    record_path = None
    for rp in _record_paths:
        if record.file_identifier == rp[0].file_identifier:
            record_path = rp[1]
            break
    if not record_path:
        msg = f"File for record '{record.file_identifier}' not found"
        raise FileNotFoundError(msg) from None
    params = f"task esri-record --force --path {import_path.resolve()} --record {record_path.resolve()} --item {item}"
    return import_path, record, item, params


def get_agol_token(config: ExtraConfig) -> str:
    """
    Generates an access token for an AGOL OAuth application per request (which is known to be inefficient).

    Sources:
    - https://developers.arcgis.com/documentation/security-and-authentication/reference/rest-authentication-operations/#access-token-from-client-credentials
    - https://developers.arcgis.com/documentation/security-and-authentication/reference/access-tokens/#how-to-use-an-access-token
    """
    token_endpoint = "https://www.arcgis.com/sharing/rest/oauth2/token"  # noqa: S105
    session = OAuth2Session(
        client_id=config.AGOL_CLIENT_ID,
        client_secret=config.AGOL_CLIENT_ID,
        token_endpoint_auth_method=ClientSecretJWT(token_endpoint),
    )
    # AGOL requires the client ID/secret as body parameters, not from basic auth which AuthLib does by default.
    token = session.fetch_token(
        token_endpoint, client_id=config.AGOL_CLIENT_ID, client_secret=config.AGOL_CLIENT_SECRET
    )
    return token["access_token"]


def get_agol_item_data(
    logger: logging.Logger, item_id: str, access_token: str | None = None, config: ExtraConfig | None = None
) -> dict:
    """
    Get ArcGIS Online item data for an item ID.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    """
    logger.info(f"Fetching ArcGIS item: {item_id}")

    if not access_token:
        if not config:
            msg = "Config required where access token is not provided"
            raise TypeError(msg) from None
        access_token = get_agol_token(config)

    req_data: Response = requests.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}",
        params={"f": "json", "token": access_token},
        timeout=10,
    )
    req_data.raise_for_status()
    data = req_data.json()
    if "error" in data:
        msg = f"Error fetching item {item_id} from AGOL: {data['error']['message']}"
        raise ValueError(msg)

    return data


def _get_agol_item_metadata(
    logger: logging.Logger, config: ExtraConfig, item_id: str, access_token: str | None = None
) -> str:
    """Get metadata for an ArcGIS Online item."""
    logger.info(f"Fetching ArcGIS metadata for item: {item_id}")

    if not access_token:
        access_token = get_agol_token(config)

    # AGOL requires the token as a query parameter, not a bearer type Authorization header.
    req: Response = requests.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}/info/metadata/metadata.xml",
        params={"token": access_token},
        timeout=10,
    )
    req.raise_for_status()
    return req.text


def _get_agol_item_thumbnail(logger: logging.Logger, item_id: str, access_token: str) -> tuple[str, str] | None:
    """
    Get thumbnail for an ArcGIS Online item.

    Returns thumbnail path (relative to item info) and a SHA1 hash of thumbnail content, or None if no thumbnail.
    """
    agol_data = get_agol_item_data(logger=logger, item_id=item_id, access_token=access_token)

    # get thumbnail path if set
    thumbnail: str | None = agol_data.get("thumbnail")
    if not thumbnail:
        return None

    # get hash of thumbnail content, requested as JSON for error checking
    req_thumb: Response = requests.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}/info/{thumbnail}",
        params={"f": "json", "token": access_token, "w": "400"},
        timeout=10,
    )

    # check for JSON encoded error, where successful response is binary
    req_thumb.raise_for_status()
    try:
        error = req_thumb.json()
        if "error" in error:
            msg = f"Error fetching item {item_id} thumbnail from AGOL: {error['error']['message']}"
            raise ValueError(msg)
    except JSONDecodeError:
        pass

    req_thumb_url = urlparse(req_thumb.url)
    thumbnail_sha1 = hashlib.sha1(req_thumb.content).hexdigest()  # noqa: S324
    thumbnail_url = f"{req_thumb_url.scheme}://{req_thumb_url.netloc}{req_thumb_url.path}?sha1={thumbnail_sha1}&w=400"
    return thumbnail, thumbnail_url


def get_agol_item(
    logger: logging.Logger, config: ExtraConfig, item_ref: str, access_token: str | None = None
) -> ArcGisItem:
    """
    Get an ArcGIS Online item from an item ID or URL.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    """
    item_id = item_ref
    if item_ref.startswith("http"):
        item_id = parse_qs(urlparse(item_ref).query).get("id", [item_ref])[0]
        if not item_id:
            msg = f"Unable to extract item ID from URL: {item_ref}"
            raise ValueError(msg)

    if not access_token:
        access_token = get_agol_token(config)

    agol_data = get_agol_item_data(logger=logger, config=config, item_id=item_id)
    agol_meta = _get_agol_item_metadata(logger=logger, config=config, item_id=item_id, access_token=access_token)
    agol_thumbnail = _get_agol_item_thumbnail(logger=logger, item_id=item_id, access_token=access_token)

    item = ArcGisItem.from_item_json(data=agol_data, metadata=agol_meta, thumbnail=agol_thumbnail)
    item.properties.metadata = _get_agol_item_metadata(logger=logger, config=config, item_id=item.id)
    return item


def _make_esri_distributions(arcgis_item: ArcGisItem) -> list[Distribution]:
    """Generate distribution options for an ArcGIS item."""
    item_format = {
        ArcGisItemType.FEATURE_SERVICE: Format(
            format="ArcGIS Feature Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        ),
        ArcGisItemType.OGCFEATURESERVER: Format(
            format="ArcGIS OGC Feature Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        ),
        ArcGisItemType.MAP_SERVICE: Format(
            format="ArcGIS Raster Tile Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        ),
        ArcGisItemType.VECTOR_TILE_SERVICE: Format(
            format="ArcGIS Vector Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
        ),
        ArcGisItemType.WEB_MAP: Format(
            format=DistributionType.ARCGIS_WEBMAP.value,
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+webmap",
        ),
    }
    item_description = {
        ArcGisItemType.FEATURE_SERVICE: "Access information as an ArcGIS feature layer.",
        ArcGisItemType.OGCFEATURESERVER: "Access information as an ArcGIS OGC feature layer.",
        ArcGisItemType.MAP_SERVICE: "Access information as an ArcGIS raster tile layer.",
        ArcGisItemType.VECTOR_TILE_SERVICE: "Access information as an ArcGIS vector tile layer.",
        ArcGisItemType.WEB_MAP: "Access information as an ArcGIS web map",
    }

    service_format = {
        ArcGisItemType.FEATURE_SERVICE: Format(
            format="ArcGIS Feature Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        ),
        ArcGisItemType.OGCFEATURESERVER: Format(
            format="OGC API Features Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        ),
        ArcGisItemType.MAP_SERVICE: Format(
            format="ArcGIS Raster Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        ),
        ArcGisItemType.VECTOR_TILE_SERVICE: Format(
            format="ArcGIS Vector Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
        ),
    }
    service_description = {
        ArcGisItemType.FEATURE_SERVICE: "Access information as an ArcGIS feature service.",
        ArcGisItemType.OGCFEATURESERVER: "Access information as an OGC API feature service.",
        ArcGisItemType.MAP_SERVICE: "Access information as an ArcGIS raster tile service.",
        ArcGisItemType.VECTOR_TILE_SERVICE: "Access information as an ArcGIS vector tile service.",
    }

    item_type = arcgis_item.properties.item_type
    item_host = "maps.arcgis.com" if arcgis_item.sharing_level == SharingLevel.EVERYONE else "bas.maps.arcgis.com"

    distributions = [
        Distribution(
            distributor=ESRI_DISTRIBUTOR,
            format=item_format[item_type],
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=f"https://{item_host}/home/item.html?id={arcgis_item.id}",
                    function=OnlineResourceFunctionCode.INFORMATION,
                    title="ArcGIS Online",
                    description=item_description[item_type],
                )
            ),
        )
    ]
    if item_type != item_type.WEB_MAP:
        distributions.append(
            Distribution(
                distributor=ESRI_DISTRIBUTOR,
                format=service_format[item_type],
                transfer_option=TransferOption(
                    online_resource=OnlineResource(
                        href=arcgis_item.url,
                        function=OnlineResourceFunctionCode.DOWNLOAD,
                        title="ArcGIS Online",
                        description=service_description[item_type],
                    )
                ),
            ),
        )
    return distributions


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    cli_args = _get_cli_args()
    import_path, record, item_url, params = _get_args(logger=logger, cli_args=cli_args)

    item = get_agol_item(logger=logger, config=config, item_ref=item_url)
    distribution_options = _make_esri_distributions(item)
    for option in distribution_options:
        record.distribution.ensure(option)
    dump_records(logger=logger, records=[record], output_path=import_path)

    logger.info(f"Re-run as: '% {params}'")


if __name__ == "__main__":
    main()
