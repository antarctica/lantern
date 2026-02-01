import functools
import logging
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from mypy_boto3_s3 import S3Client
from tasks._config import ExtraConfig
from tasks._record_utils import init

from lantern.exporters.html import HtmlExporter
from lantern.exporters.site import SiteExporter, SiteResourcesExporter
from lantern.models.site import ExportMeta
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import RsyncUtils


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


def upload_trusted(
    logger: logging.Logger, config: ExtraConfig, store: GitLabStore, s3: S3Client, identifiers: set[str] | None = None
) -> None:
    """
    Publish trusted content to SFTP.

    Group write permissions are set on uploaded files (660) and directories (770) to allow shared management.
    """
    sync = RsyncUtils(logger=logger)
    export_meta = ExportMeta.from_config_store(
        config=config, store=store, build_repo_ref=store.head_commit, trusted=True
    )
    with TemporaryDirectory() as tmp_path:
        items_path = Path(tmp_path) / "items"
    items_path.mkdir(parents=True, exist_ok=True)

    env_path = "stage" if "integration" in config.AWS_S3_BUCKET else "prod"
    items_target = config.TRUSTED_UPLOAD_PATH / env_path / "items"

    assets_exporter = SiteResourcesExporter(logger=logger, meta=export_meta, s3=s3)
    assets_exporter.export()

    for record in store.select(identifiers):
        fid = record.file_identifier
        logger.info(f"Generating record '{fid}' using Item HTML exporter in a trusted context")
        item_exporter = HtmlExporter(
            logger=logger, meta=export_meta, s3=s3, record=record, select_record=store.select_one
        )
        item_path = items_path / fid / "index.html"
        item_path.parent.mkdir(parents=True, exist_ok=True)
        with item_path.open("w") as record_file:
            record_file.write(item_exporter.dumps())
        item_path.parent.chmod(0o770)
        item_path.chmod(0o660)

    sync.put(src_path=items_path, target_path=items_target, target_host=config.TRUSTED_UPLOAD_HOST)


class ToyCatalogue:
    """Toy catalogue for prototyping."""

    def __init__(
        self,
        logger: logging.Logger,
        config: ExtraConfig,
        s3: S3Client,
        store: GitLabStore | GitLabCachedStore,
        selected_identifiers: set[str] | None = None,
    ) -> None:
        self._logger = logger
        self._config = config
        self._s3 = s3
        self._store = store
        self._selected_identifiers = selected_identifiers

        if isinstance(self._store, GitLabCachedStore):
            # ensure cache exists to get head commit for ExportMeta and is up to date before freezing
            self._store._cache._ensure_exists()
        self._meta = ExportMeta.from_config_store(
            config=self._config, store=self._store, build_repo_ref=self._store.head_commit, trusted=False
        )

        if isinstance(self._store, GitLabCachedStore):
            self._logger.info("Freezing store.")
            self._store._frozen = True
            self._store._cache._frozen = True

        self._site = SiteExporter(
            logger=self._logger,
            config=self._config,
            meta=self._meta,
            s3=self._s3,
            store=self._store,
            selected_identifiers=selected_identifiers,
        )

    @time_task(label="Export")
    def export(self) -> None:
        """Export catalogue to file system."""
        self._site.export()

    def _publish_untrusted(self) -> None:
        """Publish catalogue to S3 with unrestricted access."""
        self._site.publish()

    def _publish_trusted(self) -> None:
        """Publish supplemental content with restricted access."""
        upload_trusted(
            logger=self._logger,
            config=self._config,
            store=self._store,
            s3=self._s3,
            identifiers=self._selected_identifiers,
        )

    @time_task(label="Publish")
    def publish(self) -> None:
        """Publish catalogue to remote (un)trusted location."""
        self._publish_untrusted()
        self._publish_trusted()

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

    cached = True  # always cached as index and website search exporters always select all records
    logger, config, store, s3 = init(cached_store=cached)
    cat = ToyCatalogue(config=config, logger=logger, s3=s3, store=store, selected_identifiers=selected)

    if export:
        cat.export()
    if publish:
        cat.publish()


if __name__ == "__main__":
    main()
