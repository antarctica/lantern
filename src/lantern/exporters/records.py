import logging
from collections.abc import Callable
from copy import deepcopy
from enum import Enum
from typing import NamedTuple

from joblib import Parallel, delayed
from mypy_boto3_s3 import S3Client as S3ClientT

from lantern.config import Config
from lantern.exporters.base import Exporter, ResourceExporter
from lantern.exporters.html import HtmlAliasesExporter, HtmlExporter
from lantern.exporters.json import JsonExporter
from lantern.exporters.xml import IsoXmlExporter, IsoXmlHtmlExporter
from lantern.log import init as init_logging
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import Store
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import init_s3_client


class JobMethod(Enum):
    """Exporter action."""

    EXPORT = "export"
    PUBLISH = "publish"


class Job(NamedTuple):
    """Record/exporter and trusted context for processing job."""

    trusted: bool
    record: RecordRevision
    exporter: Callable[..., ResourceExporter]


_STORE_SINGLETON: Store | None = None
_S3_SINGLETON: S3ClientT | None = None


def _job_worker_s3(config: Config) -> S3ClientT:
    """
    AWS S3 client per worker process.

    Singleton used to avoid initialising store for each job as S3 clients cannot be pickled.
    """
    global _S3_SINGLETON
    if _S3_SINGLETON is None:
        _S3_SINGLETON = init_s3_client(config=config)
    return _S3_SINGLETON


def _job_worker_store(store: Store) -> Store:
    """
    Store per worker process.

    Singleton used to avoid initialising store for each job as some stores cannot be pickled.
    """
    global _STORE_SINGLETON
    if _STORE_SINGLETON is None:
        _STORE_SINGLETON = store
        if isinstance(store, GitLabCachedStore):
            # recreate flash cache
            _STORE_SINGLETON.select()
    return _STORE_SINGLETON


def _run_job(
    config: Config,
    meta: ExportMeta,
    store: Store,
    trusted: bool,
    exporter: Callable[..., ResourceExporter],
    record: RecordRevision,
    method: JobMethod,
) -> None:
    """
    Export or publish a record with a record exporter class.

    Receives a record and a RecordExporter class to instantiate with relevant parameters which is then run.

    Standalone function for use in parallel processing.
    """
    init_logging(config.LOG_LEVEL)
    logger = logging.getLogger("app")

    meta.trusted = trusted
    s3 = _job_worker_s3(config=config)
    store = _job_worker_store(store=store)
    select_record = store.select_one

    if exporter == HtmlAliasesExporter:
        exporter_ = HtmlAliasesExporter(logger=logger, meta=meta, s3=s3, record=record)
    elif exporter == HtmlExporter:
        exporter_ = HtmlExporter(logger=logger, meta=meta, s3=s3, record=record, select_record=select_record)
    else:
        exporter_ = exporter(logger=logger, meta=meta, s3=s3, record=record)

    msg = f"{method.value.capitalize()}ing record '{record.file_identifier}' using {exporter_.name} exporter"
    logger.info(msg)
    getattr(exporter_, method.value)()


class RecordsExporter(Exporter):
    """
    Data Catalogue records exporter.

    Coordinates exporting/publishing a selected set of records using format specific exporters.

    Records are processed in parallel where meta.parallel_jobs != 1.

    Config class and Store init callable needed for objects that cannot be passed into parallel jobs.
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        meta: ExportMeta,
        s3: S3ClientT,
        store: Store,
        selected_identifiers: set[str] | None = None,
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._config = config
        self._parallel_jobs = meta.parallel_jobs
        self._selected_identifiers: set[str] = selected_identifiers or set()
        self._store = store

    def _generate(self) -> list[Job]:
        """
        Generate parallel processing jobs for exporting or publishing all/selected records.

        Jobs = all/selected records * (record exporter classes + with trusted context for items).
        """
        parallel_classes = [HtmlExporter, HtmlAliasesExporter, JsonExporter, IsoXmlExporter, IsoXmlHtmlExporter]
        jobs: list[Job] = []

        for record in self._store.select(self._selected_identifiers):
            jobs.extend([Job(trusted=False, record=record, exporter=cls) for cls in parallel_classes])
            jobs.append(Job(trusted=True, record=record, exporter=HtmlExporter))
        return jobs

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

    def _prep_meta(self) -> ExportMeta:
        """
        Prepare export metadata for use in parallel processing jobs.

        Copied to prevent final job influencing trusted context value.
        """
        return deepcopy(self._meta)

    def _run(self, method: JobMethod) -> None:
        """
        Execute parallel processing jobs for exporting or publishing selected records.

        To debug, comment out Parallel loop and manually call _job() before with a selected job then return early. E.g:
        ```
        _run_job(
            self._config, self._meta, admin_meta_keys_json, jobs[0].trusted, jobs[0].exporter, jobs[0].record, method,
        )
        return None
        Parallel(n_jobs=self._parallel_jobs)(...)
        ```
        jobs[15] = 30825673-6276-4e5a-8a97-f97f2094cd25 (complete product, HTML exporter)
        """
        jobs = self._generate()
        meta = self._prep_meta()
        store = self._prep_store()
        Parallel(n_jobs=self._parallel_jobs)(
            delayed(_run_job)(self._config, meta, store, job.trusted, job.exporter, job.record, method) for job in jobs
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Records"

    def export(self) -> None:
        """Export selected records to a directory."""
        self._run(method=JobMethod.EXPORT)

    def publish(self) -> None:
        """Publish selected records to S3."""
        self._run(method=JobMethod.PUBLISH)
