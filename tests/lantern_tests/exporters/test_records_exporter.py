import logging
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest

# noinspection PyPep8Naming
from botocore.client import BaseClient as S3  # noqa: N814
from mypy_boto3_s3 import S3Client
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.exporters.base import S3Utils
from lantern.exporters.html import HtmlAliasesExporter, HtmlExporter
from lantern.exporters.json import JsonExporter

# noinspection PyProtectedMember
from lantern.exporters.records import JobMethod, RecordsExporter, _job, _job_config, _job_s3
from lantern.exporters.xml import IsoXmlExporter, IsoXmlHtmlExporter
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision


class TestRecordExporterJob:
    """Test functions related to record parallel processing jobs."""

    @pytest.mark.cov()
    def test_job_config(self):
        """Can create standalone config instance."""
        result = _job_config()
        assert isinstance(result, Config)

    @pytest.mark.cov()
    def test_job_s3(self, fx_config: Config):
        """Can create standalone S3 client instance."""
        result = _job_s3(config=fx_config)
        assert isinstance(result, S3)

    @pytest.mark.parametrize(
        ("exporter", "expected"),
        [
            (HtmlExporter, "items/FILE_IDENTIFIER/index.html"),
            (HtmlAliasesExporter, "datasets/x/index.html"),
            (JsonExporter, "records/FILE_IDENTIFIER.json"),
            (IsoXmlExporter, "records/FILE_IDENTIFIER.xml"),
            (IsoXmlHtmlExporter, "records/FILE_IDENTIFIER.html"),
        ],
    )
    @pytest.mark.parametrize("method", [JobMethod.EXPORT, JobMethod.PUBLISH])
    def test_job(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_revision_model_min: RecordRevision,
        fx_get_record: callable,
        fx_s3_bucket_name: str,
        fx_s3_utils: S3Utils,
        fx_exporter_records_sel: RecordsExporter,
        exporter: RecordsExporter,
        expected: str,
        method: JobMethod,
    ):
        """Can export or publish a record using a record exporter class."""
        mocker.patch("lantern.exporters.records._job_config", return_value=fx_exporter_records_sel._config)
        mocker.patch("lantern.exporters.records._job_s3", return_value=fx_exporter_records_sel._s3_client)
        fx_revision_model_min.identification.identifiers.append(
            Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)
        )
        expected = expected.replace("FILE_IDENTIFIER", fx_revision_model_min.file_identifier)
        expected_path = fx_exporter_records_sel._config.EXPORT_PATH / expected

        # noinspection PyTypeChecker
        _job(
            logger=fx_logger,
            exporter=exporter,
            record=fx_revision_model_min,
            get_record=fx_get_record,
            export_base=fx_exporter_records_sel._config.EXPORT_PATH,
            method=method,
        )

        if method == JobMethod.EXPORT:
            assert expected_path.exists()
        elif method == JobMethod.PUBLISH:
            result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
            assert result["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestRecordsExporter:
    """Test meta records exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_get_record: Callable[[str], RecordRevision],
    ):
        """Can create an empty Records Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = RecordsExporter(config=mock_config, s3=fx_s3_client, logger=fx_logger, get_record=fx_get_record)

        assert isinstance(exporter, RecordsExporter)
        assert exporter.name == "Records"

    def test_export(self, mocker: MockerFixture, fx_exporter_records_sel: RecordsExporter):
        """Can export selected records."""
        mocker.patch("lantern.exporters.records._job_config", return_value=fx_exporter_records_sel._config)
        mocker.patch("lantern.exporters.records._job_s3", return_value=fx_exporter_records_sel._s3_client)

        fx_exporter_records_sel.export()

        result = list(fx_exporter_records_sel._config.EXPORT_PATH.glob("**/*.*"))
        assert len(result) > 0

    def test_publish(
        self,
        mocker: MockerFixture,
        fx_exporter_records_sel: RecordsExporter,
        fx_s3_bucket_name: str,
        fx_s3_utils: S3Utils,
    ):
        """Can publish selected records."""
        mocker.patch("lantern.exporters.records._job_config", return_value=fx_exporter_records_sel._config)
        mocker.patch("lantern.exporters.records._job_s3", return_value=fx_exporter_records_sel._s3_client)

        fx_exporter_records_sel.publish()

        result = fx_s3_utils._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        assert len(keys) > 0
