from __future__ import annotations

import json
import logging
from datetime import date
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, PropertyMock
from uuid import uuid4

import pytest
from lxml import etree

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.checks import Check
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput
from lantern.repositories.base import RecordsProtocol
from lantern.site import Site, SiteAction, SiteJob, _job_worker_iso_html_transform, _job_worker_records, _run_job
from lantern.stores.gitlab_cache import GitLabCachedStore
from tests.resources.records.item_cat_product_min import record as product_min_required

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_mock import MockerFixture

    from lantern.models.record.revision import RecordRevision
    from lantern.outputs.base import OutputBase
    from lantern.stores.base import StoreBase
    from tests.resources.repositories.fake_repository import FakeRepository


@pytest.mark.usefixtures("fx_reset_site_singletons")
class TestSiteJob:
    """Test functions related to site generator parallel processing jobs."""

    @pytest.mark.cov()
    def test_job_worker_source(self, fx_records_snapshot: RecordsProtocol):
        """Can create records snapshot instance."""
        result = _job_worker_records(key=str(uuid4()), records=fx_records_snapshot)
        assert isinstance(result.record_count, int)

    @pytest.mark.cov()
    def test_job_worker_source_cached(self, fx_fake_repo: FakeRepository, fx_records_snapshot: RecordsProtocol):
        """Can reuse the records snapshot for workers associated with the same site."""
        key = str(uuid4())
        first = _job_worker_records(key=key, records=fx_records_snapshot)
        with fx_fake_repo.snapshot() as alt_snapshot:
            second = _job_worker_records(key=key, records=alt_snapshot)
        assert second is first

    @pytest.mark.cov()
    def test_job_worker_store_rekeyed(self, fx_fake_repo: FakeRepository, fx_records_snapshot: RecordsProtocol):
        """
        Cannot reuse the records snapshot for workers associated with different sites.

        As determined by site keys.
        """
        first = _job_worker_records(key=str(uuid4()), records=fx_records_snapshot)
        second = _job_worker_records(key=str(uuid4()), records=MagicMock(spec=RecordsProtocol))
        assert second is not first

    @pytest.mark.cov()
    def test_job_worker_store_gitlab_cache(self, fx_gitlab_cached_store_pop: GitLabCachedStore):
        """
        Can create and re-warm a GitLabCachedStore instance.

        To test `RecordsProtocol.restore_parallel()` method, which in this case calls a Store implementing that
        protocol directly (rather than via a Repository).
        """
        fx_gitlab_cached_store_pop._cache._flash.clear()
        result = _job_worker_records(key=str(uuid4()), records=fx_gitlab_cached_store_pop)
        assert isinstance(result, GitLabCachedStore)
        assert len(result._cache._flash) > 0

    @pytest.mark.cov()
    def test_job_worker_iso_transform(self):
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
        fx_select_record: Callable,
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
        expected_count = 99
        expected_str = "x"
        expected_date = date(2014, 6, 30)

        individual_outputs = [
            ItemCatalogueOutput,
            ItemAliasesOutput,
            RecordIsoJsonOutput,
            RecordIsoXmlOutput,
            RecordIsoHtmlOutput,
        ]
        job = SiteJob(
            action="content",
            output=output_cls,
            record=fx_revision_model_min if output_cls in individual_outputs else None,
            extras={
                "site_records_count": expected_count,
                "search_records_count": expected_count,
                "entra_client_secret_expiry": expected_date,
                "entra_client_secret_id": expected_str,
            }
            if output_cls == SiteHealthOutput
            else None,
        )
        content = _run_job(
            log_level=logging.DEBUG, meta=fx_export_meta, records=fx_fake_store, job=job, worker_key=str(uuid4())
        )

        results = [str(output.path) for output in content]
        for exp in expected:
            assert exp in results

        checks = _run_job(
            log_level=logging.DEBUG,
            meta=fx_export_meta,
            records=fx_fake_store,
            job=SiteJob(action="checks", output=output_cls, record=fx_revision_model_min),
            worker_key=str(uuid4()),
        )
        assert len(checks) > 0

        for check in checks:
            if check.url.removeprefix(f"{fx_export_meta.base_url}/") in results:
                assert check.http_status == (HTTPStatus.MOVED_PERMANENTLY if check.redirect_location else HTTPStatus.OK)

        # check content for outputs that use extras
        if output_cls == SiteHealthOutput:
            health_output = next(output for output in content if str(output.path) == "static/json/health.json")
            health_data = json.loads(health_output.content)
            assert health_data["checks"]["site:records"]["observedValue"] == expected_count
            assert health_data["checks"]["search:records"]["observedValue"] == expected_count
            assert isinstance(health_data["checks"]["entra:expiry"]["observedValue"], int)

    @pytest.mark.parametrize("output_cls", [ItemCatalogueOutput, RecordIsoXmlOutput, RecordIsoHtmlOutput])
    def test_check_jobs_do_not_render(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_revision_model_min: RecordRevision,
        fx_records_snapshot: RecordsProtocol,
        fx_export_meta: ExportMeta,
        output_cls: type[OutputBase],
    ):
        """Can output checks and invalidations without generating content."""
        rendered = mocker.patch.object(output_cls, "_content", new_callable=PropertyMock)
        rendered.side_effect = AssertionError("rendered content")
        for action in ("checks", "invalidations"):
            results = _run_job(
                log_level=fx_logger.level,
                meta=fx_export_meta,
                records=fx_records_snapshot,
                job=SiteJob(action=action, output=output_cls, record=fx_revision_model_min),
                worker_key=str(uuid4()),
            )
            assert results
        rendered.assert_not_called()


