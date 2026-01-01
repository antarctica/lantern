import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture
from requests import Response

from lantern.exporters.verification import (
    VerificationExporter,
    VerificationReport,
    _req_url,
    check_item_download,
    check_url,
    check_url_arcgis,
    check_url_redirect,
    run_job,
)
from lantern.lib.metadata_library.models.record.elements.common import (
    Identifier,
)
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteMeta
from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext
from lantern.stores.base import SelectRecordsProtocol


class TestVerificationExporterChecks:
    """Test Verification standalone URL check methods."""

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("url", "context", "expected"),
        [
            pytest.param(
                "https://example.com",
                {"BASE_URL": "https://data.bas.ac.uk", "SHAREPOINT_PROXY_ENDPOINT": "x"},
                VerificationResult.PENDING,  # not failed
                id="default",
            ),
            pytest.param(
                "https://example.com/unknown",
                {"BASE_URL": "https://data.bas.ac.uk", "SHAREPOINT_PROXY_ENDPOINT": "x", "EXPECTED_STATUS": 404},
                VerificationResult.PENDING,  # not failed
                id="expected_status",
            ),
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "EXPECTED_LENGTH": 1,
                },
                VerificationResult.PENDING,  # not failed
                id="expected_length",
            ),
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "METHOD": "get",
                },
                VerificationResult.PENDING,  # not failed
                id="method_get",
            ),
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "METHOD": "post",
                    "JSON": {"path": "/x"},
                },
                VerificationResult.PENDING,  # not failed
                id="method_post",
            ),
            pytest.param(
                "https://example.com",
                {"BASE_URL": "https://data.bas.ac.uk", "SHAREPOINT_PROXY_ENDPOINT": "x"},
                VerificationResult.FAIL,
                id="unexpected_status",
            ),
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "EXPECTED_LENGTH": 100,
                },
                VerificationResult.FAIL,
                id="unexpected_length",
            ),
        ],
    )
    def test_req_url(
        self, fx_logger: logging.Logger, url: str, context: VerificationContext, expected: VerificationResult
    ):
        """Can make HTTP request."""
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url=url,
            context=context,
        )
        assert job.result == VerificationResult.PENDING
        result = _req_url(fx_logger, job)
        assert isinstance(result, Response)
        assert job.result == expected

    @pytest.mark.cov()
    def test_req_url_invalid_method(self, fx_logger: logging.Logger):
        """Cannot make HTTP request with unsupported method."""
        context: VerificationContext = {
            "BASE_URL": "https://data.bas.ac.uk",
            "SHAREPOINT_PROXY_ENDPOINT": "x",
            "SAN_PROXY_ENDPOINT": "x",
            "METHOD": "x",
        }
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url="https://example.com",
            context=context,
        )
        with pytest.raises(ValueError, match=r"Unsupported HTTP method: x"):
            _ = _req_url(fx_logger, job)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url(self, fx_logger: logging.Logger):
        """Can check a URL."""
        context: VerificationContext = {
            "BASE_URL": "https://data.bas.ac.uk",
            "SHAREPOINT_PROXY_ENDPOINT": "x",
            "SAN_PROXY_ENDPOINT": "x",
        }
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url="https://example.com",
            context=context,
        )
        assert job.result == VerificationResult.PENDING

        check_url(fx_logger, job)
        assert job.result == VerificationResult.PASS

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("url", "context", "expected"),
        [
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "TARGET": "https://example.com/redirected",
                },
                VerificationResult.PASS,
                id="ok",
            ),
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "TARGET": "https://example.com/redirected",
                },
                VerificationResult.FAIL,
                id="location_missing",
            ),
            pytest.param(
                "https://example.com",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "TARGET": "https://example.com/redirected",
                },
                VerificationResult.FAIL,
                id="location_unexpected",
            ),
        ],
    )
    def test_check_url_redirect(
        self, fx_logger: logging.Logger, url: str, context: VerificationContext, expected: VerificationResult
    ):
        """Can check a redirect URL."""
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url=url,
            context=context,
        )
        assert job.result == VerificationResult.PENDING

        check_url_redirect(fx_logger, job)
        assert job.result == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("url", "context", "expected"),
        [
            pytest.param(
                "https://www.arcgis.com/sharing/rest/content/items/123?f=json",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                },
                VerificationResult.PASS,
                id="ok",
            ),
            pytest.param(
                "https://www.arcgis.com/sharing/rest/content/items/123?f=json",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                },
                VerificationResult.FAIL,
                id="error",
            ),
        ],
    )
    def test_check_url_arcgis(
        self, fx_logger: logging.Logger, url: str, context: VerificationContext, expected: VerificationResult
    ):
        """Can check an ArcGIS API URL."""
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url=url,
            context=context,
        )
        assert job.result == VerificationResult.PENDING

        check_url_arcgis(fx_logger, job)
        assert job.result == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("label", "url", "context", "expected"),
        [
            (
                "ok",
                "https://valid",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "URL": "https://data.bas.ac.uk/items/123/",
                },
                VerificationResult.PASS,
            ),
            (
                "error",
                "https://invalid",
                {
                    "BASE_URL": "https://data.bas.ac.uk",
                    "SHAREPOINT_PROXY_ENDPOINT": "x",
                    "URL": "https://data.bas.ac.uk/items/123/",
                },
                VerificationResult.FAIL,
            ),
        ],
    )
    def test_check_item_download(
        self,
        fx_logger: logging.Logger,
        label: str,
        url: str,
        context: VerificationContext,
        expected: VerificationResult,
    ):
        """Can check a download URL on an item page."""
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url=url,
            context=context,
        )
        assert job.result == VerificationResult.PENDING

        check_item_download(fx_logger, job)
        assert job.result == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_run_job(self, fx_logger: logging.Logger):
        """Can run job with relevant check function."""
        job = VerificationJob(
            type=VerificationType.ITEM_PAGES,
            url="https://example.com",
            context={"BASE_URL": "https://example.com", "SHAREPOINT_PROXY_ENDPOINT": "x", "SAN_PROXY_ENDPOINT": "x"},
        )
        assert job.result == VerificationResult.PENDING

        _ = run_job(fx_logger.level, job)
        assert job.result == VerificationResult.PASS
        assert job.data["duration"].microseconds > 0

    @pytest.mark.cov()
    def test_run_job_complete(self, fx_logger: logging.Logger):
        """Cannot run job that isn't pending."""
        job = VerificationJob(
            result=VerificationResult.PASS,
            type=VerificationType.ITEM_PAGES,
            url="https://example.com",
            context={"BASE_URL": "https://example.com", "SHAREPOINT_PROXY_ENDPOINT": "x", "SAN_PROXY_ENDPOINT": "x"},
        )

        _ = run_job(fx_logger.level, job)
        assert job.result == VerificationResult.PASS
        assert "duration" not in job.data


