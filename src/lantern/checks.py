import base64
import json
import logging
import time
from http import HTTPMethod, HTTPStatus
from typing import TYPE_CHECKING

import requests
from joblib import Parallel, delayed
from requests import Response
from requests.auth import HTTPBasicAuth

from lantern.lib.requests.auth import HTTPBearerTokenAuth
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

        Handles time out errors only.
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
        Check URL as per check properties.

        Validates the response status code and optionally, content length and/or location header (for redirects).
        """
        self._logger.info("Fetching: %s", self._check.url)
        self._logger.debug({"method": self._check.http_method, "url": self._check.url})

        headers = None
        if self._check.type == CheckType.DOWNLOADS_NORA:
            # NORA does not support HEAD requests but does support ranges to avoid full downloads
            headers = {"Range": "bytes=0-253"}

        r = self._fetch_url(
            method=self._check.http_method,
            url=self._check.url,
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
        r2 = self._fetch_url(method=self._check.http_method, url=self._check.url, redirects=r_max, raise_errors=True)
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
        self._logger.info("Checking ArcGIS item page: %s", self._check.url)
        self._logger.info("Fetching from ArcGIS sharing API: %s", item_url)
        self._check_arcgis_url(item_url)

    def _check_arcgis_service(self) -> None:
        """
        Check ArcGIS service.

        Checks service endpoint directly. Limited to public items.
        """
        service_url = f"{self._check.url}?f=json"
        self._logger.info("Fetching: %s", service_url)
        self._check_arcgis_url(service_url)

    def _check_magic_product(self) -> None:
        """
        Check MAGIC Products Distribution Service file.

        https://gitlab.data.bas.ac.uk/MAGIC/products-distribution

        The distribution service uses Microsoft SharePoint. This check effectively reverse proxies a request for a
        SharePoint sharing URL (e.g. [1]), as per [2] using the MS Graph API [3] to get basic details including
        expected file size.

        [1] https://nercacuk.sharepoint.com/:b:/r/sites/MAGICProductsDistribution/...
        [2] https://learn.microsoft.com/en-us/graph/api/shares-get#encoding-sharing-urls
        [3] https://learn.microsoft.com/en-us/graph/api/driveitem-get
        """
        self._logger.info("Fetching: %s", self._check.url)

        share_url = "u!" + base64.urlsafe_b64encode(self._check.url.encode("utf-8")).decode("utf-8").rstrip("=")
        graph_url = f"https://graph.microsoft.com/v1.0/shares/{share_url}/driveItem"
        self._logger.info("Resolved to: %s", graph_url)

        r = self._fetch_url(
            method=HTTPMethod.GET,
            url=graph_url,
            params={"$select": "id,name,size,file"},
            auth=self._check.http_auth,
            redirects=0,
            raise_errors=False,
        )
        if r is None:
            return
        result = r.json()

        if self._check.result_http_status != self._check.http_status:
            self._check.state = CheckState.FAILED
            self._check.result_output = (
                f"Bad status: {self._check.result_http_status} (expected {self._check.http_status})"
            )
            return

        if "file" not in result:
            self._check.state = CheckState.FAILED
            self._check.result_output = "Bad drive item type: expected file"
            return

        if self._check.content_length is not None and result.get("size") != self._check.content_length:
            self._check.state = CheckState.FAILED
            self._check.result_output = (
                f"Bad drive item size: {result.get('size')} (expected {self._check.content_length})"
            )
            return

        self._check.state = CheckState.PASS
        self._check.result_output = "OK"

    def run(self) -> None:
        """Run check unless skipped."""
        if self._check.state == CheckState.SKIPPED:
            return

        start = time.monotonic()
        if self._check.type in (CheckType.DOWNLOADS_ARCGIS_LAYER, CheckType.INFO_ARCGIS_WEBMAP):
            self._check_arcgis_item()
        elif self._check.type == CheckType.DOWNLOADS_ARCGIS_SERVICE:
            self._check_arcgis_service()
        elif self._check.type == CheckType.DOWNLOADS_SHAREPOINT_MAGIC_PRODUCTS:
            self._check_magic_product()
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

    def _get_auth_entra(self) -> str:
        """
        Get access token for accessing entra protected resources.

        Includes the Microsoft Graph API.
        """
        response = requests.post(
            f"https://login.microsoftonline.com/{self._config.CHECKS_MAGIC_PRODUCTS_TENANT_ID}/oauth2/v2.0/token",
            data={
                "client_id": self._config.CHECKS_MAGIC_PRODUCTS_CLIENT_ID,
                "client_secret": self._config.CHECKS_MAGIC_PRODUCTS_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _prepare_auth(self, checks: list[Check]) -> None:
        """
        Add authentication needed to check restricted resources.

        Reuses/caches tokens for supported services.
        """
        _entra_token: str | None = None

        for check in checks:
            # Add basic auth for accessing trusted publishing content (Ops Data Store LDAP)
            if check.type == CheckType.ITEM_PAGES_TRUSTED:
                check.http_auth = HTTPBasicAuth(
                    username=self._config.CHECKS_TRUSTED_USERNAME, password=self._config.CHECKS_TRUSTED_PASSWORD
                )
            elif check.type == CheckType.DOWNLOADS_SHAREPOINT_MAGIC_PRODUCTS:
                # Add entra token for accessing SharePoint drive items (MS Graph via catalogue app registration)
                if not _entra_token:
                    _entra_token = self._get_auth_entra()
                check.http_auth = HTTPBearerTokenAuth(token=_entra_token)

    def _prepare_checks(self, checks: list[Check]) -> None:
        """Post process checks prior to execution."""
        self._prepare_auth(checks)

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
