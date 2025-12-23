import functools
import logging
import shutil
from collections.abc import Callable
from datetime import UTC, datetime

from mypy_boto3_s3 import S3Client
from tasks._record_utils import init

from lantern.config import Config as Config
from lantern.exporters.site import SiteExporter
from lantern.models.site import ExportMeta
from lantern.utils import init_gitlab_store


def time_task(label: str) -> Callable:
    """Time a task and log duration."""

    def decorator(func: Callable) -> Callable:
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

    def __init__(self, logger: logging.Logger, config: Config, s3: S3Client, trusted: bool = False) -> None:
        self._logger = logger
        self._config = config
        self._s3 = s3
        self._trusted = trusted

        self._store = init_gitlab_store(logger=self._logger, config=self._config)

        self._meta = ExportMeta.from_config_store(
            config=self._config, store=None, build_repo_ref=self._store.head_commit, trusted=self._trusted
        )
        self._site = SiteExporter(
            config=self._config, meta=self._meta, logger=self._logger, s3=self._s3, get_record=self._store.get
        )

    # noinspection PyMethodOverriding
    @time_task(label="Load")
    def loads(self) -> None:
        """Load records into catalogue store and site exporter."""
        self._logger.info(f"Loading available records from branch '{self._store.branch}' of store")
        self._store.populate()
        # update head commit in meta as cache will now exist
        self._meta.build_repo_ref = self._store.head_commit

    # noinspection PyProtectedMember
    @time_task(label="Purge")
    def purge(self, purge_export: bool = False, purge_publish: bool = False) -> None:
        """Empty records from catalogue store and site exporter."""
        self._logger.info("Purging store and store cache")
        self._store.purge()
        self._store._cache.purge()

        if purge_export and self._site._meta.export_path.exists():
            self._site._logger.info("Purging file system export directory")
            shutil.rmtree(self._site._meta.export_path)
        if purge_publish:
            self._logger.info("Purging S3 publishing bucket")
            self._site._s3_utils.empty_bucket()

    def _get_selections(self, selection: set[str] | None) -> set[str]:
        """Select all identifiers if none specified."""
        if selection is not None and len(selection) > 0:
            return selection
        return {record.file_identifier for record in self._store.records}

    @time_task(label="Export")
    def export(self, file_identifiers: set[str] | None = None) -> None:
        """Export catalogue to file system."""
        self._site.select(file_identifiers=self._get_selections(file_identifiers))
        self._site.export()

    @time_task(label="Export")
    def publish(self, file_identifiers: set[str] | None = None) -> None:
        """Publish catalogue to S3."""
        self._site.select(file_identifiers=self._get_selections(file_identifiers))
        self._site.publish()


def main() -> None:
    """Entrypoint."""
    export = True
    publish = False
    selected = set()  # to set use the form {"abc", "..."}
    purge = False
    trusted = False

    logger, config, _store, s3, _keys = init()
    cat = ToyCatalogue(config=config, logger=logger, s3=s3, trusted=trusted)

    if purge:
        cat.purge()
    cat.loads()
    if export:
        cat.export(file_identifiers=selected)
    if publish:
        cat.publish(file_identifiers=selected)


if __name__ == "__main__":
    main()
