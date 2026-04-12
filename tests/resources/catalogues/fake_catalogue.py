import logging
import shutil
from pathlib import Path

from tasks._shared import time_task

from lantern.catalogue import CatalogueBase
from lantern.checks import Checker
from lantern.config import Config
from lantern.exporters.local import LocalExporter
from lantern.models.site import ExportMeta
from lantern.site import Site
from tests.resources.stores.fake_records_store import FakeRecordsStore


class FakeCatalogue(CatalogueBase):
    """
    Fake catalogue for testing.

    Used to test CatalogueBase and to build test/fake records into a local site for development.

    Simplistic catalogue example without record management features.
    """

    def __init__(self, logger: logging.Logger, config: Config, store: FakeRecordsStore, base_path: Path) -> None:
        super().__init__(logger)
        self._config = config
        self._store = store
        self._path = base_path

        self._meta = ExportMeta.from_config_store(
            config=self._config, env="testing", store=None, build_repo_ref="83fake48", trusted=True
        )
        self._site = Site(logger=logger, meta=self._meta, store=store)
        self._exporter = LocalExporter(logger=logger, path=self._path)
        self._checker = Checker(logger=self._logger, meta=self._meta)

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
        content = self._checker.check(checks)
        self._exporter.export(content)

    @time_task(label="Purge site")
    def purge(self) -> None:
        """Delete any existing site."""
        shutil.rmtree(self._path, ignore_errors=True)
