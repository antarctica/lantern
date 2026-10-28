# Update a record to include distribution options for an ArcGIS Online item

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
from tasks._shared import dump_records, init, parse_records, pick_local_record

from lantern.lib.arcgis.client import ArcGisClient

if TYPE_CHECKING:
    import logging

    from lantern.lib.magic_distribution.models.artefact import ArtefactArcGisService
    from lantern.lib.metadata_library.models.record.elements.distribution import Distribution
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
        logger.info("Loading record from: '%s'", record_path.resolve())
        record = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]

        params = (
            f"task esri-record --force --path {import_path.resolve()} --record {record_path.resolve()} --item {item}"
        )
        return import_path, record, item, params

    logger.info("Loading records from: '%s'", import_path.resolve())
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


def _make_esri_distributions(artefact: ArtefactArcGisService) -> list[Distribution]:
    """
    Generate distribution options for an ArcGIS artefact.

    Assumes artefact represents an ArcGIS Portal item, and will generate an Item and Service distribution option (if applicable).
    """
    distributions = [artefact.distribution_option]
    service_dist_opt = artefact.distribution_option_service
    if service_dist_opt:
        distributions.append(service_dist_opt)
    return distributions


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()
    arc_client = ArcGisClient(
        logger=logger, app_client_id=config.AGOL_CLIENT_ID, app_client_secret=config.AGOL_CLIENT_SECRET
    )

    cli_args = _get_cli_args()
    import_path, record, item_url, params = _get_args(logger=logger, cli_args=cli_args)

    artefact = arc_client.get_artefact(resource_id=record.file_identifier, item_ref=item_url)
    distribution_options = _make_esri_distributions(artefact)
    for option in distribution_options:
        record.distribution.ensure(option)
    dump_records(logger=logger, records=[record], output_path=import_path)

    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
