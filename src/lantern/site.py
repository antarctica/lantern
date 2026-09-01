import logging
import time
from datetime import date
from typing import TYPE_CHECKING, Literal, NamedTuple, cast
from uuid import uuid4

from joblib import Parallel, delayed

from lantern.log import init as init_logging
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_health import SiteHealthOutput, SiteHealthOutputComponentValues
from lantern.outputs.site_index import SiteIndexOutput

if TYPE_CHECKING:
    from collections.abc import Callable

    from lxml import etree

    from lantern.models.checks import Check
    from lantern.models.record.revision import RecordRevision
    from lantern.models.site import ExportMeta, SiteContent
    from lantern.outputs.base import OutputBase
    from lantern.stores.base import StoreBase

SiteAction = Literal["content", "checks", "invalidations"]

_STORE_SINGLETON: tuple[str, StoreBase] | None = None
_ISO_HTML_XSLT_SINGLETON: etree.XSLT | None = None


def _job_worker_store(key: str, store: StoreBase) -> StoreBase:
    """
    Store per worker process.

    Singleton used to avoid re-initialising the store for each job, as some stores are expensive or impossible
    to pickle with in memory state.

    Keyed by the owning Site so that a worker reused by a different Site does not silently return the wrong
    store. Only the most recent store is retained, as jobs from a Site are dispatched together.
    """
    global _STORE_SINGLETON  # noqa: PLW0603
    if _STORE_SINGLETON is None or _STORE_SINGLETON[0] != key:
        store.restore_parallel()
        _STORE_SINGLETON = (key, store)
    return _STORE_SINGLETON[1]


def _job_worker_iso_html_transform() -> etree.XSLT:
    """
    ISO HTML XSLT transform per worker process.

    Singleton used to avoid initialising transform for each job as transform cannot be pickled.

    Not keyed, as the transform is built from a static stylesheet and so is identical for all Sites.
    """
    global _ISO_HTML_XSLT_SINGLETON  # noqa: PLW0603
    if _ISO_HTML_XSLT_SINGLETON is None:
        _ISO_HTML_XSLT_SINGLETON = RecordIsoHtmlOutput.create_xslt_transformer()
    # noinspection PyTypeChecker
    return _ISO_HTML_XSLT_SINGLETON


def _run_job(
    log_level: int,
    meta: ExportMeta,
    store: StoreBase,
    job: SiteJob,
    worker_key: str,
) -> list[SiteContent] | list[Check] | list[str]:
    """
    Generate content or checks from an Output.

    Standalone function for use in parallel processing.
    """
    init_logging(log_level)
    logger = logging.getLogger("lantern")
    store = _job_worker_store(key=worker_key, store=store)
    iso_html_transform = _job_worker_iso_html_transform()
    select_record = store.select_one
    select_records = store.select
    job_extras = job.extras or {}

    if job.output == ItemCatalogueOutput:
        output = job.output(logger=logger, meta=meta, record=job.record, select_record=select_record)
    elif job.output == SiteHealthOutput:
        component_values = SiteHealthOutputComponentValues(
            job_extras.get("site_records_count", -1),
            job_extras.get("search_records_count", -1),
            job_extras.get("entra_secret_expiry", date.min),
            job_extras.get("entra_secret_id", "?"),
        )
        output = job.output(
            logger=logger,
            meta=meta,
            component_values=component_values,
        )
    elif job.output in [SiteIndexOutput, ItemsBasWebsiteOutput, RecordsWafOutput]:
        output = job.output(logger=logger, meta=meta, select_records=select_records)
    elif job.output == RecordIsoHtmlOutput:
        output = job.output(logger=logger, meta=meta, record=job.record, transform=iso_html_transform)
    elif job.output in [ItemAliasesOutput, RecordIsoJsonOutput, RecordIsoXmlOutput]:
        output = job.output(logger=logger, meta=meta, record=job.record)
    else:
        output = job.output(logger=logger, meta=meta)

    msg = f"Outputting {job.action} for {output.name}."
    if job.record:
        msg = f"Outputting {job.action} for record '{job.record.file_identifier}' using {output.name}."
    logger.info(msg)
    if job.action == "checks":
        return output.checks
    if job.action == "invalidations":
        keys = output.invalidation_keys
        # In Cloudfront '/foo/index.html' and '/foo' are separate keys
        keys.extend([k.replace("index.html", "") for k in keys if k.endswith("/index.html")])
        return keys
    return output.content


