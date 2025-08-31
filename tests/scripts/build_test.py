import functools
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import logging

from boto3 import client as S3Client  # noqa: N812
from moto import mock_aws
from tests.resources.stores.fake_records_store import FakeRecordsStore

from lantern.config import Config as Config
from lantern.exporters.site import SiteExporter
from lantern.log import init as init_logging


def time_task(label: str) -> callable:
    """Time a task and log duration."""

    def decorator(func: callable) -> callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202,
            start = datetime.now(tz=UTC)
            result = func(self, *args, **kwargs)
            end = datetime.now(tz=UTC)
            self._logger.info(f"{label} took {round((end - start).total_seconds())} seconds")
            return result

        return wrapper

    return decorator


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
        self._site = SiteExporter(config=self._config, logger=self._logger, s3=self._s3, get_record=self._store.get)

    # noinspection PyMethodOverriding
    @time_task(label="Load")
    def loads(self, inc_records: list[str]) -> None:
        """Load records into catalogue store and site exporter."""
        self._logger.info("Loading records")
        self._store.populate(inc_records=inc_records)
        self._site.select(file_identifiers={record.file_identifier for record in self._store.records})
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
    purge = False

    init_logging()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    config = Config()
    cat = FakeCatalogue(config=config, logger=logger)

    if purge:
        cat.purge()
    cat.loads(inc_records=inc_records)
    cat.export()


if __name__ == "__main__":
    main()
