import functools
import logging
from datetime import UTC, datetime

from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config as Config
from lantern.exporters.site import SiteExporter
from lantern.log import init as init_logging
from lantern.log import init_sentry
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

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        self._config = config
        self._s3 = s3
        self._logger = logger
        self._store = GitLabStore(
            logger=self._logger,
            endpoint=self._config.STORE_GITLAB_ENDPOINT,
            access_token=self._config.STORE_GITLAB_TOKEN,
            project_id=self._config.STORE_GITLAB_PROJECT_ID,
            cache_path=self._config.STORE_GITLAB_CACHE_PATH,
        )
        self._site = SiteExporter(config=self._config, logger=self._logger, s3=self._s3)

    # noinspection PyMethodOverriding
    @time_task(label="Load")
    def loads(self, inc_records: list[str], exc_records: list[str]) -> None:
        """Load records into catalogue store and site exporter."""
        self._logger.info("Loading records")
        self._store.populate(inc_records=inc_records, exc_records=exc_records)
        self._site.loads(records=self._store.records)

    @time_task(label="Purge")
    def purge(self) -> None:
        """Empty records from catalogue store and site exporter."""
        self._logger.info("Purging store and site exporter outputs")
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
    export = True
    publish = False
    purge = False

    init_logging()
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    config = Config()
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )

    cat = ToyCatalogue(config=config, logger=logger, s3=s3)

    if purge:
        cat.purge()
    cat.loads(inc_records=inc_records, exc_records=exc_records)
    if export:
        cat.export()
    if publish:
        cat.publish()


if __name__ == "__main__":
    main()
