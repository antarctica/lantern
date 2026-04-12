import logging
import time
from http import HTTPMethod, HTTPStatus

import pytest
import requests
from pytest_mock import MockerFixture

from lantern.checks import Checker, CheckRunner, run_check
from lantern.models.checks import Check, CheckState, CheckType
from lantern.models.site import ExportMeta, SiteContent


class TestCheckRunner:
    """Test check runner."""

    def test_init(self, fx_logger: logging.Logger, fx_check: Check) -> None:
        """Can create a CheckRunner instance."""
        runner = CheckRunner(logger=fx_logger, check=fx_check)
        assert isinstance(runner, CheckRunner)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL normally."""
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.result_http_status == fx_check.http_status
        assert fx_check.state == CheckState.PASS

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url_redirect(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL for an expected redirect."""
        fx_check.http_status = HTTPStatus.MOVED_PERMANENTLY
        fx_check.url = "https://example.com/redirect.html"
        fx_check.redirect_location = "https://example.com/index.html"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.state == CheckState.PASS
        assert fx_check.result_output == "OK"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url_nora(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a NORA hosted file using a partial range request."""
        fx_check.type = CheckType.DOWNLOADS_NORA
        fx_check.http_method = HTTPMethod.GET
        fx_check.http_status = HTTPStatus.PARTIAL_CONTENT
        fx_check.content_length = 1439443
        fx_check.url = "https://nora.nerc.ac.uk/id/eprint/123/x.pdf"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.state == CheckState.PASS

    def test_check_url_timeout(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL that times out."""
        mocker.patch.object(requests.Session, "request", side_effect=requests.Timeout)
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Request timed out"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url_wrong_status(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL that returns the wrong status."""
        expected_status = HTTPStatus.INTERNAL_SERVER_ERROR
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_http_status == expected_status
        assert fx_check.result_output == "Bad status: 500 (expected 200)"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url_wrong_length(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL that returns the wrong content length."""
        fx_check.content_length = 20
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Bad content length: 10 (expected 20)"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url_wrong_redirect(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL that returns an unexpected redirect location."""
        fx_check.http_status = HTTPStatus.MOVED_PERMANENTLY
        fx_check.url = "https://example.com/redirect.html"
        fx_check.redirect_location = "https://example.com/index.html"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_url()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Bad location: https://invalid (expected https://example.com/index.html)"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_url_multiple_redirects(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL that results in too many redirects."""
        fx_check.http_status = HTTPStatus.MOVED_PERMANENTLY
        fx_check.url = "https://example.com/redirect.html"
        fx_check.redirect_location = "https://example.com/index.html"
        runner = CheckRunner(logger=fx_logger, check=fx_check)
        runner._check_url()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Multiple redirects"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_arc_item(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check an ArcGIS item normally."""
        fx_check.type = CheckType.DOWNLOADS_ARCGIS_LAYER
        fx_check.url = "https://www.arcgis.com/home/item.html?id=123"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_item()
        assert fx_check.state == CheckState.PASS

    @pytest.mark.cov
    def test_check_arc_item_timeout(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check):
        """Check any errors set by fetch_url are handled correctly."""
        mocker.patch.object(requests.Session, "request", side_effect=requests.Timeout)
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_item()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Request timed out"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_arc_item_error(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check an ArcGIS item that triggers an error."""
        fx_check.type = CheckType.DOWNLOADS_ARCGIS_LAYER
        fx_check.url = "https://www.arcgis.com/home/item.html?id=123"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_item()
        assert fx_check.state == CheckState.FAILED

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        "url",
        [
            "https://services.arcgis.com/x/arcgis/rest/services/x/FeatureServer",
            "https://utility.arcgis.com/usrsvcs/servers/x/rest/services/x/FeatureServer",
        ],
    )
    def test_check_arc_service(self, fx_logger: logging.Logger, fx_check: Check, url: str):
        """Can check an ArcGIS service normally."""
        fx_check.type = CheckType.DOWNLOADS_ARCGIS_SERVICE
        fx_check.url = url
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_service()
        assert fx_check.state == CheckState.PASS

    @pytest.mark.cov
    def test_check_arc_service_timeout(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check):
        """Check any errors set by fetch_url are handled correctly."""
        mocker.patch.object(requests.Session, "request", side_effect=requests.Timeout)
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_service()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Request timed out"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_arc_service_error(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check an ArcGIS layer that triggers an error."""
        fx_check.type = CheckType.DOWNLOADS_ARCGIS_SERVICE
        fx_check.url = "https://services.arcgis.com/arcgis/rest/services/x/featureserver"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_service()
        assert fx_check.state == CheckState.FAILED

    @pytest.mark.parametrize("skipped", [False, True])
    def test_run(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check, skipped: bool) -> None:
        """Can run a check and measure its duration."""
        if skipped:
            fx_check.state = CheckState.SKIPPED
        runner = CheckRunner(logger=fx_logger, check=fx_check)
        mocker.patch.object(runner, "_check_url", side_effect=lambda: time.sleep(0.01))

        runner.run()
        if not skipped:
            assert fx_check.duration > 0
        else:
            assert fx_check.duration == 0


@pytest.mark.cov()
class TestRunCheck:
    """Test standalone check runner."""

    @pytest.mark.parametrize(
        "check_type", [CheckType.DOWNLOADS_OPEN, CheckType.DOWNLOADS_ARCGIS_LAYER, CheckType.DOWNLOADS_ARCGIS_SERVICE]
    )
    def test_run(
        self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check, check_type: CheckType
    ) -> None:
        """Can run a CheckRunner with the correct check method."""
        mocker.patch.object(CheckRunner, "_check_url", return_value=None)
        mocker.patch.object(CheckRunner, "_check_arcgis_item", side_effect=RuntimeError)
        mocker.patch.object(CheckRunner, "_check_arcgis_service", side_effect=RuntimeError)
        if check_type == CheckType.DOWNLOADS_ARCGIS_LAYER:
            mocker.patch.object(CheckRunner, "_check_url", side_effect=RuntimeError)
            mocker.patch.object(CheckRunner, "_check_arcgis_item", return_value=None)
        elif check_type == CheckType.DOWNLOADS_ARCGIS_SERVICE:
            mocker.patch.object(CheckRunner, "_check_url", side_effect=RuntimeError)
            mocker.patch.object(CheckRunner, "_check_arcgis_service", return_value=None)

        fx_check.type = check_type
        result = run_check(fx_logger.level, fx_check)
        assert result == fx_check


class TestChecker:
    """Test checks runner."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta) -> None:
        """Can create a Checker instance."""
        runner = Checker(logger=fx_logger, meta=fx_export_meta)
        assert isinstance(runner, Checker)

    def test_execute(
        self, mocker: MockerFixture, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check
    ) -> None:
        """
        Can run checks.

        Check methods are disabled to avoid making real requests.
        """
        mocker.patch.object(CheckRunner, "run", return_value=None)
        checker = Checker(logger=fx_logger, meta=fx_export_meta)

        checks = checker.execute([fx_check])
        assert checks == [fx_check]  # checks will remain as initial

    def test_checks(
        self, mocker: MockerFixture, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_check: Check
    ) -> None:
        """
        Can run checks and get output.

        Check methods are disabled to avoid making real requests.
        """
        mocker.patch.object(CheckRunner, "run", return_value=None)
        checker = Checker(logger=fx_logger, meta=fx_export_meta)

        outputs = checker.check([fx_check])
        assert all(isinstance(o, SiteContent) for o in outputs)
