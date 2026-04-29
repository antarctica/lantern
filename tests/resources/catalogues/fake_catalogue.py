import functools
import logging
import shutil
import time
from collections.abc import Callable
from pathlib import Path

from lantern.catalogues.base import CatalogueBase
from lantern.checks import Checker
from lantern.config import Config
from lantern.exporters.local import LocalExporter
from lantern.models.site import ExportMeta
from lantern.site import Site
from tests.resources.stores.fake_records_store import FakeRecordsStore


def time_task(label: str) -> Callable:
    """
    Time a task and log duration.

    Copied from tasks.shared.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            start = time.monotonic()
            result = func(*args, **kwargs)
            logger = logging.getLogger("app")
            logger.setLevel(logging.INFO)
            logger.info(f"{label} took {round(time.monotonic() - start)} seconds")
            return result

        return wrapper

    return decorator


class FakeCatalogue(CatalogueBase):
    """
    Fake catalogue for testing.

    Used to test CatalogueBase and to build test/fake records into a local site for development.

    Simplistic catalogue example without record management features.
    """

    def __init__(self, logger: logging.Logger, config: Config, base_path: Path) -> None:
        super().__init__(logger)
        self._config = config
        self._path = base_path

        self._store = FakeRecordsStore(logger=logger)
        self._meta = ExportMeta.from_config(config=self._config, env="testing", build_repo_ref="83fake48", trusted=True)
        self._site = Site(logger=logger, meta=self._meta, store=self._store)
        self._exporter = LocalExporter(logger=logger, path=self._path)
        self._checker = Checker(logger=self._logger, parallel_jobs=config.PARALLEL_JOBS)

    @time_task(label="Export site")
    def export(self, identifiers: set[str] | None = None) -> None:
        """Generate and export site content to hosting."""
        global_, individual = self._group_output_classes()
        content = self._site.generate_content(
            global_outputs=global_, individual_outputs=individual, identifiers=identifiers
        )
        self._exporter.export(content)

    @time_task(label="Check site")
    def check(self, identifiers: set[str] | None = None) -> None:
        """Check site contents (optionally for selected records)."""
        global_, individual = self._group_output_classes()
        checks = self._site.generate_checks(
            global_outputs=global_, individual_outputs=individual, identifiers=identifiers
        )
        content = self._checker.check(checks=checks, meta=self._meta)
        self._exporter.export(content)

    @time_task(label="Purge site")
    def purge(self) -> None:
        """Delete any existing site."""
        shutil.rmtree(self._path, ignore_errors=True)