class TestVerificationReport:
    """Test Verification report."""

    def test_init(self, fx_site_meta: SiteMeta):
        """Can instantiate report."""
        context: VerificationContext = {
            "BASE_URL": "https://data.bas.ac.uk",
            "SHAREPOINT_PROXY_ENDPOINT": "x",
            "SAN_PROXY_ENDPOINT": "x",
        }
        jobs = [
            VerificationJob(
                result=VerificationResult.PASS,
                type=VerificationType.SITE_PAGES,
                url="https://data.bas.ac.uk/-/index",
                context=context,
                data={"duration": timedelta(microseconds=1)},
            ),
            VerificationJob(
                result=VerificationResult.PASS,
                type=VerificationType.ITEM_PAGES,
                url="https://data.bas.ac.uk/items/123",
                context=context,
                data={"file_identifier": "x", "duration": timedelta(microseconds=1)},
            ),
        ]

        report = VerificationReport(meta=fx_site_meta, jobs=jobs, context=context)
        assert isinstance(report._created, datetime)
        assert report._duration.microseconds == 2
        assert len(report._site_jobs) > 0
        assert len(report._resource_jobs) > 0
        assert report._result == VerificationResult.PASS
        assert report._summary == {
            VerificationResult.PENDING: 0,
            VerificationResult.SKIP: 0,
            VerificationResult.PASS: len(jobs),
            VerificationResult.FAIL: 0,
        }

    def test_failed(self, fx_site_meta: SiteMeta):
        """
        Any failed jobs are reflected in report.

        Second job for same record added for coverage.
        """
        context: VerificationContext = {
            "BASE_URL": "https://data.bas.ac.uk",
            "SHAREPOINT_PROXY_ENDPOINT": "x",
            "SAN_PROXY_ENDPOINT": "x",
        }
        jobs = [
            VerificationJob(
                result=VerificationResult.PASS,
                type=VerificationType.SITE_PAGES,
                url="https://data.bas.ac.uk/-/index",
                context=context,
                data={"duration": timedelta(microseconds=1)},
            ),
            VerificationJob(
                result=VerificationResult.FAIL,
                type=VerificationType.ITEM_PAGES,
                url="https://data.bas.ac.uk/items/123",
                context=context,
                data={"file_identifier": "x", "duration": timedelta(microseconds=1)},
            ),
            VerificationJob(
                result=VerificationResult.FAIL,
                type=VerificationType.RECORD_PAGES_XML,
                url="https://data.bas.ac.uk/records/123.xml",
                context=context,
                data={"file_identifier": "x", "duration": timedelta(microseconds=1)},
            ),
        ]

        report = VerificationReport(meta=fx_site_meta, jobs=jobs, context=context)
        assert report._result == VerificationResult.FAIL
        assert report._summary == {
            VerificationResult.PENDING: 0,
            VerificationResult.SKIP: 0,
            VerificationResult.PASS: 1,
            VerificationResult.FAIL: 2,
        }

    def test_data(self, fx_exporter_verify_post_run: VerificationExporter):
        """Can get report data."""
        report = fx_exporter_verify_post_run.report
        result = report.data
        assert isinstance(result, dict)
        assert result["pass_fail"] is True
        assert isinstance(result["time"], str)
        assert "-" not in result["stats"]
        assert isinstance(json.dumps(result), str)  # JSON safe types
        assert "context" not in result["site_checks"][0]  # context not shown in output

    @pytest.mark.cov()
    def test_data_no_commit(self, fx_exporter_verify_post_run: VerificationExporter):
        """Can get report data without commit in context."""
        fx_exporter_verify_post_run._meta.build_repo_ref = None
        fx_exporter_verify_post_run._meta.build_repo_base_url = None

        report = fx_exporter_verify_post_run.report
        result = report.data
        assert isinstance(result, dict)
        assert result["commit"] is None

    def test_dumps(self, fx_exporter_verify_post_run: VerificationExporter):
        """Can get report data as HTML."""
        commit = "abc123"
        fx_exporter_verify_post_run._meta.build_repo_ref = commit
        fx_exporter_verify_post_run._meta.build_repo_base_url = "x"
        report = fx_exporter_verify_post_run.report
        result = report.dumps()
        assert isinstance(result, str)
        assert "All tests passed" in result
        assert commit in result


