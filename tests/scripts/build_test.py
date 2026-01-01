import functools
import sys
from datetime import UTC, datetime
from pathlib import Path

from lantern.models.site import ExportMeta
from lantern.stores.base import Store

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


# noinspection PyUnusedLocal
def _init_store_adapter(logger: logging.Logger, config: Config | None, frozen: bool = False) -> Store:
    """To resolve type errors."""
    return FakeRecordsStore(logger=logger, frozen=frozen)


class FakeCatalogue:
    """Catalogue for fake records."""

    def __init__(self, logger: logging.Logger, config: Config, inc_records: set[str] | None = None) -> None:
        self._logger = logger
        self._config = config

        meta = ExportMeta.from_config_store(config=self._config, store=None, build_repo_ref="83fake48", trusted=True)
        with mock_aws():
            self._s3 = S3Client(
                "s3",
                aws_access_key_id="x",
                aws_secret_access_key="x",  # noqa: S106
                region_name="eu-west-1",
            )
        self._site = SiteExporter(
            logger=self._logger,
            config=self._config,
            meta=meta,
            s3=self._s3,
            init_store=_init_store_adapter,
            selected_identifiers=inc_records,
        )

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
    inc_records = set()
    purge = False

    config = Config()
    init_logging(config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising")

    cat = FakeCatalogue(config=config, logger=logger, inc_records=inc_records)

    if purge:
        cat.purge()
    cat.export()


if __name__ == "__main__":
    main()
