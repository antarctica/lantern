from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from tasks._record_utils import confirm_source, dump_records, init, load_record

from lantern.lib.metadata_library.models.record.elements.common import OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR
from lantern.lib.metadata_library.models.record.record import Record
from lantern.models.item.catalogue.enums import DistributionType


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


def _get_agol_item(item_ref: str) -> dict:
    """
    Get an ArcGIS Online item from an item ID or URL.

    Limited to public items.
    """
    item_id = item_ref
    if item_ref.startswith("http"):
        item_id = parse_qs(urlparse(item_ref).query).get("id")
    req = requests.get(f"https://www.arcgis.com/sharing/rest/content/items/{item_id}", timeout=10, params={"f": "json"})
    req.raise_for_status()
    return req.json()


def _get_esri_type(item_json: dict) -> DistributionType:
    """
    Determine distribution type for an ArcGIS item.

    | Type (UI)                    | Type (JSON)           | Example Item                                                               |
    |------------------------------|-----------------------|----------------------------------------------------------------------------|
    | 'Feature layer (hosted)'     | 'Feature Service'     | https://maps.arcgis.com/home/item.html?id=54a2070f3d6943a29a635c0761e19301 |
    | 'OGC feature layer (hosted)' | 'OGCFeatureServer'    | https://maps.arcgis.com/home/item.html?id=67c77b72e46c467eb0a2ba041c04cc98 |
    | 'Tile Layer (Hosted)'        | 'Map Service'         | https://maps.arcgis.com/home/item.html?id=7af8a136533c4d70a9e8116591058694 |
    | 'Tile layer (hosted)'        | 'Vector Tile Service' | https://maps.arcgis.com/home/item.html?id=caa4df3010a549e38fabfca03a4daa87 |
    """
    mapping = {
        "Feature Service": DistributionType.ARCGIS_FEATURE_LAYER,
        "OGCFeatureServer": DistributionType.ARCGIS_OGC_FEATURE_LAYER,
        "Map Service": DistributionType.ARCGIS_RASTER_TILE_LAYER,
        "Vector Tile Service": DistributionType.ARCGIS_VECTOR_TILE_LAYER,
    }
    return mapping[item_json["type"]]


def _make_esri_distributions(item_json: dict) -> list[Distribution]:
    """Generate distribution options for an ArcGIS item."""
    item_type = _get_esri_type(item_json)

    item_format = {
        DistributionType.ARCGIS_FEATURE_LAYER: Format(
            format="ArcGIS Feature Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        ),
        DistributionType.ARCGIS_OGC_FEATURE_LAYER: Format(
            format="ArcGIS OGC Feature Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        ),
        DistributionType.ARCGIS_RASTER_TILE_LAYER: Format(
            format="ArcGIS Raster Tile Layer",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        ),
        DistributionType.ARCGIS_VECTOR_TILE_LAYER: Format(
            format="ArcGIS Vector Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
        ),
    }
    item_description = {
        DistributionType.ARCGIS_FEATURE_LAYER: "Access information as an ArcGIS feature layer.",
        DistributionType.ARCGIS_OGC_FEATURE_LAYER: "Access information as an ArcGIS OGC feature layer.",
        DistributionType.ARCGIS_RASTER_TILE_LAYER: "Access information as an ArcGIS raster tile layer.",
        DistributionType.ARCGIS_VECTOR_TILE_LAYER: "Access information as an ArcGIS vector tile layer.",
    }

    service_format = {
        DistributionType.ARCGIS_FEATURE_LAYER: Format(
            format="ArcGIS Feature Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        ),
        DistributionType.ARCGIS_OGC_FEATURE_LAYER: Format(
            format="OGC API Features Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        ),
        DistributionType.ARCGIS_RASTER_TILE_LAYER: Format(
            format="ArcGIS Raster Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        ),
        DistributionType.ARCGIS_VECTOR_TILE_LAYER: Format(
            format="ArcGIS Vector Tile Service",
            href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
        ),
    }
    service_description = {
        DistributionType.ARCGIS_FEATURE_LAYER: "Access information as an ArcGIS feature service.",
        DistributionType.ARCGIS_OGC_FEATURE_LAYER: "Access information as an OGC API feature service.",
        DistributionType.ARCGIS_RASTER_TILE_LAYER: "Access information as an ArcGIS raster tile service.",
        DistributionType.ARCGIS_VECTOR_TILE_LAYER: "Access information as an ArcGIS vector tile service.",
    }

    return [
        Distribution(
            distributor=ESRI_DISTRIBUTOR,
            format=item_format[item_type],
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=f"https://maps.arcgis.com/home/item.html?id={item_json['id']}",
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
                    href=item_json["url"],
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description=service_description[item_type],
                )
            ),
        ),
    ]


def _add_distribution_options(record: Record, options: list[Distribution]) -> None:
    """Add distribution options to a record if needed."""
    for option in options:
        if not any(record_option == option for record_option in record.distribution):
            record.distribution.append(option)


def main() -> None:
    """Entrypoint."""
    logger, _config, store, _s3 = init()
    output_path = Path("import")
    confirm_source(logger=logger, store=store, action="Selecting records from")
    args = _get_cli_args()

    record = load_record(logger=logger, ref=(args["id"], args["path"]), store=store)
    item = _get_agol_item(args["item"])
    distribution_options = _make_esri_distributions(item)
    _add_distribution_options(record, distribution_options)
    output_path = args["path"].parent if args["path"] else output_path
    dump_records(logger=logger, output_path=output_path, records=[record])


if __name__ == "__main__":
    main()
