import importlib
import logging
from collections.abc import Callable

import pytest
from lxml import etree

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.checks import Check
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputBase
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput
from lantern.site import Site, SiteAction, SiteJob, _job_worker_iso_html_transform, _job_worker_store, _run_job
from lantern.stores.base import StoreBase
from lantern.stores.gitlab_cache import GitLabCachedStore
from tests.resources.records.item_cat_product_min import record as product_min_required


@pytest.fixture()
def fx_reset_singletons():
    """Reset singletons for test isolation."""
    mod = importlib.import_module("lantern.site")
    mod._STORE_SINGLETON = None
    mod._ISO_HTML_XSLT_SINGLETON = None

    yield

    mod._STORE_SINGLETON = None
    mod._ISO_HTML_XSLT_SINGLETON = None


class TestSiteJob:
    """Test functions related to site generator parallel processing jobs."""

    @pytest.mark.cov()
    def test_job_worker_store(self, fx_reset_singletons, fx_fake_store: StoreBase):  # noqa: ANN001
        """Can create store instance."""
        result = _job_worker_store(store=fx_fake_store)
        assert isinstance(result, StoreBase)

    @pytest.mark.cov()
    def test_job_worker_store_gitlab_cache(self, fx_reset_singletons, fx_gitlab_cached_store_pop: GitLabCachedStore):  # noqa: ANN001
        """Can create and re-warm GitLabCachedStore instance."""
        fx_gitlab_cached_store_pop._cache._flash.clear()
        result = _job_worker_store(store=fx_gitlab_cached_store_pop)
        assert isinstance(result, GitLabCachedStore)
        assert len(result._cache._flash) > 0

    @pytest.mark.cov()
    def test_job_worker_iso_transform(self, fx_reset_singletons):  # noqa: ANN001
        """Can create ISO HTML XSLT instance."""
        result = _job_worker_iso_html_transform()
        assert isinstance(result, etree.XSLT)

    @pytest.mark.parametrize(
        ("output_cls", "expected"),
        [
            (SiteResourcesOutput, ["static/css/main.css", "favicon.ico"]),  # representative
            (SiteIndexOutput, ["-/index/index.html"]),
            (SitePagesOutput, ["404.html", "legal/accessibility/index.html"]),  # representative
            (SiteApiOutput, [".well-known/api-catalog", "static/json/openapi.json"]),  # representative
            (SiteHealthOutput, ["static/json/health.json", "-/health"]),
            (RecordsWafOutput, ["waf/iso-19139-all/index.html"]),
            (ItemsBasWebsiteOutput, ["-/public-website-search/items.json"]),
            (ItemCatalogueOutput, ["items/FILE_IDENTIFIER/index.html"]),
            (ItemAliasesOutput, ["products/x/index.html"]),
            (RecordIsoJsonOutput, ["records/FILE_IDENTIFIER.json"]),
            (RecordIsoXmlOutput, ["records/FILE_IDENTIFIER.xml"]),
            (RecordIsoHtmlOutput, ["records/FILE_IDENTIFIER.html"]),
        ],
    )
    def test_job(
        self,
        fx_logger: logging.Logger,
        fx_revision_model_min: RecordRevision,
        fx_select_record: callable,
        fx_fake_store: StoreBase,
        fx_export_meta: ExportMeta,
        output_cls: OutputBase,
        expected: list[str],
    ):
        """Can output site content and checks for an output class."""
        fx_revision_model_min.identification.identifiers.append(
            Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/products/x", namespace=ALIAS_NAMESPACE)
        )
        expected = [exp.replace("FILE_IDENTIFIER", fx_revision_model_min.file_identifier) for exp in expected]

        content = _run_job(
            log_level=logging.DEBUG,
            meta=fx_export_meta,
            store=fx_fake_store,
            job=SiteJob(action="content", output=output_cls, record=fx_revision_model_min),
        )
        results = [str(output.path) for output in content]
        for exp in expected:
            assert exp in results

        checks = _run_job(
            log_level=logging.DEBUG,
            meta=fx_export_meta,
            store=fx_fake_store,
            job=SiteJob(action="checks", output=output_cls, record=fx_revision_model_min),
        )
        assert len(checks) > 0


