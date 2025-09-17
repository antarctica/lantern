import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Final, cast

import cattrs
import requests
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from mypy_boto3_s3 import S3Client
from requests import Response

from lantern.exporters.base import ResourcesExporter, get_jinja_env
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteMeta
from lantern.models.verification.elements import VerificationRecord
from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext


def _req_url(job: VerificationJob, params: dict | None = None) -> Response:
    """
    Request a URL as part of a site verification job.

    Intended as an inner method called by URL check callables. Returns a Requests response for further validation.

    Uses verification job context configuration to control the request:
    - method (defaults to HEAD)
    - url
    - headers
    - body (JSON content-type only)

    Additional request parameters (such as following redirects) can be set via the `params` parameter.

    The response status code and optionally content length will be validated. If invalid, the verification job is
    updated in place as failed.

    Standalone function for use in parallel processing.
    """
    expected_status = job.context.get("EXPECTED_STATUS", 200)
    expected_length = job.context.get("EXPECTED_LENGTH", None)
    method = job.context.get("METHOD", "head")
    url = job.context.get("URL", job.url)
    headers = job.context.get("HEADERS", {})
    body = job.context.get("JSON", {})

    params_ = {"url": url, "timeout": 30, "headers": headers, "allow_redirects": False}
    if params is not None:
        params_.update(params)

    match method:
        case "get":
            r = requests.get(**params_)  # noqa: S113 # ty: ignore[missing-argument]
        case "post":
            r = requests.post(**params_, json=body)  # noqa: S113 # ty: ignore[missing-argument]
        case "head":
            r = requests.head(**params_)  # noqa: S113 # ty: ignore[missing-argument]
        case _:
            msg = f"Unsupported HTTP method: {method}"
            raise ValueError(msg) from None

    # noinspection PyUnboundLocalVariable
    job.data["status_code"] = r.status_code
    if r.status_code != expected_status:
        # fail if status is not expected
        job.result = VerificationResult.FAIL
        return r

    if (
        expected_length is not None
        and expected_status != 206
        and int(r.headers.get("content-length", 0)) != expected_length
    ):
        # fail if content-length is not expected (if known and is not partial content)
        job.result = VerificationResult.FAIL
        return r

    return r


def check_url(job: VerificationJob) -> None:
    """
    Default URL check.

    Checks the status code and optionally content length are expected values.

    Standalone function for use in parallel processing.
    """
    _req_url(job)
    job.result = VerificationResult.PASS


def check_url_redirect(job: VerificationJob) -> None:
    """
    Redirect URL check.

    Checks the status code and location header of the redirect are expected values. Also checks this location (target)
    gives an expected status (i.e. the redirect target exists and can be followed).

    Standalone function for use in parallel processing.
    """
    # check redirect
    job.context["EXPECTED_STATUS"] = 301
    redirect_req = _req_url(job)
    if "location" not in redirect_req.headers or redirect_req.headers["Location"] != job.context["TARGET"]:
        # fail if redirect location is missing or not expected
        job.result = VerificationResult.FAIL
        return

    # check redirect target
    job.context["EXPECTED_STATUS"] = 200
    _req_url(job, {"allow_redirects": True})

    job.result = VerificationResult.PASS
    return


def check_url_arcgis(job: VerificationJob) -> None:
    """
    ArcGIS item URL check.

    Checks a request to the ArcGIS API does not contain an error.

    Expects check URLs to return JSON content/errors (use `?f=json` or equivalent in URL).

    Standalone function for use in parallel processing.
    """
    job.context["METHOD"] = "get"
    req = _req_url(job)
    if "error" in req.json():
        job.result = VerificationResult.FAIL
        job.data["error"] = req.json()
        return

    job.result = VerificationResult.PASS
    return


