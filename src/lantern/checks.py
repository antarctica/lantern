import json
import logging
import time
from http import HTTPMethod, HTTPStatus

import requests
from joblib import Parallel, delayed
from requests import Response

from lantern.log import init as init_logging
from lantern.models.checks import Check, CheckState, CheckType
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.checks import ChecksOutput


class CheckRunner:
    """
    Check Runner.

    Logic to execute and update a check.
    """

    def __init__(self, logger: logging.Logger, check: Check) -> None:
        self._logger = logger
        self._check = check

    def _fetch_url(
        self,
        method: HTTPMethod,
        url: str,
        headers: dict | None = None,
        redirects: bool = False,
        raise_errors: bool = False,
    ) -> Response | None:
        """
        Common method for checking a URL.

        Handles time out errors only.
        """
        s = requests.Session()
        s.max_redirects = 1

        if headers is None:
            headers = {}

        try:
            r = s.request(method=method.value, url=url, headers=headers, allow_redirects=redirects, timeout=10)
            if raise_errors:
                r.raise_for_status()
        except requests.Timeout:
            self._check.state = CheckState.FAILED
            self._check.result_output = "Request timed out"
        except requests.TooManyRedirects:
            self._check.state = CheckState.FAILED
            self._check.result_output = "Multiple redirects"
        else:
            self._logger.debug(r.headers)
            self._check.result_http_status = HTTPStatus(r.status_code)
            return r
        finally:
            s.close()

    def _check_url(self) -> None:
        """
        Check URL as per check properties.

        Validates the response status code and optionally, content length and/or location header (for redirects).
        """
        self._logger.info(f"Fetching: {self._check.url}")
        self._logger.debug({"method": self._check.http_method, "url": self._check.url})

        headers = None
        if self._check.type == CheckType.DOWNLOADS_NORA:
            # NORA does not support HEAD requests but does support ranges to avoid full downloads
            headers = {"Range": "bytes=0-253"}

        r = self._fetch_url(
            method=self._check.http_method,
            url=self._check.url,
            headers=headers,
            redirects=False,
            raise_errors=False,
        )
        if r is None:
            return

        if self._check.result_http_status != self._check.http_status:
            self._check.state = CheckState.FAILED
            self._check.result_output = (
                f"Bad status: {self._check.result_http_status} (expected {self._check.http_status})"
            )
            return

        content_length = int(r.headers.get("content-length", 0))
        if (
            self._check.content_length is not None
            and self._check.http_status != HTTPStatus.PARTIAL_CONTENT
            and content_length != self._check.content_length
        ):
            self._check.state = CheckState.FAILED
            self._check.result_output = f"Bad content length: {content_length} (expected {self._check.content_length})"
            return

        location = r.headers.get("location", None)
        if not self._check.redirect_location:
            self._check.state = CheckState.PASS
            self._check.result_output = "OK"
            return

        if location != self._check.redirect_location:
            self._check.state = CheckState.FAILED
            self._check.result_output = f"Bad location: {location} (expected {self._check.redirect_location})"
            return

        # Follow redirect
        r2 = self._fetch_url(method=self._check.http_method, url=self._check.url, redirects=True, raise_errors=True)
        if r2 is None:
            return

        self._check.state = CheckState.PASS
        self._check.result_output = "OK"

    def _check_arcgis_url(self, url: str) -> None:
        """
        Common method for checking ArcGIS resources.

        Limited to public items.

        Uses a GET request as Arc APIs return 200 responses for errors.
        """
        self._check.http_method = HTTPMethod.GET

        r = self._fetch_url(method=self._check.http_method, url=url, raise_errors=True)
        if r is None:
            return

        if "error" in r.json():
            self._check.state = CheckState.FAILED
            self._check.result_output = json.dumps(r.json())
            return

        self._check.state = CheckState.PASS
        self._check.result_output = "OK"

    def _check_arcgis_item(self) -> None:
        """
        Check ArcGIS item using ArcGIS sharing API.

        API lookup used over loading item page directly for speed and robustness. Limited to public items.
        """
        item_id = self._check.url.split("id=")[-1]
        item_url = f"https://www.arcgis.com/sharing/rest/content/items/{item_id}?f=json"
        self._logger.info(f"Checking ArcGIS item page: {self._check.url}")
        self._logger.info(f"Fetching from ArcGIS sharing API: {item_url}")
        self._check_arcgis_url(item_url)

    def _check_arcgis_service(self) -> None:
        """
        Check ArcGIS service.

        Checks service endpoint directly. Limited to public items.
        """
        service_url = f"{self._check.url}?f=json"
        self._logger.info(f"Fetching: {service_url}")
        self._check_arcgis_url(service_url)

    def run(self) -> None:
        """Run check unless skipped."""
        if self._check.state == CheckState.SKIPPED:
            return

        start = time.monotonic()
        if self._check.type == CheckType.DOWNLOADS_ARCGIS_LAYER:
            self._check_arcgis_item()
        elif self._check.type == CheckType.DOWNLOADS_ARCGIS_SERVICE:
            self._check_arcgis_service()
        else:
            self._check_url()
        self._check.duration = time.monotonic() - start


def run_check(logging_level: int, check: Check) -> Check:
    """
    Run a check job.

    Standalone function for use in parallel processing.
    """
    init_logging(logging_level)  # each process needs logging initialising
    logger = logging.getLogger("app")
    runner = CheckRunner(logger, check)
    runner.run()
    return check


class Checker:
    """
    Checks runner.

    Executes a set of checks for site/resource content in parallel.

    Flexible class intended to be used in a higher level and opinionated Catalogue class.
    """

    def __init__(self, logger: logging.Logger, parallel_jobs: int) -> None:
        self._logger = logger
        self._parallel_jobs = parallel_jobs

    def execute(self, checks: list[Check]) -> list[Check]:
        """
        Run checks in parallel.

        Returns executed checks.
        """
        return Parallel(n_jobs=self._parallel_jobs)(delayed(run_check)(self._logger.level, check) for check in checks)

    def check(self, meta: ExportMeta, checks: list[Check]) -> list[SiteContent]:
        """
        Run checks.

        Returns report outputs for export. Use `execute()` to return raw checks.
        """
        results = self.execute(checks)
        return ChecksOutput(logger=self._logger, meta=meta, checks=results).content
