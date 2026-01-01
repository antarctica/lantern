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
from lantern.stores.base import Store
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


def _init_store_adapter(logger: logging.Logger, config: Config | None, frozen: bool = False) -> Store:
    """To resolve type errors."""
    if config is None:
        raise TypeError()

    return init_gitlab_store(logger=logger, config=config, frozen=frozen)


class ToyCatalogue:
    """Toy catalogue for prototyping."""

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        s3: S3Client,
        trusted: bool = False,
        selected_identifiers: set[str] | None = None,
    ) -> None:
        self._logger = logger
        self._config = config
        self._s3 = s3
        self._trusted = trusted
        self._selected_identifiers = selected_identifiers

        self._store = init_gitlab_store(logger=self._logger, config=self._config)
        if self._store.head_commit is None:
            # noinspection PyProtectedMember
            self._store._cache._ensure_exists()  # ensure cache exists to get head commit for ExportMeta
        self._meta = ExportMeta.from_config_store(
            config=self._config, store=None, build_repo_ref=self._store.head_commit, trusted=self._trusted
        )

        self._site = SiteExporter(
            config=self._config,
            meta=self._meta,
            logger=self._logger,
            s3=self._s3,
            init_store=_init_store_adapter,
            selected_identifiers=selected_identifiers,
        )

    @time_task(label="Export")
    def export(self) -> None:
        """Export catalogue to file system."""
        self._site.export()

    @time_task(label="Publish")
    def publish(self) -> None:
        """Publish catalogue to S3."""
        self._site.publish()

    # noinspection PyProtectedMember
    @time_task(label="Purge")
    def purge(self, purge_export: bool = False, purge_publish: bool = False) -> None:
        """Empty records from catalogue store and site exporter."""
        self._logger.info("Purging store")
        self._store.purge()

        if purge_export and self._site._meta.export_path.exists():
            self._site._logger.info("Purging file system export directory")
            shutil.rmtree(self._site._meta.export_path)
        if purge_publish:
            self._logger.info("Purging S3 publishing bucket")
            self._site._s3_utils.empty_bucket()


def main() -> None:
    """Entrypoint."""
    export = True
    publish = False
    selected = set()  # to set use the form {"abc", "..."}
    trusted = False

    logger, config, _store, s3, _keys = init()
    cat = ToyCatalogue(config=config, logger=logger, s3=s3, trusted=trusted, selected_identifiers=selected)

    if export:
        cat.export()
    if publish:
        cat.publish()


if __name__ == "__main__":
    main()
