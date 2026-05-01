# Update record to include distribution options for an ArcGIS Online item

import logging
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import inquirer
import requests
from authlib.integrations.requests_client.oauth2_session import OAuth2Session
from authlib.oauth2.rfc7523 import ClientSecretJWT
from tasks._config import ExtraConfig
from tasks._shared import dump_records, init, parse_records, pick_local_record

from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.enums import ItemType as ArcGisItemType
from lantern.lib.metadata_library.models.record.elements.common import OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR
from lantern.lib.metadata_library.models.record.record import Record


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


def _get_args(logger: logging.Logger, cli_args: tuple[bool, Path, Path | None, str | None]) -> tuple[Path, Record, str]:
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
        return import_path, record, item

    logger.info(f"Loading records from: '{import_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=import_path)]
    record = pick_local_record(logger=logger, records=records)
    item = inquirer.text(message="ArcGIS item URL", default=item)

    return import_path, record, item


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


def _get_agol_metadata(logger: logging.Logger, config: ExtraConfig, item_id: str) -> str:
    """Get metadata for an ArcGIS Online item."""
    logger.info(f"Fetching ArcGIS metadata for item: {item_id}")
    access_token = get_agol_token(config)
    # AGOL requires the token as a query parameter, not a bearer type Authorization header.
    req = requests.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}/info/metadata/metadata.xml",
        params={"token": access_token},
        timeout=10,
    )
    req.raise_for_status()

    return req.text


def get_agol_item(logger: logging.Logger, config: ExtraConfig, item_ref: str) -> ArcGisItem:
    """
    Get an ArcGIS Online item from an item ID or URL.

    AGOL requires the token as a query parameter, not a bearer type Authorization header.
    """
    item_id = item_ref
    if item_ref.startswith("http"):
        item_id = parse_qs(urlparse(item_ref).query).get("id")

    logger.info(f"Fetching ArcGIS item: {item_id}")
    access_token = get_agol_token(config)

    req_data = requests.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}",
        params={"f": "json", "token": access_token},
        timeout=10,
    )
    req_data.raise_for_status()
    data = req_data.json()
    if "error" in data:
        msg = f"Error fetching item {item_id} from AGOL: {data['error']['message']}"
        raise ValueError(msg)

    req_metadata = requests.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}/info/metadata/metadata.xml",
        params={"token": access_token},
        timeout=10,
    )
    req_metadata.raise_for_status()
    metadata = req_metadata.text

    item = ArcGisItem.from_item_json(data=data, metadata=metadata)
    item.properties.metadata = _get_agol_metadata(logger=logger, config=config, item_id=item.id)
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
    }
    item_description = {
        ArcGisItemType.FEATURE_SERVICE: "Access information as an ArcGIS feature layer.",
        ArcGisItemType.OGCFEATURESERVER: "Access information as an ArcGIS OGC feature layer.",
        ArcGisItemType.MAP_SERVICE: "Access information as an ArcGIS raster tile layer.",
        ArcGisItemType.VECTOR_TILE_SERVICE: "Access information as an ArcGIS vector tile layer.",
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
    return [
        Distribution(
            distributor=ESRI_DISTRIBUTOR,
            format=item_format[item_type],
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=f"https://maps.arcgis.com/home/item.html?id={arcgis_item.id}",
                    function=OnlineResourceFunctionCode.INFORMATION,
                    title="ArcGIS Online",
                    description=item_description[item_type],
                )
            ),
        ),
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
    ]


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    cli_args = _get_cli_args()
    import_path, record, item_url = _get_args(logger=logger, cli_args=cli_args)

    item = get_agol_item(logger=logger, config=config, item_ref=item_url)
    distribution_options = _make_esri_distributions(item)
    for option in distribution_options:
        record.distribution.ensure(option)
    dump_records(logger=logger, records=[record], output_path=import_path)


if __name__ == "__main__":
    main()
