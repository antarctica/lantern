import logging
import shutil
from pathlib import Path

from tasks._shared import time_task

from lantern.catalogue import CatalogueBase
from lantern.config import Config
from lantern.exporters.local import LocalExporter
from lantern.models.site import ExportMeta, SiteContent
from lantern.models.verification.types import VerificationContext
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput
from lantern.site import Site
from lantern.verification import Verification
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
        self._verify_context = VerificationContext(
            BASE_URL=self._config.BASE_URL_TESTING,
            SHAREPOINT_PROXY_ENDPOINT=self._config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
            SAN_PROXY_ENDPOINT=self._config.VERIFY_SAN_PROXY_ENDPOINT,
        )

        self._site = Site(logger=logger, meta=self._meta, store=store)
        self._exporter = LocalExporter(logger=logger, path=self._path)

    @time_task(label="Generate site")
    def _generate(self, identifiers: set[str] | None = None) -> list[SiteContent]:
        """Generate a static site from records and other content."""
        return self._site.process(
            global_outputs=[
                SiteResourcesOutput,
                SiteIndexOutput,
                SitePagesOutput,
                SiteApiOutput,
                SiteHealthOutput,
                RecordsWafOutput,
                ItemsBasWebsiteOutput,
            ],
            individual_outputs=[
                ItemCatalogueOutput,
                ItemAliasesOutput,
                RecordIsoJsonOutput,
                RecordIsoXmlOutput,
                RecordIsoHtmlOutput,
            ],
            identifiers=identifiers,
        )

    @time_task(label="Generate site")
    def export(self, identifiers: set[str] | None = None) -> None:
        """Generate and export site content to hosting."""
        self._exporter.export(self._generate(identifiers))

    @time_task(label="Verify site")
    def verify(self, identifiers: set[str] | None = None) -> None:
        """Verify site contents (optionally for selected records)."""
        verify = Verification(
            logger=self._logger,
            meta=self._meta,
            context=self._verify_context,
            select_records=self._store.select,
            identifiers=identifiers,
        )
        verify.run()
        self._exporter.export(verify.outputs)

    @time_task(label="Purge site")
    def purge(self) -> None:
        """Delete any existing site."""
        shutil.rmtree(self._path, ignore_errors=True)
