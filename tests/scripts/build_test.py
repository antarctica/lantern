import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging

from boto3 import client as S3Client  # noqa: N812
from moto import mock_aws
from tasks.build import time_task
from tests.resources.stores.fake_records_store import FakeRecordsStore

from lantern.config import Config as Config
from lantern.exporters.site import SiteExporter
from lantern.log import init as init_logging


class FakeCatalogue:
    """Catalogue for fake records."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger

        with mock_aws():
            self._s3 = S3Client(
                "s3",
                aws_access_key_id="x",
                aws_secret_access_key="x",  # noqa: S106
                region_name="eu-west-1",
            )
        self._store = FakeRecordsStore(logger=self._logger)
        self._site = SiteExporter(config=self._config, logger=self._logger, s3=self._s3)

    # noinspection PyMethodOverriding
    @time_task(label="Load")
    def loads(self, inc_records: list[str], inc_related: bool) -> None:
        """Load records into catalogue store and site exporter."""
        self._logger.info("Loading records")
        self._store.populate(inc_records=inc_records, inc_related=inc_related)
        self._site.loads(records=self._store.records)
        self._logger.info(f"Loaded {len(self._store.records)} records")

    @time_task(label="Purge")
    def purge(self) -> None:
        """Empty records from catalogue store and site exporter."""
        self._logger.info("Purging catalogue store and site exporter outputs")
        self._site.purge()

    @time_task(label="Export")
    def export(self) -> None:
        """Export catalogue to file system."""
        self._site.export()


def main() -> None:
    """Entrypoint."""
    inc_records = []
    inc_related = True
    purge = False

    init_logging()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    config = Config()
    cat = FakeCatalogue(config=config, logger=logger)

    if purge:
        cat.purge()
    cat.loads(inc_records=inc_records, inc_related=inc_related)
    cat.export()


if __name__ == "__main__":
    main()