class SiteJob(NamedTuple):
    """Output class, action, and optional Record instance and/or any extras for a Site generator job."""

    action: SiteAction
    output: Callable[..., OutputBase]
    record: RecordRevision | None = None
    extras: dict | None = None


class Site:
    """
    Simple static site generator.

    Generates content or content checks for selected Output classes and records from a Store.

    Flexible class intended to be used in a higher level and opinionated Catalogue class.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, store: StoreBase, extras: dict | None = None) -> None:
        self._logger = logger
        self._meta = meta
        self._store = store
        self._extras = extras or {}

        self._workers = meta.parallel_jobs
        self._worker_key = str(uuid4())

    def _generate_jobs(
        self,
        actions: list[SiteAction],
        global_outputs: list[type[OutputBase]],
        individual_outputs: list[type[OutputBase]],
        identifiers: set[str] | None = None,
    ) -> list[SiteJob]:
        """
        Create jobs for generating content, checks and/or invalidation keys for Output classes and records.

        Includes any site extras for use in Outputs.

        Output classes are 'global' or 'individual' depending on whether they operate on individual records.

        Generated as: [actions] * [output class] (* [record])
        """
        extras = self._extras or None
        global_ = [SiteJob(action=action, output=cls, extras=extras) for action in actions for cls in global_outputs]
        individual_ = [
            SiteJob(action=action, output=cls, record=record, extras=extras)
            for action in actions
            for cls in individual_outputs
            for record in self._store.select(identifiers)
        ]
        return global_ + individual_

    def execute(self, jobs: list[SiteJob]) -> list[SiteContent | Check | list[str]]:
        """
        Execute a set of jobs in parallel to generate site content, checks and/or invalidation keys.

        Returns generated content, checks or invalidation keys as a flattened list.
        """
        store = self._store.prep_parallel()
        start = time.monotonic()
        nested_outputs: list[list[SiteContent | Check | list[str]]] = Parallel(n_jobs=self._workers)(
            delayed(_run_job)(self._logger.level, self._meta, store, job, self._worker_key) for job in jobs
        )
        outputs: list[SiteContent | Check | list[str]] = [
            output for output_outputs in nested_outputs for output in output_outputs
        ]
        self._logger.info(
            "Generated %s site content/checks/keys in %s seconds", len(outputs), round(time.monotonic() - start)
        )
        return outputs

    def generate_content(
        self,
        global_outputs: list[type[OutputBase]],
        individual_outputs: list[type[OutputBase]],
        identifiers: set[str] | None = None,
    ) -> list[SiteContent]:
        """Generate site content."""
        jobs = self._generate_jobs(
            actions=["content"],
            global_outputs=global_outputs,
            individual_outputs=individual_outputs,
            identifiers=identifiers,
        )
        return cast("list[SiteContent]", self.execute(jobs))

    def generate_checks(
        self,
        global_outputs: list[type[OutputBase]],
        individual_outputs: list[type[OutputBase]],
        identifiers: set[str] | None = None,
    ) -> list[Check]:
        """Generate site checks."""
        jobs = self._generate_jobs(
            actions=["checks"],
            global_outputs=global_outputs,
            individual_outputs=individual_outputs,
            identifiers=identifiers,
        )
        return cast("list[Check]", self.execute(jobs))

    def generate_invalidation_keys(
        self,
        global_outputs: list[type[OutputBase]],
        individual_outputs: list[type[OutputBase]],
        identifiers: set[str] | None = None,
    ) -> list[str]:
        """Generate site invalidation keys for content."""
        jobs = self._generate_jobs(
            actions=["invalidations"],
            global_outputs=global_outputs,
            individual_outputs=individual_outputs,
            identifiers=identifiers,
        )
        keys = set(self.execute(jobs))
        return cast("list[str]", cast("object", list(keys)))
