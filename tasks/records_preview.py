# Directly output catalogue items for selected records

import json
import logging
import sys
from pathlib import Path

from tasks._shared import init, parse_records, pick_records
from tests.conftest import _select_record

from lantern.config import Config
from lantern.exporters.local import LocalExporter
from lantern.lib.metadata_library.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.outputs.item_html import ItemCatalogueOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput
from lantern.site import Site, SiteJob
from lantern.stores.base import RecordsNotFoundError, Store


class MirrorStore(Store):
    """
    Store that reflects requested records.

    Returns a placeholder for any related record lookups when testing local, unpublished or otherwise detached records.
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


def _get_args(logger: logging.Logger, records: list[Record]) -> list[Record]:
    """
    Get user input.

    Returns a list of records to preview.
    """
    return pick_records(logger=logger, records=records)


def _export(logger: logging.Logger, config: Config, records: list[Record], output_path: Path) -> None:
    meta = ExportMeta.from_config_store(config=config, store=None, trusted=True)
    site = Site(logger=logger, meta=meta, store=MirrorStore())
    exporter = LocalExporter(logger=logger, path=output_path)

    jobs = [SiteJob(output=cls) for cls in [SiteResourcesOutput, SitePagesOutput, SiteApiOutput]]
    # not SiteHealth (not front facing), not SiteIndex (won't include previewed records)
    for record in records:
        record = RecordRevision.loads({**json.loads(record.dumps_json(strip_admin=False)), "file_revision": "x"})
        jobs.append(SiteJob(output=ItemCatalogueOutput, record=record))

    outputs = site.execute(jobs)
    exporter.export(outputs)


def main() -> None:
    """Entrypoint."""
    logger, config, _store = init()
    input_path = Path("./import")
    output_path = Path("./export")

    logger.info(f"Loading records from: '{input_path.resolve()}'")
    records = [record_path[0] for record_path in parse_records(logger=logger, search_path=input_path)]
    selected_records = _get_args(logger=logger, records=records)
    if not selected_records:
        logger.info("No records selected, aborting.")
        sys.exit(0)

    logger.info(f"Loading {len(selected_records)} records to: '{output_path.resolve()}'")
    _export(logger=logger, config=config, records=selected_records, output_path=output_path)


if __name__ == "__main__":
    main()
