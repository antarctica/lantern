import json
import logging
import time
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING

import requests
from joblib import Parallel, delayed
from requests import Response
from requests.auth import HTTPBasicAuth

from lantern.lib.magic_distribution.client import MagicResourceDistributionClient
from lantern.log import init as init_logging
from lantern.models.checks import Check, CheckState, CheckType
from lantern.outputs.checks import ChecksOutput

if TYPE_CHECKING:
    from requests.auth import AuthBase

    from lantern.config import Config
    from lantern.models.site import ExportMeta, SiteContent


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
        params: dict | None = None,
        redirects: int = 0,
        auth: AuthBase | None = None,
        raise_errors: bool = False,
    ) -> Response | None:
        """
        Common method for checking a URL.

        `redirects` is the maximum number of redirects allowed (where 0 is none).

        Otherise, handles time out errors only.
        """
        s = requests.Session()
        s.max_redirects = redirects if redirects > 0 else 1  # for requests that should redirect but not be followed

        if headers is None:
            headers = {}

        try:
            r = s.request(
                method=method.value,
                url=url,
                headers=headers,
                params=params,
                allow_redirects=redirects > 0,
                timeout=10,
                auth=auth,
            )
            if raise_errors:
                r.raise_for_status()
        except requests.Timeout:
            self._check.state = CheckState.FAILED
            self._check.result_output = "Request timed out"
        except requests.TooManyRedirects:
            self._check.state = CheckState.FAILED
            self._check.result_output = "Exceeds allowed redirects"
        else:
            self._logger.debug(r.headers)
            self._check.result_http_status = HTTPStatus(r.status_code)
            return r
        finally:
            s.close()

    def _check_url(self) -> None:
        """
        Check URL as per check properties or optional override.

        Validates the response status code and optionally, content length and/or location header (for redirects).
        """
        url = self._check.access_url or self._check.url
        self._logger.info("Fetching: %s", url)
        self._logger.debug({"method": self._check.http_method, "url": url})

        headers = None
        if self._check.type == CheckType.DOWNLOADS_NORA:
            # NORA does not support HEAD requests but does support ranges to avoid full downloads
            headers = {"Range": "bytes=0-253"}

        r = self._fetch_url(
            method=self._check.http_method,
            url=url,
            headers=headers,
            auth=self._check.http_auth,
            redirects=0,
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

        # Follow redirect(s if a DOI)
        r_max = 2 if self._check.type == CheckType.DOI_REDIRECTS else 1
        r2 = self._fetch_url(method=self._check.http_method, url=url, redirects=r_max, raise_errors=True)
        if r2 is None:
            return

        self._check.state = CheckState.PASS
        self._check.result_output = "OK"

    def _check_arcgis_api(self) -> None:
        """
        Common method for checking resources within ArcGIS APIs.

        Limited to public items.

        Uses a GET request as Arc APIs return 200 responses for errors.
        """
        url = self._check.access_url or self._check.url
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

    def run(self) -> None:
        """Run check unless skipped."""
        if self._check.state == CheckState.SKIPPED:
            return

        start = time.monotonic()
        if self._check.type in (
            CheckType.INFO_ARCGIS_LAYER,
            CheckType.INFO_ARCGIS_WEBMAP,
            CheckType.DOWNLOADS_ARCGIS_SERVICE,
        ):
            self._check_arcgis_api()
        else:
            self._check_url()
        self._check.duration = time.monotonic() - start


def run_check(logging_level: int, check: Check) -> Check:
    """
    Run a check job.

    Standalone function for use in parallel processing.
    """
    init_logging(logging_level)  # each process needs logging initialising
    logger = logging.getLogger("lantern")
    runner = CheckRunner(logger, check)
    runner.run()
    return check


class Checker:
    """
    Checks runner.

    Executes a set of checks for site/resource content in parallel.

    Flexible class intended to be used in a higher level and opinionated Catalogue class.
    """

    def __init__(self, logger: logging.Logger, config: Config) -> None:
        self._logger = logger
        self._config = config
        self._parallel_jobs = self._config.PARALLEL_JOBS

    def _prepare_checks(self, checks: list[Check]) -> None:
        """
        Post process checks prior to execution.

        E.g. To include authentication or construct an alternative access URL.
        """
        magic_resource_client = MagicResourceDistributionClient(
            tenant_id=self._config.CHECKS_MAGIC_RESOURCES_TENANT_ID,
            app_client_id=self._config.CHECKS_MAGIC_RESOURCES_CLIENT_ID,
            app_client_secret=self._config.CHECKS_MAGIC_RESOURCES_CLIENT_SECRET,
            site_id=self._config.CHECKS_MAGIC_RESOURCES_SITE_ID,
            library_name=self._config.CHECKS_MAGIC_RESOURCES_LIBRARY_NAME,
        )

        for check in checks:
            if check.type == CheckType.ITEM_PAGES_TRUSTED:
                # Add basic auth for accessing trusted publishing content (Ops Data Store LDAP)
                self._logger.info(
                    "[%s] Setting credentials for accessing trusted publishing page: %s",
                    check.file_identifier,
                    check.url,
                )
                check.http_auth = HTTPBasicAuth(
                    username=self._config.CHECKS_TRUSTED_USERNAME, password=self._config.CHECKS_TRUSTED_PASSWORD
                )
            elif check.type == CheckType.DOWNLOADS_SHAREPOINT_MAGIC_RESOURCE:
                # Add presigned access URL to access restricted content
                artefact = magic_resource_client.lookup_artefact(check.url)
                check.access_url = artefact.presigned_url
            if check.type in (CheckType.INFO_ARCGIS_LAYER, CheckType.INFO_ARCGIS_WEBMAP):
                # Check item page via ArcGIS sharing API
                self._logger.info("[%s] Processing check for ArcGIS item page: %s", check.file_identifier, check.url)
                item_id = check.url.split("id=")[-1]
                check.access_url = f"https://www.arcgis.com/sharing/rest/content/items/{item_id}?f=json"
                self._logger.info(
                    "[%s] Checking item page using ArcGIS sharing API: %s", check.file_identifier, check.access_url
                )
            if check.type == CheckType.DOWNLOADS_ARCGIS_SERVICE:
                # Check service directly
                self._logger.info("[%s] Processing check for ArcGIS service: %s", check.file_identifier, check.url)
                check.access_url = f"{check.url}?f=json"
                self._logger.info("[%s] Checking ArcGIS service: %s", check.file_identifier, check.access_url)

    def execute(self, checks: list[Check]) -> list[Check]:
        """
        Run checks in parallel.

        Returns executed, prepared, checks.
        """
        self._prepare_checks(checks)
        return Parallel(n_jobs=self._parallel_jobs)(delayed(run_check)(self._logger.level, check) for check in checks)

    def check(self, meta: ExportMeta, checks: list[Check]) -> list[SiteContent]:
        """
        Run checks.

        Returns report outputs for export. Use `execute()` to return raw checks.
        """
        results = self.execute(checks)
        return ChecksOutput(logger=self._logger, meta=meta, checks=results).content
