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
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore


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

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        s3: S3Client,
        store: GitLabStore | GitLabCachedStore,
        trusted: bool = False,
        selected_identifiers: set[str] | None = None,
    ) -> None:
        self._logger = logger
        self._config = config
        self._s3 = s3
        self._store = store
        self._trusted = trusted
        self._selected_identifiers = selected_identifiers

        if isinstance(self._store, GitLabCachedStore):
            # ensure cache exists to get head commit for ExportMeta and is up to date before freezing
            self._store._cache._ensure_exists()
        self._meta = ExportMeta.from_config_store(
            config=self._config, store=self._store, build_repo_ref=self._store.head_commit, trusted=self._trusted
        )

        if isinstance(self._store, GitLabCachedStore):
            self._logger.info("Freezing store.")
            self._store._frozen = True
            self._store._cache._frozen = True

        self._site = SiteExporter(
            config=self._config,
            meta=self._meta,
            logger=self._logger,
            s3=self._s3,
            store=self._store,
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
        if isinstance(self._store, GitLabCachedStore):
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

    cached = True
    if len(selected) <= 3:
        cached = False
    logger, config, store, s3 = init(cached_store=cached)
    cat = ToyCatalogue(config=config, logger=logger, s3=s3, store=store, trusted=trusted, selected_identifiers=selected)

    if export:
        cat.export()
    if publish:
        cat.publish()


if __name__ == "__main__":
    main()
