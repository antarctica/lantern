import logging
from http import HTTPStatus
from pathlib import Path

import pytest

from lantern.models.checks import Check, CheckState, CheckType
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.checks import ChecksOutput


class TestChecksOutput:
    """Test checks report output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check):
        """Can create a checks output."""
        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=[fx_check])
        assert isinstance(output, ChecksOutput)

    @pytest.mark.cov()
    @pytest.mark.parametrize("build_ref", [True, False])
    def test_object_meta(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check, build_ref: bool):
        """Can get object metadata if build_ref is available."""
        if not build_ref:
            fx_export_meta.build_repo_ref = None
        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=[fx_check])
        object_meta = output._object_meta
        if build_ref:
            assert "build_ref" in object_meta
        else:
            assert "build_ref" not in object_meta

    @pytest.mark.parametrize(
        ("checks", "exp_duration", "exp_pass", "exp_stats"),
        [
            (
                [
                    Check(
                        type=CheckType.SITE_HEALTH,
                        url="x",
                        state=CheckState.PASS,
                        duration=0.1,
                        result_http_status=HTTPStatus.OK,
                        result_output="OK",
                    ),
                    Check(
                        type=CheckType.ITEM_PAGES,
                        url="x",
                        file_identifier="x",
                        state=CheckState.PASS,
                        duration=0.1,
                        result_http_status=HTTPStatus.OK,
                        result_output="OK",
                    ),
                ],
                0.2,
                True,
                {CheckState.PENDING: 0, CheckState.SKIPPED: 0, CheckState.PASS: 2, CheckState.FAILED: 0},
            ),
            (
                [
                    Check(
                        type=CheckType.SITE_HEALTH,
                        url="x",
                        state=CheckState.PASS,
                        duration=0.1,
                        result_http_status=HTTPStatus.OK,
                        result_output="OK",
                    ),
                    Check(
                        type=CheckType.RECORD_PAGES_XML,
                        url="x",
                        file_identifier="x",
                        state=CheckState.FAILED,
                        duration=0.1,
                        result_http_status=HTTPStatus.NOT_FOUND,
                        result_output="Bad",
                    ),
                    Check(
                        type=CheckType.DOWNLOADS_SHAREPOINT,
                        url="x",
                        file_identifier="x",
                        state=CheckState.SKIPPED,
                        duration=0.0,
                    ),
                    Check(
                        type=CheckType.ITEM_ALIASES,
                        url="x",
                        file_identifier="x",
                        state=CheckState.PENDING,
                        duration=0.0,
                    ),
                ],
                0.2,
                False,
                {CheckState.PENDING: 1, CheckState.SKIPPED: 1, CheckState.PASS: 1, CheckState.FAILED: 1},
            ),
        ],
    )
    def test_process(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        checks: list[Check],
        exp_duration: float,
        exp_pass: bool,
        exp_stats: dict,
    ):
        """
        Can process checks.

        Test cases must have at least one site and resource check.
        """
        expected_site_checks = checks[:1]
        expected_resource_checks = {"x": checks[1:]}

        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=checks)
        duration, pass_fail, stats, site_checks, resource_checks = output._process()
        assert round(duration, 2) == exp_duration
        assert pass_fail == exp_pass
        assert stats == exp_stats
        assert site_checks == expected_site_checks
        assert resource_checks == expected_resource_checks

    @pytest.mark.parametrize("build_ref", [True, False])
    def test_data(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, build_ref: bool):
        """Can unstructure processed checks into simple types."""
        checks = [
            Check(
                type=CheckType.SITE_HEALTH,
                url="x",
                state=CheckState.PASS,
                duration=0.1,
                result_http_status=HTTPStatus.OK,
                result_output="OK",
            ),
            Check(
                type=CheckType.RECORD_PAGES_XML,
                url="x",
                file_identifier="x",
                state=CheckState.FAILED,
                duration=0.1,
                result_http_status=HTTPStatus.NOT_FOUND,
                result_output="Bad",
            ),
            Check(
                type=CheckType.DOWNLOADS_SHAREPOINT,
                url="x",
                file_identifier="x",
                state=CheckState.SKIPPED,
                duration=0.0,
            ),
        ]
        if not build_ref:
            fx_export_meta.build_repo_ref = None
            fx_export_meta.build_repo_url = None
        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=checks)

        results = output._data
        assert isinstance(results, dict)
        assert isinstance(results["time"], str)
        assert results["stats"] == {"passed": 1, "failed": 1, "skipped": 1}
        if build_ref:
            assert results["commit"] == {
                "href": "https://example.com/-/commit/83fake48",
                "value": "83fake48",
            }
        else:
            assert results["commit"] is None
        assert isinstance(results["site_checks"], list)
        assert results["site_checks"][0]["state"] == "passed"
        assert isinstance(results["resource_checks"], dict)
        assert results["resource_checks"]["x"][0]["state"] == "failed"
        assert results["resource_checks"]["x"][1]["state"] == "skipped"

    def test_report(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check):
        """Can unstructure processed checks into simple types."""
        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=[fx_check])
        results = output._report
        assert "<!DOCTYPE html>" in results

    def test_content(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check):
        """Can generate site content items."""
        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=[fx_check])
        results = output.content
        assert len(results) == 2

        data = results[0]
        assert isinstance(data, SiteContent)
        assert "pass_fail" in data.content
        assert data.path == Path("-/checks/data.json")
        assert data.media_type == "application/json"

        report = results[1]
        assert isinstance(report, SiteContent)
        assert "<!DOCTYPE html>" in report.content
        assert report.path == Path("-/checks/index.html")
        assert report.media_type == "text/html"

    @pytest.mark.cov()
    def test_checks(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check):
        """Can get empty checks as not applicable."""
        output = ChecksOutput(logger=fx_logger, meta=fx_export_meta, checks=[fx_check])
        assert len(output.checks) == 0