class TestSite:
    """Test site generator."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_records_snapshot: RecordsProtocol):
        """Can create a site generator instance."""
        site = Site(logger=fx_logger, meta=fx_export_meta, records=fx_records_snapshot)
        assert isinstance(site, Site)
        assert site._extras == {}
        assert site._workers == 1
        assert site._worker_key

    @pytest.mark.cov()
    def test_worker_key_unique(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_records_snapshot: RecordsProtocol
    ):
        """Can assign a distinct worker key to site instances, to prevent workers pollution."""
        site_a = Site(logger=fx_logger, meta=fx_export_meta, records=fx_records_snapshot)
        site_b = Site(logger=fx_logger, meta=fx_export_meta, records=fx_records_snapshot)
        assert site_a._worker_key != site_b._worker_key

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("actions", "global_", "individual", "extras", "identifiers", "expected"),
        [
            ([], [], [], None, None, []),
            (
                ["content"],
                [SiteResourcesOutput],
                [],
                {"x": "x"},
                None,
                [SiteJob(action="content", output=SiteResourcesOutput, extras={"x": "x"})],
            ),
            (["checks"], [SiteResourcesOutput], [], None, None, [SiteJob(action="checks", output=SiteResourcesOutput)]),
            (
                ["invalidations"],
                [SiteResourcesOutput],
                [],
                None,
                None,
                [SiteJob(action="invalidations", output=SiteResourcesOutput)],
            ),
            (["content"], [], [ItemCatalogueOutput], None, None, []),
            (
                ["content"],
                [],
                [ItemCatalogueOutput, RecordIsoXmlOutput],
                None,
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
                None,
                {product_min_required.file_identifier},
                [
                    SiteJob(action="content", output=SiteResourcesOutput),
                    SiteJob(action="checks", output=SiteResourcesOutput),
                    SiteJob(action="content", output=ItemCatalogueOutput, record=product_min_required),
                    SiteJob(action="checks", output=ItemCatalogueOutput, record=product_min_required),
                ],
            ),
            (
                ["content", "checks", "invalidations"],
                [SiteResourcesOutput],
                [ItemCatalogueOutput],
                None,
                {product_min_required.file_identifier},
                [
                    SiteJob(action="content", output=SiteResourcesOutput),
                    SiteJob(action="checks", output=SiteResourcesOutput),
                    SiteJob(action="invalidations", output=SiteResourcesOutput),
                    SiteJob(action="content", output=ItemCatalogueOutput, record=product_min_required),
                    SiteJob(action="checks", output=ItemCatalogueOutput, record=product_min_required),
                    SiteJob(action="invalidations", output=ItemCatalogueOutput, record=product_min_required),
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
        extras: dict | None,
        identifiers: set[str] | None,
        expected: list[SiteJob],
    ):
        """Can generate expected processing jobs."""
        if extras:
            fx_site._extras = extras

        result = fx_site._generate_jobs(actions, global_, individual, identifiers)
        if individual and not identifiers:
            # where > 0 individual output classes and no selected identifiers, jobs are generated for all records
            assert len(result) > 0
        else:
            assert result == expected

    @pytest.mark.cov()
    def test_execute(self, fx_site: Site):
        """Can generate expected site content, checks and/or invalidation keys for directly created processing jobs."""
        results = fx_site.execute(
            jobs=[
                SiteJob(action="content", output=SiteIndexOutput),
                SiteJob(action="checks", output=SiteIndexOutput),
                SiteJob(action="invalidations", output=SiteIndexOutput),
            ]
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

    def test_generate_invalidation_keys(self, fx_site: Site):
        """Can generate expected invalidation keys for selected outputs."""
        results = fx_site.generate_invalidation_keys(global_outputs=[SiteIndexOutput], individual_outputs=[])
        assert sorted(results) == sorted(["/-/index/index.html", "/-/index/"])