class TestVerificationExporter:
    """Test Verification exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_select_records: SelectRecordsProtocol):
        """Can instantiate exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")
        context: VerificationContext = {
            "BASE_URL": meta.base_url,
            "SHAREPOINT_PROXY_ENDPOINT": "x",
            "SAN_PROXY_ENDPOINT": "x",
        }

        exporter = VerificationExporter(
            logger=fx_logger, meta=meta, s3=s3_client, select_records=fx_select_records, context=context
        )

        assert isinstance(exporter, VerificationExporter)
        assert exporter.name == "Verification"

    def test_jobs(self, fx_exporter_verify_sel: VerificationExporter):
        """Can generate jobs for site and selected records."""
        fx_exporter_verify_sel._init_jobs()
        results = fx_exporter_verify_sel._jobs
        assert len(results) == 11

        for path in ["404", "/legal/privacy", "/-/formatting"]:  # representative sample
            site_page_job = next(
                (
                    result
                    for result in results
                    if result.type == VerificationType.SITE_PAGES and result.data["path"] == path
                ),
                None,
            )
            assert site_page_job is not None
        record_job = next((result for result in results if result.type == VerificationType.RECORD_PAGES_XML), None)
        item_job = next((result for result in results if result.type == VerificationType.ITEM_PAGES), None)
        assert record_job is not None
        assert item_job is not None

    @pytest.mark.cov()
    def test_jobs_404_local(self, fx_exporter_verify_sel: VerificationExporter):
        """Skips 404 job when using localhost."""
        fx_exporter_verify_sel._context["BASE_URL"] = "http://localhost"
        not_found_job = fx_exporter_verify_sel._404_job
        assert not_found_job.result == VerificationResult.SKIP

    @pytest.mark.cov()
    def test_jobs_aliases_local(
        self, mocker: MockerFixture, fx_revision_model_min: RecordRevision, fx_exporter_verify_sel: VerificationExporter
    ):
        """Skips aliases jobs when using localhost."""
        fx_exporter_verify_sel._context["BASE_URL"] = "http://localhost"
        fx_revision_model_min.identification.identifiers.append(
            Identifier(identifier="x/x", href=f"https://{CATALOGUE_NAMESPACE}/x/x", namespace=ALIAS_NAMESPACE)
        )
        fx_exporter_verify_sel._select_records = mocker.MagicMock(return_value=[fx_revision_model_min])

        results = fx_exporter_verify_sel._record_jobs
        alias_job = next((result for result in results if result.type == VerificationType.ALIAS_REDIRECTS), None)
        assert alias_job.result == VerificationResult.SKIP

    @pytest.mark.cov()
    def test_jobs_doi_other(
        self, mocker: MockerFixture, fx_revision_model_min: RecordRevision, fx_exporter_verify_sel: VerificationExporter
    ):
        """Skips DOI jobs when not using production domain."""
        fx_exporter_verify_sel._context["BASE_URL"] = "http://localhost"
        fx_revision_model_min.identification.identifiers.append(
            Identifier(identifier="x/x", href="https://doi.org/x/x", namespace="doi")
        )
        fx_exporter_verify_sel._select_records = mocker.MagicMock(return_value=[fx_revision_model_min])

        results = fx_exporter_verify_sel._record_jobs
        alias_job = next((result for result in results if result.type == VerificationType.DOI_REDIRECTS), None)
        assert alias_job.result == VerificationResult.SKIP

    @pytest.mark.cov()
    def test_jobs_doi_ok(
        self, mocker: MockerFixture, fx_revision_model_min: RecordRevision, fx_exporter_verify_sel: VerificationExporter
    ):
        """Can get DOI jobs when using production domain."""
        fx_exporter_verify_sel._context["BASE_URL"] = f"https://{CATALOGUE_NAMESPACE}"
        fx_revision_model_min.identification.identifiers.append(
            Identifier(identifier="x/x", href="https://doi.org/x/x", namespace="doi")
        )
        fx_exporter_verify_sel._select_records = mocker.MagicMock(return_value=[fx_revision_model_min])

        results = fx_exporter_verify_sel._record_jobs
        alias_job = next((result for result in results if result.type == VerificationType.DOI_REDIRECTS), None)
        assert alias_job.result == VerificationResult.PENDING

    def test_report(self, fx_exporter_verify_post_run: VerificationExporter):
        """Can generate jobs for site and selected records."""
        report = fx_exporter_verify_post_run.report
        assert isinstance(report, VerificationReport)
        assert report._result == VerificationResult.PASS

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_run(self, fx_exporter_verify_sel: VerificationExporter):
        """Can execute generated jobs."""
        assert len(fx_exporter_verify_sel._jobs) == 0
        fx_exporter_verify_sel.run()
        jobs = fx_exporter_verify_sel._jobs
        assert len(jobs) > 0
        # assert all jobs are not pending (i.e. at least some have run)
        assert all(job.result != VerificationResult.PENDING for job in jobs)

    def test_export(self, fx_exporter_verify_post_run: VerificationExporter):
        """Can export report files to local files."""
        base_path = fx_exporter_verify_post_run._export_path
        data_path = base_path / "data.json"
        report_path = base_path / "index.html"

        fx_exporter_verify_post_run.export()
        assert data_path.exists()
        assert report_path.exists()

    def test_publish(self, fx_exporter_verify_post_run: VerificationExporter, fx_s3_bucket_name: str):
        """Can publish report files to S3."""
        data_key = "-/verification/data.json"
        report_key = "-/verification/index.html"

        fx_exporter_verify_post_run.publish()

        data_output = fx_exporter_verify_post_run._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=data_key,
        )
        report_output = fx_exporter_verify_post_run._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=report_key,
        )
        assert data_output["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert report_output["ResponseMetadata"]["HTTPStatusCode"] == 200
