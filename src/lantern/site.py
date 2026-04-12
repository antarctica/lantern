import logging
import time
from collections.abc import Callable
from copy import deepcopy
from typing import Literal, NamedTuple, cast

from joblib import Parallel, delayed
from lxml import etree

from lantern.log import init as init_logging
from lantern.models.checks import Check
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputBase
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.stores.base import Store
from lantern.stores.gitlab_cache import GitLabCachedStore

SiteAction = Literal["content", "checks"]

_STORE_SINGLETON: Store | None = None
_ISO_HTML_XSLT_SINGLETON: etree.XSLT | None = None


def _job_worker_store(store: Store) -> Store:
    """
    Store per worker process.

    Singleton used to avoid initialising store for each job as some stores cannot be pickled.
    """
    global _STORE_SINGLETON
    if _STORE_SINGLETON is None:
        _STORE_SINGLETON = store
        if isinstance(store, GitLabCachedStore):
            _STORE_SINGLETON.select()  # recreate flash cache
    return _STORE_SINGLETON


def _job_worker_iso_html_transform() -> etree.XSLT:
    """
    ISO HTML XSLT transform per worker process.

    Singleton used to avoid initialising transform for each job as transform cannot be pickled.
    """
    global _ISO_HTML_XSLT_SINGLETON
    if _ISO_HTML_XSLT_SINGLETON is None:
        _ISO_HTML_XSLT_SINGLETON = RecordIsoHtmlOutput.create_xslt_transformer()
    return _ISO_HTML_XSLT_SINGLETON


def _run_job(
    log_level: int,
    meta: ExportMeta,
    store: Store,
    job: "SiteJob",
) -> list[SiteContent] | list[Check]:
    """
    Generate content or checks from an Output.

    Standalone function for use in parallel processing.
    """
    init_logging(log_level)
    logger = logging.getLogger("app")
    store = _job_worker_store(store=store)
    iso_html_transform = _job_worker_iso_html_transform()
    select_record = store.select_one
    select_records = store.select

    if job.output == ItemCatalogueOutput:
        output = job.output(logger=logger, meta=meta, record=job.record, select_record=select_record)
    elif job.output in [SiteIndexOutput, SiteHealthOutput, ItemsBasWebsiteOutput, RecordsWafOutput]:
        output = job.output(logger=logger, meta=meta, select_records=select_records)
    elif job.output == RecordIsoHtmlOutput:
        output = job.output(logger=logger, meta=meta, record=job.record, transform=iso_html_transform)
    elif job.output in [ItemAliasesOutput, RecordIsoJsonOutput, RecordIsoXmlOutput]:
        output = job.output(logger=logger, meta=meta, record=job.record)
    else:
        output = job.output(logger=logger, meta=meta)

    msg = f"Outputting {job.action} using {output.name}."
    if job.record:
        msg = f"Outputting {job.action} for record '{job.record.file_identifier}' using {output.name}."
    logger.info(msg)
    if job.action == "checks":
        return output.checks
    return output.content


class SiteJob(NamedTuple):
    """Output class, action, and optional Record instance for a Site generator job."""

    action: SiteAction
    output: Callable[..., OutputBase]
    record: RecordRevision | None = None


class Site:
    """
    Simple static site generator.

    Generates content or content checks for selected Output classes and records from a Store.

    Flexible class intended to be used in a higher level and opinionated Catalogue class.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, store: Store) -> None:
        self._logger = logger
        self._meta = meta
        self._store = store

        self._workers = meta.parallel_jobs

    def _prep_store(self) -> Store:
        """
        Prepare store for use in parallel processing jobs.

        Applies specifically to GitLabCachedStore which contain an in-memory dict of pickled records, and add
        significant overhead when pickling and unpickling these stores for each parallel job.

        A copy of the store without the in-memory cache layer is made to avoid this, and the `_STORE_SINGLETON`
        singleton will then recreate it for each worker process.
        """
        if not isinstance(self._store, GitLabCachedStore):
            return self._store

        store = deepcopy(self._store)
        store._cache._flash.clear()
        return store

    def _generate_jobs(
        self,
        actions: list[SiteAction],
        global_outputs: list[type[OutputBase]],
        individual_outputs: list[type[OutputBase]],
        identifiers: set[str] | None = None,
    ) -> list[SiteJob]:
        """
        Create jobs for generating content and/or checks for Output classes and records.

        Output classes are 'global' or 'individual' depending on whether they operate on individual records.

        Generated as: [actions] * [output class] (* [record])
        """
        global_ = [SiteJob(action=action, output=cls) for action in actions for cls in global_outputs]
        individual_ = [
            SiteJob(action=action, output=cls, record=record)
            for action in actions
            for cls in individual_outputs
            for record in self._store.select(identifiers)
        ]
        return global_ + individual_

    def execute(self, jobs: list[SiteJob]) -> list[SiteContent | Check]:
        """
        Execute a set of jobs in parallel to generate site content and/or checks.

        Returns generated content and/or checks as a flattened list.
        """
        store = self._prep_store()
        start = time.monotonic()
        nested_outputs: list[list[SiteContent]] = Parallel(n_jobs=self._workers)(
            delayed(_run_job)(self._logger.level, self._meta, store, job) for job in jobs
        )
        outputs = [content for output_content in nested_outputs for content in output_content]
        self._logger.info(f"Generated {len(outputs)} site content/checks in {round(time.monotonic() - start)} seconds")
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
        return cast(list[SiteContent], self.execute(jobs))

    def generate_checks(
        self,
        global_outputs: list[type[OutputBase]],
        individual_outputs: list[type[OutputBase]],
        identifiers: set[str] | None = None,
    ) -> list[Check]:
        """Generate site content."""
        jobs = self._generate_jobs(
            actions=["checks"],
            global_outputs=global_outputs,
            individual_outputs=individual_outputs,
            identifiers=identifiers,
        )
        return cast(list[Check], self.execute(jobs))
