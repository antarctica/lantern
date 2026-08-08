import os
import shutil
from typing import TYPE_CHECKING

from tasks._shared import time_task

from lantern.catalogues.base import CatalogueBase
from lantern.checks import Checker
from lantern.exporters.local import LocalExporter
from lantern.models.site import ExportMeta
from lantern.outputs.item_html import ItemCatalogueOutput
from lantern.outputs.redirects import RedirectsOutput
from lantern.site import Site
from tests.resources.stores.fake_records_store import FakeRecordsStore

if TYPE_CHECKING:
    import logging
    from pathlib import Path

    from lantern.config import Config


class FakeCatalogue(CatalogueBase):
    """
    Fake catalogue for testing.

    Used to test CatalogueBase and to build test/fake records into a local site for development.

    Simplistic catalogue example without record management features.
    """

    def __init__(self, logger: logging.Logger, config: Config, base_path: Path) -> None:
        super().__init__(logger)
        self._config = config
        self._path_untrusted = base_path
        self._path_trusted = base_path.with_name(f"{base_path.name}-trusted")

        self._store = FakeRecordsStore(logger=logger)
        self._checker = Checker(logger=self._logger, config=self._config)

        self._site_extras = {
            "site_records_count": len(self._store),
            "search_records_count": -1,  # not available
            "entra_secret_expiry": self._config.CHECKS_MAGIC_PRODUCTS_CLIENT_SECRET_EXP,
            "entra_secret_id": self._config.CHECKS_MAGIC_PRODUCTS_CLIENT_SECRET_ID,
        }

    @time_task(label="Export site")
    def export(self, identifiers: set[str] | None = None, trusted: bool = False) -> None:
        """Generate and export site content locally."""
        global_, individual = self._group_output_classes()
        if trusted:
            global_ = []
            individual = [ItemCatalogueOutput]
        path = self._path_untrusted if not trusted else self._path_trusted

        meta = ExportMeta.from_config(config=self._config, env="testing", build_repo_ref="83fake48", trusted=trusted)
        site = Site(logger=self._logger, meta=meta, store=self._store, extras=self._site_extras)
        exporter = LocalExporter(logger=self._logger, path=path)

        content = site.generate_content(global_outputs=global_, individual_outputs=individual, identifiers=identifiers)
        if not trusted:
            content.extend(RedirectsOutput(logger=self._logger, meta=meta, content=content).content)
        exporter.export(content)

        if not trusted:
            return
        if trusted and not self._path_untrusted.exists():
            self._logger.warning(
                "Cannot create symlink within untrusted content as untrusted content has not been exported."
            )
            return
        # Create relative symlink at '/-/items' to self._path_trusted, if needed
        # Enables e.g. '{self._path_trusted}/foo.txt' to be available at '{self._path_untrusted}/-/items/foo.txt'
        symlink_path = self._path_untrusted / "-" / "items"
        symlink_target = self._path_trusted / "items"
        symlink_path.parent.mkdir(parents=True, exist_ok=True)

        if symlink_path.exists() and symlink_path.is_symlink():
            return
        self._logger.info("Symlinking %s to %s", symlink_path.resolve(), symlink_target.resolve())
        relative_target = os.path.relpath(symlink_target, symlink_path.parent)
        symlink_path.symlink_to(relative_target, target_is_directory=True)

    @time_task(label="Check site")
    def check(self, identifiers: set[str] | None = None) -> None:
        """
        Check site contents (optionally for selected records).

        Locked to untrusted content.
        """
        global_, individual = self._group_output_classes()
        meta = ExportMeta.from_config(config=self._config, env="testing", build_repo_ref="83fake48", trusted=False)
        site = Site(logger=self._logger, meta=meta, store=self._store, extras=self._site_extras)
        exporter = LocalExporter(logger=self._logger, path=self._path_untrusted)

        checks = site.generate_checks(global_outputs=global_, individual_outputs=individual, identifiers=identifiers)
        content = self._checker.check(checks=checks, meta=meta)
        exporter.export(content)

    @time_task(label="Purge site")
    def purge(self) -> None:
        """Delete any existing site."""
        shutil.rmtree(self._path_untrusted, ignore_errors=True)
        shutil.rmtree(self._path_trusted, ignore_errors=True)
