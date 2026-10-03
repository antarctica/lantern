import time
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING

import pytest
import requests
from requests.auth import AuthBase, HTTPBasicAuth

from lantern.checks import Checker, CheckRunner, run_check
from lantern.models.checks import Check, CheckState, CheckType
from lantern.models.site import ExportMeta, SiteContent

if TYPE_CHECKING:
    import logging

    from pytest_mock import MockerFixture

    from lantern.config import Config
    from lantern.lib.magic_distribution.models.artefact import ArtefactSharePointFile


class TestCheckRunner:
    """Test check runner."""

    def test_init(self, fx_logger: logging.Logger, fx_check: Check) -> None:
        """Can create a CheckRunner instance."""
        runner = CheckRunner(logger=fx_logger, check=fx_check)
        assert isinstance(runner, CheckRunner)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("access_url", [None, "https://example.com/alt.html"])
    def test_check_url(self, fx_logger: logging.Logger, fx_check: Check, access_url: str | None):
        """Can check an (access) URL normally."""
        if access_url:
            fx_check.access_url = access_url
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
    def test_check_url_auth(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check a URL with basic auth."""
        fx_check.url = "https://example.com/restricted.html"
        fx_check.http_auth = HTTPBasicAuth(username="x", password="x")  # noqa: S106
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
        assert fx_check.result_output == "Exceeds allowed redirects"

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("check_type", "url", "access_url"),
        [
            (
                CheckType.INFO_ARCGIS_LAYER,
                "https://www.arcgis.com/home/item.html?id=123",
                "https://www.arcgis.com/sharing/rest/content/items/123?f=json",
            ),
            (
                CheckType.DOWNLOADS_ARCGIS_SERVICE,
                "https://services.arcgis.com/x/arcgis/rest/services/x/FeatureServer",
                "https://services.arcgis.com/x/arcgis/rest/services/x/FeatureServer?f=json",
            ),
            (
                CheckType.DOWNLOADS_ARCGIS_SERVICE,
                "https://utility.arcgis.com/usrsvcs/servers/x/rest/services/x/FeatureServer",
                "https://utility.arcgis.com/usrsvcs/servers/x/rest/services/x/FeatureServer?f=json",
            ),
        ],
    )
    def test_check_arc_api(
        self, fx_logger: logging.Logger, fx_check: Check, check_type: CheckType, url: str, access_url: str
    ):
        """Can check an ArcGIS API resource normally."""
        fx_check.type = check_type
        fx_check.url = url
        fx_check.access_url = access_url

        runner = CheckRunner(logger=fx_logger, check=fx_check)
        runner._check_arcgis_api()
        assert fx_check.state == CheckState.PASS

    @pytest.mark.cov
    def test_check_arc_api_timeout(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check):
        """Can handle a ArcGIS API resource that times out correctly."""
        mocker.patch.object(requests.Session, "request", side_effect=requests.Timeout)
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_api()
        assert fx_check.state == CheckState.FAILED
        assert fx_check.result_output == "Request timed out"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_check_arc_api_error(self, fx_logger: logging.Logger, fx_check: Check):
        """Can check an ArcGIS API resource that triggers an error."""
        fx_check.type = CheckType.DOWNLOADS_ARCGIS_SERVICE
        fx_check.url = "https://services.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
        fx_check.access_url = f"{fx_check.url}?f=json"
        runner = CheckRunner(logger=fx_logger, check=fx_check)

        runner._check_arcgis_api()
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
        "check_type",
        [
            CheckType.DOWNLOADS_OPEN,
            CheckType.INFO_ARCGIS_LAYER,
            CheckType.DOWNLOADS_ARCGIS_SERVICE,
            CheckType.INFO_ARCGIS_WEBMAP,
        ],
    )
    def test_run(
        self, mocker: MockerFixture, fx_logger: logging.Logger, fx_check: Check, check_type: CheckType
    ) -> None:
        """Can run a CheckRunner with the correct check method."""
        mocker.patch.object(CheckRunner, "_check_url", return_value=None)
        mocker.patch.object(CheckRunner, "_check_arcgis_api", side_effect=RuntimeError)
        if check_type in (
            CheckType.INFO_ARCGIS_LAYER,
            CheckType.INFO_ARCGIS_WEBMAP,
            CheckType.DOWNLOADS_ARCGIS_SERVICE,
        ):
            mocker.patch.object(CheckRunner, "_check_url", side_effect=RuntimeError)
            mocker.patch.object(CheckRunner, "_check_arcgis_api", return_value=None)

        fx_check.type = check_type
        result = run_check(fx_logger.level, fx_check)
        assert result == fx_check


class TestChecker:
    """Test checks runner."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config) -> None:
        """Can create a Checker instance."""
        runner = Checker(logger=fx_logger, config=fx_config)
        assert isinstance(runner, Checker)

    @pytest.mark.parametrize(
        ("check_type", "expected_access_url", "expected_auth"),
        [
            (CheckType.NONE, None, None),
            (CheckType.ITEM_PAGES_TRUSTED, None, HTTPBasicAuth),
            (CheckType.DOWNLOADS_SHAREPOINT_MAGIC_RESOURCE, "x", None),
            (CheckType.INFO_ARCGIS_LAYER, "https://www.arcgis.com/sharing/rest/content/items/123?f=json", None),
            (
                CheckType.DOWNLOADS_ARCGIS_SERVICE,
                "https://services.arcgis.com/x/arcgis/rest/services/x/FeatureServer?f=json",
                None,
            ),
        ],
    )
    def test_prepare_checks(
        self,
        mocker: MockerFixture,
        fx_checker: Checker,
        fx_check: Check,
        fx_lib_artefact_sharepoint: ArtefactSharePointFile,
        check_type: CheckType,
        expected_access_url: str | None,
        expected_auth: AuthBase | None,
    ):
        """
        Can prepare checks for selected resource distribution options.

        E.g. access URL or auth class is set.
        """
        fx_check.type = check_type
        if check_type == CheckType.DOWNLOADS_SHAREPOINT_MAGIC_RESOURCE:
            mocker.patch(
                "lantern.checks.MagicResourceDistributionClient.lookup_artefact",
                return_value=fx_lib_artefact_sharepoint,
            )
        if check_type == CheckType.INFO_ARCGIS_LAYER:
            fx_check.url = "https://www.arcgis.com/home/item.html?id=123"
        elif check_type == CheckType.DOWNLOADS_ARCGIS_SERVICE:
            fx_check.url = "https://services.arcgis.com/x/arcgis/rest/services/x/FeatureServer"
        checks = [fx_check]
        fx_checker._prepare_checks(checks=checks)

        if expected_access_url:
            assert checks[0].access_url == expected_access_url
            assert checks[0].access_url != checks[0].url
        else:
            assert checks[0].access_url is None
        if expected_auth:
            assert isinstance(checks[0].http_auth, expected_auth)
        else:
            assert checks[0].http_auth is None

    def test_execute(self, fx_checker: Checker, fx_check: Check) -> None:
        """
        Can run checks.

        Check methods are disabled to avoid making real requests.
        """
        checks = fx_checker.execute([fx_check])
        assert checks == [fx_check]  # checks will remain as initial as not actually run

    def test_checks(self, fx_checker: Checker, fx_export_meta: ExportMeta, fx_check: Check) -> None:
        """
        Can run checks and get output.

        Check methods are disabled to avoid making real requests.
        """
        outputs = fx_checker.check(meta=fx_export_meta, checks=[fx_check])
        assert all(isinstance(o, SiteContent) for o in outputs)
