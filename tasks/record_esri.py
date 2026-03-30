# Update record to include distribution options for an ArcGIS Online item

import logging
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from authlib.integrations.requests_client.oauth2_session import OAuth2Session
from authlib.oauth2.rfc7523 import ClientSecretJWT
from tasks._config import ExtraConfig
from tasks._record_utils import confirm_source, dump_records, init, load_record

from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.enums import ItemType as ArcGisItemType
from lantern.lib.metadata_library.models.record.elements.common import OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR


def _get_cli_args() -> dict:
    """
    Get command line arguments.

    Supports two modes:
    - Positional: 'task esri-record record_ref item_id'
    - Named:
      - 'task esri-record --id record_id --item item_id'
      - 'task esri-record --path /path/to/config --item item_id'

    Mixing positional and named arguments is not supported and will raise an error.
    """
    parser = ArgumentParser(description="Add distribution options to a record for an Esri ArcGIS item.")
    parser.add_argument(
        "ref",
        nargs="?",
        type=str,
        help="Optional positional reference: path to a record config file or an ID.",
    )
    parser.add_argument(
        "item_pos",
        nargs="?",
        type=str,
        help="Optional positional ArcGIS Online item ID or item URL.",
    )
    parser.add_argument(
        "--id",
        type=str,
        help="Record identifier (file identifier, URL, or file name). Will interactively prompt if missing.",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to a record configuration file, as an alternative to a record identifier.",
    )
    parser.add_argument(
        "--item",
        type=str,
        help="ArcGIS Online item ID or item URL.",
    )
    args = parser.parse_args()

    # Detect usage mode
    using_positional = args.ref is not None or args.item_pos is not None
    using_named = args.id is not None or args.path is not None or args.item is not None

    if using_positional and using_named:
        msg = "Cannot mix positional and named arguments."
        raise ValueError(msg) from None

    path = None
    record_id = None
    # noinspection PyUnusedLocal
    item = None

    if using_named:
        if args.path is not None:
            path_candidate = Path(args.path)
            if not path_candidate.is_file():
                msg = f"Path to record config file specified but not found at: '{path_candidate.resolve()}'"
                raise FileNotFoundError(msg)
            path = path_candidate
        if args.id is not None:
            record_id = args.id
        item = args.item
    else:
        # Positional mode
        if args.ref is not None:
            ref_candidate = Path(args.ref)
            if ref_candidate.is_file():
                path = ref_candidate
            else:
                record_id = args.ref
        item = args.item_pos

    if record_id is None and path is None:
        msg = "A path to a record, or a record identifier, is required."
        raise ValueError(msg) from None

    return {"id": record_id, "path": path, "item": item}


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
    logger, config, store = init()
    output_path = Path("import")
    confirm_source(logger=logger, store=store, action="Selecting records from")
    args = _get_cli_args()

    record = load_record(logger=logger, ref=(args["id"], args["path"]), store=store)
    item = get_agol_item(logger=logger, config=config, item_ref=args["item"])

    distribution_options = _make_esri_distributions(item)
    for option in distribution_options:
        record.distribution.ensure(option)

    output_path = args["path"].parent if args["path"] else output_path
    dump_records(logger=logger, output_path=output_path, records=[record])


if __name__ == "__main__":
    main()
