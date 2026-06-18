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
        """Whether the store is frozen."""
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

    def freeze(self) -> None:
        """Unsupported."""
        raise NotImplementedError


def _get_cli_args() -> tuple[bool, Path, Path, list[Path]]:
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
        action="append",
        help="Set specific record config file to preview. Can be repeated. Will prompt for files in import directory if omitted.",
    )
    args = parser.parse_args()
    if args.path is None:
        args.path = []
    return args.force, args.import_path, args.export_path, args.path


def _get_args(logger: logging.Logger, cli_args: tuple[bool, Path, Path, list[Path]]) -> tuple[Path, list[Record], str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_import_path, cli_export_path, cli_record_paths = cli_args

    import_path = cli_import_path
    export_path = cli_export_path
    record_paths: list[Path] = cli_record_paths
    records: list[Record] = []

    if cli_force and not record_paths:
        msg = "At least one record path must be set when using --force option for this task."
        raise RuntimeError(msg) from None
    if cli_force:
        for path in record_paths:
            logger.info(f"Loading record from: '{path.resolve()}'")
            r = parse_records(logger=logger, glob_pattern=path.name, search_path=path.parent, validate_catalogue=True)
            records.append(r[0][0])

        _paths_param = " ".join([f"--path {p.resolve()}" for p in record_paths])
        params = f"task preview-records --force --import-path {import_path.resolve()} --export-path {export_path.resolve()} {_paths_param}"
        return export_path, records, params

    import_path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=import_path))
    export_path = Path(inquirer.path("Export path", path_type=InquirerPath.DIRECTORY, exists=True, default=export_path))

    logger.info(f"Loading records from: '{import_path.resolve()}'")
    _record_paths = parse_records(logger=logger, search_path=import_path)
    records = pick_local_records(logger=logger, records=[rp[0] for rp in _record_paths])

    if not export_path.exists():
        logger.info(f"Creating missing export directory: '{export_path.resolve()}'")
        export_path.mkdir(parents=True, exist_ok=True)

    _records_lookup = {rp[0].file_identifier: rp[1].resolve() for rp in _record_paths}
    for r in records:
        try:
            record_paths.append(_records_lookup[r.file_identifier])
        except KeyError:
            msg = f"File for record '{r.file_identifier}' not found"
            raise FileNotFoundError(msg) from None
    _paths_param = " ".join([f"--path {p.resolve()}" for p in record_paths])
    params = f"task preview-records --force --import-path {import_path.resolve()} --export-path {export_path.resolve()} {_paths_param}"
    return export_path, records, params


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
    output_path, selected_records, params = _get_args(logger=logger, cli_args=cli_args)

    logger.info(f"Exporting previews of {len(selected_records)} record(s) to: '{output_path.resolve()}'")
    _export(logger=logger, config=config, records=selected_records, output_path=output_path)
    logger.info(f"Re-run as: '% {params}'")


if __name__ == "__main__":
    main()
