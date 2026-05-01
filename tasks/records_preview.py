# Directly output catalogue items for selected records

import json
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import init, parse_records, pick_local_records
from tests.conftest import _select_record

from lantern.config import Config
from lantern.exporters.local import LocalExporter
from lantern.lib.metadata_library.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.item_html import ItemCatalogueOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput
from lantern.site import Site, SiteJob
from lantern.stores.base import RecordsNotFoundError, StoreBase


class PlaceholderStore(StoreBase):
    """
    Store that reflects requested records with a placeholder.

    Intended for related record lookups when testing local, unpublished or otherwise detached records.
    """

    def __init__(self) -> None:
        """Initialise."""
        self.records = []

    def __len__(self) -> int:
        """Number of records."""
        return 0

    @property
    def frozen(self) -> bool:
        """Whether store can be modified/updated."""
        return True

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Return minimal records for selected records or raise a `RecordsNotFoundError` exception."""
        if not file_identifiers:
            raise RecordsNotFoundError(file_identifiers=set())
        return [self.select_one(fid) for fid in file_identifiers]

    def select_one(self, file_identifier: str) -> RecordRevision:
        """
        Return a minimal record for any identifier.

        Will never raise a `RecordNotFoundError` exception.
        """
        return _select_record(file_identifier)


def _get_cli_args() -> tuple[bool, Path, Path, Path | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Preview local records as locally exported catalogue items.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force import and export to defaults or set values, and record path to preview selected record to preview path.",
    )
    parser.add_argument(
        "--import-path",
        "-i",
        type=Path,
        default=Path("./import"),
        help="Directory to select records from. Will use default if omitted.",
    )
    parser.add_argument(
        "--export-path",
        "-e",
        type=Path,
        default=Path("./export"),
        help="Directory to save generated record outputs to. Will use default if omitted.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        help="Set specific record config file to preview. Will prompt for available files in import directory if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.import_path, args.export_path, args.path


def _get_args(logger: logging.Logger, cli_args: tuple[bool, Path, Path, Path | None]) -> tuple[Path, list[Record]]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_import_path, cli_export_path, cli_record_path = cli_args

    import_path = cli_import_path
    export_path = cli_export_path
    record_path = cli_record_path

    if not export_path.exists():
        export_path.mkdir(parents=True, exist_ok=True)

    if record_path:
        logger.info(f"Loading record from: '{record_path.resolve()}'")
        record = parse_records(
            logger=logger, glob_pattern=record_path.name, search_path=record_path.parent, validate_catalogue=True
        )[0][0]
        return export_path, [record]

    if not cli_force:
        import_path = Path(
            inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=import_path)
        )
        export_path = Path(
            inquirer.path("Export path", path_type=InquirerPath.DIRECTORY, exists=True, default=export_path)
        )

    logger.info(f"Loading records from: '{import_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=import_path)]
    selected_records = records  # if force option, preview all loaded records

    if not cli_force:
        selected_records = pick_local_records(logger=logger, records=records)

    return export_path, selected_records


def _export(logger: logging.Logger, config: Config, records: list[Record], output_path: Path) -> None:
    meta = ExportMeta.from_config(config=config, env="testing", trusted=True)
    site = Site(logger=logger, meta=meta, store=PlaceholderStore())
    exporter = LocalExporter(logger=logger, path=output_path)

    jobs = [SiteJob(action="content", output=cls) for cls in [SiteResourcesOutput, SitePagesOutput, SiteApiOutput]]
    # not SiteHealth (not front facing), not SiteIndex (won't include previewed records)

    for record in records:
        record = RecordRevision.loads({**json.loads(record.dumps_json(strip_admin=False)), "file_revision": "x"})
        jobs.append(SiteJob(action="content", output=ItemCatalogueOutput, record=record))
        # not Record ISO flavours (as boring)

    outputs = cast(list[SiteContent], site.execute(jobs))
    exporter.export(outputs)


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    cli_args = _get_cli_args()
    output_path, selected_records = _get_args(logger=logger, cli_args=cli_args)

    logger.info(f"Exporting previews of {len(selected_records)} record(s) to: '{output_path.resolve()}'")
    _export(logger=logger, config=config, records=selected_records, output_path=output_path)


if __name__ == "__main__":
    main()
