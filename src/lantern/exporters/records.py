import logging
from collections.abc import Callable
from enum import Enum

from boto3 import client as S3Client  # noqa: N812
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


class JobMethod(Enum):
    """Exporter action."""

    EXPORT = "export"
    PUBLISH = "publish"


def _job_s3(config: Config) -> S3ClientT:
    """
    Create AWS S3 client instance.

    S3 instances cannot be pickled and so the S3 instance passed to RecordsExporter class cannot be passed to parallel
    processing jobs. This function exists to allow s3 mocking in tests.
    """
    return S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )


def _job(
    logger: logging.Logger,
    config: Config,
    meta: ExportMeta,
    exporter: Callable[..., ResourceExporter],
    record: RecordRevision,
    get_record: Callable[[str], RecordRevision],
    method: JobMethod,
) -> None:
    """
    Export or publish a record with a record exporter class.

    Receives a record and a RecordExporter class to instantiate with relevant parameters which is then run.

    Standalone function for use in parallel processing.
    """
    init_logging(logger.level)  # each process needs logging initialising
    s3 = _job_s3(config=config)

    if exporter == HtmlAliasesExporter:
        exporter_ = HtmlAliasesExporter(logger=logger, meta=meta, s3=s3, record=record)
    elif exporter == HtmlExporter:
        exporter_ = HtmlExporter(logger=logger, meta=meta, s3=s3, record=record, get_record=get_record)
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

    Config class needed for S3 client creation in parallel jobs.
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        meta: ExportMeta,
        s3: S3ClientT,
        get_record: Callable[[str], RecordRevision],
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._config = config
        self._parallel_jobs = meta.parallel_jobs
        self._selected_identifiers: set[str] = set()
        self._get_record = get_record

    @property
    def selected_identifiers(self) -> set[str]:
        """Selected file identifiers."""
        return self._selected_identifiers

    @selected_identifiers.setter
    def selected_identifiers(self, identifiers: set[str]) -> None:
        """Selected file identifiers."""
        self._selected_identifiers = identifiers

    def _run(self, method: JobMethod) -> None:
        """
        Generate parallel processing jobs for exporting or publishing selected records.

        Jobs are created for each record exporter class for each selected record.
        """
        jobs = []
        parallel_classes = [HtmlExporter, HtmlAliasesExporter, JsonExporter, IsoXmlExporter, IsoXmlHtmlExporter]
        for file_identifier in self._selected_identifiers:
            record = self._get_record(file_identifier)
            jobs.extend([(cls, record) for cls in parallel_classes])
        # where job[0] is an exporter class and job[1] a record
        Parallel(n_jobs=self._parallel_jobs)(
            delayed(_job)(
                self._logger,
                self._config,
                self._meta,
                job[0],
                job[1],
                self._get_record,
                method,
            )
            for job in jobs
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