def check_item_download(job: VerificationJob) -> None:
    """
    Catalogue item download option check.

    Checks a URL is included in an item page (i.e. a link to the URL appears somewhere the page contents).

    To ensure users can access distribution options listed in a record from its item page.

    Standalone function for use in parallel processing.
    """
    job.context["METHOD"] = "get"
    req = _req_url(job)
    html = BeautifulSoup(req.content, features="html.parser")
    url = job.url.replace("&", "&amp;")  # Escape & for HTML parsing

    # download href is typically in an <a> tag but for service endpoints may be in a <code> tag instead.
    if url not in str(html):
        job.result = VerificationResult.FAIL
        return

    job.result = VerificationResult.PASS
    return


def run_job(job: VerificationJob) -> VerificationJob:
    """
    Execute a verification job.

    Standalone function for use in parallel processing.
    """
    if job.result != VerificationResult.PENDING:
        return job

    default_check_func = "check_url"
    check_func_ref: str = job.context.get("CHECK_FUNC", default_check_func)

    start = datetime.now(tz=UTC)
    check_func = globals()[check_func_ref]
    check_func(job)
    end = datetime.now(tz=UTC)
    job.data["duration"] = end - start
    return job


class VerificationReport:
    """
    Site verification report.

    Processes a list of verification jobs into a JSON and HTML report with calculated statistics and overall result.
    """

    def __init__(self, meta: SiteMeta, jobs: list[VerificationJob], context: VerificationContext) -> None:
        """Initialise."""
        self._meta = meta
        self._context = context
        self._jobs = jobs

        self._jinja = get_jinja_env()
        self._template_path = "_views/-/verification.html.j2"
        self._created: datetime = datetime.now(tz=UTC)
        self._duration: timedelta = timedelta(0)

        self._site_jobs: list[VerificationJob] = []
        self._resource_jobs: dict[str, list[VerificationJob]] = {}
        self._result: VerificationResult = VerificationResult.PENDING
        self._summary: dict[VerificationResult, int] = dict.fromkeys(VerificationResult, 0)

        self._post_init()

    def __len__(self) -> int:
        """Number of jobs."""
        return len(self._jobs)

    def _post_init(self) -> None:
        """Process job results."""
        for job in self._jobs:
            self._summary[job.result] += 1
            self._duration += job.data.get("duration", timedelta(0))

            if job.type == VerificationType.SITE_PAGES:
                self._site_jobs.append(job)
                continue

            file_identifier = job.data["file_identifier"]
            if file_identifier not in self._resource_jobs:
                self._resource_jobs[file_identifier] = []
            self._resource_jobs[file_identifier].append(job)

        if self._summary[VerificationResult.PASS] == len(self):
            self._result = VerificationResult.PASS
        else:
            self._result = VerificationResult.FAIL

    @property
    def data(self) -> dict:
        """
        Structure report data.

        Intended as the source of the HTML report and for any further additional processing if needed.
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(timedelta, lambda td: td.microseconds)

        commit = self._meta.build_ref
        if commit:
            commit = converter.unstructure(commit)

        stats = {label.value: value for label, value in self._summary.items()}
        stats.pop("-")

        site_checks: list[dict] = converter.unstructure(self._site_jobs)
        resource_checks: dict[str, list[dict]] = converter.unstructure(self._resource_jobs)
        for check in site_checks:
            check.pop("context", None)
        for resource in resource_checks.values():
            for check in resource:
                check.pop("context", None)

        return {
            "pass_fail": self._result == VerificationResult.PASS,
            "base_url": self._context["BASE_URL"],
            "commit": commit,
            "time": self._created.isoformat(),
            "stats": stats,
            "site_checks": site_checks,
            "resource_checks": resource_checks,
        }

    def dumps(self) -> str:
        """Render report as HTML page."""
        data = self.data
        self._meta.html_title = "Verification Results"
        return self._jinja.get_template(self._template_path).render(data=data, meta=self._meta)


class VerificationExporter(ResourcesExporter):
    """
    Site verification exporter.

    Verifies the contents of a static site using automic URL checks processed in parallel as a series of jobs.
    The results of these checks are processed into a JSON and HTML report using a `VerificationReport` instance.
    """

    site_pages: Final[list[str]] = [
        "/legal/accessibility",
        "/legal/cookies",
        "/legal/copyright",
        "/legal/privacy",
        "/-/index",
        "/-/formatting",
    ]

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        get_record: Callable[[str], RecordRevision],
        context: VerificationContext,
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3, get_record=get_record)
        self._get_record = get_record
        self._context = context
        self._jobs: list[VerificationJob] = []
        self._export_path = self._meta.export_path / "-" / "verification"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Verification"

    @property
    def _404_job(self) -> VerificationJob:
        """Generate a 404 handler job."""
        job = VerificationJob(
            type=VerificationType.SITE_PAGES,
            exporter="SitePagesExporter",
            url=f"{self._context['BASE_URL']}/-/404",
            context=cast(VerificationContext, {"EXPECTED_STATUS": 404, **self._context}),
            data={"path": "404"},
        )
        if "localhost" in self._context["BASE_URL"]:
            job.result = VerificationResult.SKIP
        return job

    @property
    def _site_jobs(self) -> list[VerificationJob]:
        """Generate verification jobs for site pages."""
        jobs = [self._404_job]
        for path in self.site_pages:
            jobs.append(
                VerificationJob(
                    type=VerificationType.SITE_PAGES,
                    exporter="SitePagesExporter",
                    url=f"{self._context['BASE_URL']}{path}/",
                    context=self._context,
                    data={"path": path},
                )
            )
        return jobs

    @property
    def _record_jobs(self) -> list[VerificationJob]:
        """Generate verification jobs for selected records."""
        records = [self._get_record(file_identifier) for file_identifier in self._selected_identifiers]
        jobs = [job for record in records for job in VerificationRecord(record).jobs(context=self._context)]

        # Skip checks that can't run based on BASE_URL
        if "localhost" in self._context["BASE_URL"]:
            for job in jobs:
                if job.type == VerificationType.ALIAS_REDIRECTS:
                    # Python simple server does not support redirects.
                    job.result = VerificationResult.SKIP
        if self._context["BASE_URL"] != f"https://{CATALOGUE_NAMESPACE}":
            for job in jobs:
                if job.type == VerificationType.DOI_REDIRECTS:
                    # DOIs only resolve correctly from the production domain.
                    job.result = VerificationResult.SKIP
        return jobs

    def _init_jobs(self) -> None:
        """Generate verification jobs for catalogue site."""
        self._jobs = [*self._site_jobs, *self._record_jobs]

    @property
    def report(self) -> VerificationReport:
        """Generate a verification report from verification jobs."""
        return VerificationReport(meta=self._meta.site_metadata, jobs=self._jobs, context=self._context)

    def run(self) -> None:
        """Execute verification jobs."""
        self._init_jobs()
        self._jobs = Parallel(n_jobs=self._meta.parallel_jobs)(delayed(run_job)(job) for job in self._jobs)

    def export(self) -> None:
        """Export JSON and HTML report files to local directory."""
        self._export_path.mkdir(parents=True, exist_ok=True)
        with self._export_path.joinpath("data.json").open("w") as f:
            json.dump(self.report.data, f, indent=2, ensure_ascii=False)
        with self._export_path.joinpath("index.html").open("w") as f:
            f.write(self.report.dumps())

    def publish(self) -> None:
        """Publish JSON and HTML report files to S3."""
        data_key = self._s3_utils.calc_key(self._export_path.joinpath("data.json"))
        self._s3_utils.upload_content(key=data_key, content_type="application/json", body=json.dumps(self.report.data))
        index_key = self._s3_utils.calc_key(self._export_path.joinpath("index.html"))
        self._s3_utils.upload_content(key=index_key, content_type="text/html", body=self.report.dumps())