class TestSite:
    """Test site generator."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_fake_store: StoreBase):
        """Can create a site generator instance."""
        site = Site(logger=fx_logger, meta=fx_export_meta, store=fx_fake_store)
        assert isinstance(site, Site)
        assert site._workers == 1

    @pytest.mark.cov()
    def test_prep_store_gitlab_cache(self, fx_site: Site, fx_gitlab_cached_store_pop: GitLabCachedStore):
        """Can clear the flash cache of a GitLabCachedStore prior to parallel processing."""
        fx_site._store = fx_gitlab_cached_store_pop
        _ = fx_gitlab_cached_store_pop.select()
        assert len(fx_gitlab_cached_store_pop._cache._flash) > 0
        result: GitLabCachedStore = fx_site._prep_store()
        assert len(result._cache._flash) == 0
        assert len(fx_gitlab_cached_store_pop._cache._flash) > 0

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("actions", "global_", "individual", "identifiers", "expected"),
        [
            ([], [], [], None, []),
            (["content"], [SiteResourcesOutput], [], None, [SiteJob(action="content", output=SiteResourcesOutput)]),
            (["checks"], [SiteResourcesOutput], [], None, [SiteJob(action="checks", output=SiteResourcesOutput)]),
            (["content"], [], [ItemCatalogueOutput], None, []),
            (
                ["content"],
                [],
                [ItemCatalogueOutput, RecordIsoXmlOutput],
                {product_min_required.file_identifier},
                [
                    SiteJob(action="content", output=ItemCatalogueOutput, record=product_min_required),
                    SiteJob(action="content", output=RecordIsoXmlOutput, record=product_min_required),
                ],
            ),
            (
                ["content", "checks"],
                [SiteResourcesOutput],
                [ItemCatalogueOutput],
                {product_min_required.file_identifier},
                [
                    SiteJob(action="content", output=SiteResourcesOutput),
                    SiteJob(action="checks", output=SiteResourcesOutput),
                    SiteJob(action="content", output=ItemCatalogueOutput, record=product_min_required),
                    SiteJob(action="checks", output=ItemCatalogueOutput, record=product_min_required),
                ],
            ),
        ],
    )
    def test_generate_jobs(
        self,
        fx_site: Site,
        actions: list[SiteAction],
        global_: list[Callable[..., OutputBase]],
        individual: list[Callable[..., OutputBase]],
        identifiers: set[str] | None,
        expected: list[SiteJob],
    ):
        """Can generate expected processing jobs."""
        result = fx_site._generate_jobs(actions, global_, individual, identifiers)
        if individual and not identifiers:
            # where > 0 individual output classes and no selected identifiers, jobs are generated for all records
            assert len(result) > 0
        else:
            assert result == expected

    @pytest.mark.cov()
    def test_execute(self, fx_site: Site):
        """Can generate expected site content and/or checks for directly created processing jobs."""
        results = fx_site.execute(
            jobs=[SiteJob(action="content", output=SiteIndexOutput), SiteJob(action="checks", output=SiteIndexOutput)]
        )
        assert len(results) > 0

    def test_generate_content(self, fx_site: Site):
        """Can generate expected site content for selected outputs."""
        results = fx_site.generate_content(global_outputs=[SiteIndexOutput], individual_outputs=[])
        assert len(results) > 0
        assert all(isinstance(result, SiteContent) for result in results)

    def test_generate_checks(self, fx_site: Site):
        """Can generate expected checks for selected outputs."""
        results = fx_site.generate_checks(global_outputs=[SiteIndexOutput], individual_outputs=[])
        assert len(results) > 0
        assert all(isinstance(result, Check) for result in results)
