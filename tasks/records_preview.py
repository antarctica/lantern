import json
import logging
import sys
from pathlib import Path

import inquirer
from boto3 import client as S3Client  # noqa: N812
from moto import mock_aws
from tasks._record_utils import init, parse_records
from tests.conftest import _select_record

from lantern.config import Config
from lantern.exporters.html import HtmlExporter
from lantern.exporters.site import SiteResourcesExporter
from lantern.lib.metadata_library.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta


def _get_args(logger: logging.Logger, records: list[Record]) -> list[Record]:
    """
    Get user input.

    Returns a list of records to preview.
    """
    choices = {
        f"{r.file_identifier} ('{r.identification.title}' {r.hierarchy_level.value})": r.file_identifier
        for r in records
    }
    logger.debug(f"Choices: {list(choices.keys())}")

    answers = inquirer.prompt([inquirer.Checkbox("selections", message="Records", choices=list(choices.keys()))])

    records_ = {r.file_identifier: r for r in records}
    selected_fids = [choices[k] for k in answers["selections"]]
    logger.info(f"Selected records: {selected_fids}")
    return [records_[fid] for fid in selected_fids]


def _export(logger: logging.Logger, config: Config, records: list[Record], output_path: Path) -> None:
    meta = ExportMeta.from_config_store(config=config, store=None, trusted=True)
    with mock_aws():
        s3 = S3Client("s3", aws_access_key_id="x", aws_secret_access_key="x", region_name="eu-west-1")  # noqa: S106

    site_resources = SiteResourcesExporter(logger=logger, meta=meta, s3=s3)
    site_resources.export()

    for record in records:
        record = RecordRevision.loads({**json.loads(record.dumps_json(strip_admin=False)), "file_revision": "x"})
        exporter = HtmlExporter(logger=logger, meta=meta, s3=s3, record=record, select_record=_select_record)  # ty:ignore[invalid-argument-type]
        record_path = output_path / "items" / record.file_identifier / "index.html"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        with record_path.open("w") as f:
            f.write(exporter.dumps())
        logger.info(f"Exported record: '{record_path.resolve()}'")


def main() -> None:
    """Entrypoint."""
    logger, config, _store, _s3 = init()
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
