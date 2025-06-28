import functools
import logging
from datetime import UTC, datetime

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.site_exporter import SiteExporter
from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config as LanternConfig
from lantern.stores.gitlab import GitLabStore


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


class ToyCatalogue:
    """Toy catalogue for prototyping."""

    def __init__(self, config: Config, config_lantern: LanternConfig, logger: logging.Logger, s3: S3Client) -> None:
        self._config = config
        self._config_lantern = config_lantern
        self._s3 = s3
        self._logger = logger
        self._store = GitLabStore(
            logger=self._logger,
            endpoint=self._config_lantern.STORE_GITLAB_ENDPOINT,
            access_token=self._config_lantern.STORE_GITLAB_TOKEN,
            project_id=self._config_lantern.STORE_GITLAB_PROJECT_ID,
            cache_path=self._config_lantern.STORE_GITLAB_CACHE_PATH,
        )
        self._site = SiteExporter(config=self._config, logger=self._logger, s3=self._s3)

    # noinspection PyMethodOverriding
    @time_task(label="Load")
    def loads(self, inc_records: list[str], exc_records: list[str], inc_related: bool) -> None:
        """Load records into catalogue store and site exporter."""
        self._logger.info("Loading records")
        self._store.populate(inc_records=inc_records, exc_records=exc_records, inc_related=inc_related)
        self._site.loads(summaries=self._store.summaries, records=self._store.records)
        self._logger.info(f"Loaded {len(self._store.summaries)} summaries and {len(self._store.records)} records")

    @time_task(label="Purge")
    def purge(self) -> None:
        """Empty records from catalogue store and site exporter."""
        self._logger.info("Purging catalogue store and site exporter outputs")
        self._store.purge()
        self._site.purge()

    @time_task(label="Export")
    def export(self) -> None:
        """Export catalogue to file system."""
        self._site.export()

    @time_task(label="Export")
    def publish(self) -> None:
        """Publish catalogue to S3."""
        self._site.publish()


def main() -> None:
    """Entrypoint."""
    inc_records = []
    exc_records = []
    inc_related = True
    export = True
    publish = False
    purge = False

    logger = logging.getLogger("app")
    logger.info("Initialising")

    config = Config()
    config_lantern = LanternConfig()
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID,
        aws_secret_access_key=config.EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )

    cat = ToyCatalogue(config=config, config_lantern=config_lantern, logger=logger, s3=s3)

    if purge:
        cat.purge()
    cat.loads(inc_records=inc_records, exc_records=exc_records, inc_related=inc_related)
    if export:
        cat.export()
    if publish:
        cat.publish()


if __name__ == "__main__":
    main()
