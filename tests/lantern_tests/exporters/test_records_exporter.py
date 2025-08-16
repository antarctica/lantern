import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from mypy_boto3_s3 import S3Client
from pytest_mock import MockerFixture

from lantern.exporters.base import S3Utils
from lantern.exporters.records import RecordsExporter
from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.elements.common import Identifier


class TestRecordsExporter:
    """Test meta records exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_record_minimal_item_catalogue: Record,
    ):
        """Can create an empty Records Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = RecordsExporter(config=mock_config, s3=fx_s3_client, logger=fx_logger)

        assert isinstance(exporter, RecordsExporter)
        assert exporter.name == "Records"
        assert len(exporter._records) == 0

    def test_loads(self, fx_exporter_records: RecordsExporter, fx_record_minimal_item_catalogue: Record):
        """Can load records and summaries."""
        records = [fx_record_minimal_item_catalogue]
        fx_exporter_records.loads(records)

    def test_get_record(self, fx_exporter_records_pop: RecordsExporter, fx_record_minimal_item_catalogue: Record):
        """Can get record."""
        record = fx_record_minimal_item_catalogue
        assert fx_exporter_records_pop._get_record(record.file_identifier) == record

    def test_get_exporters(self, fx_exporter_records_pop: RecordsExporter, fx_record_minimal_item_catalogue: Record):
        """Can get exporter instances."""
        result = fx_exporter_records_pop._get_exporters(fx_record_minimal_item_catalogue)
        names = sorted([exporter.name for exporter in result])
        assert names == sorted(["Item HTML", "Item Aliases", "BAS JSON", "ISO XML", "ISO XML HTML"])

    def test_export_record(self, fx_exporter_records_pop: RecordsExporter, fx_record_minimal_item_catalogue: Record):
        """Can export a record to local files."""
        site_path = fx_exporter_records_pop._config.EXPORT_PATH
        record_id = fx_record_minimal_item_catalogue.file_identifier
        expected = [
            site_path.joinpath("records", f"{record_id}.json"),
            site_path.joinpath("records", f"{record_id}.xml"),
            site_path.joinpath("records", f"{record_id}.html"),
            site_path.joinpath("datasets", "y", "index.html"),
            site_path.joinpath("items", record_id, "index.html"),
        ]
        fx_exporter_records_pop._records[record_id].identification.identifiers.append(
            Identifier(
                identifier="datasets/y", href="https://data.bas.ac.uk/datasets/y", namespace="alias.data.bas.ac.uk"
            )
        )

        fx_exporter_records_pop.export_record(fx_record_minimal_item_catalogue.file_identifier)

        result = list(fx_exporter_records_pop._config.EXPORT_PATH.glob("**/*.*"))
        for path in expected:
            assert path in result

    def test_publish_record(
        self,
        fx_exporter_records_pop: RecordsExporter,
        fx_record_minimal_item_catalogue: Record,
        fx_s3_bucket_name: str,
    ):
        """Can export a record to S3 objects."""
        record_id = fx_record_minimal_item_catalogue.file_identifier
        s3_utils = S3Utils(
            logger=fx_exporter_records_pop._logger,
            s3=fx_exporter_records_pop._s3_client,
            s3_bucket=fx_s3_bucket_name,
            relative_base=fx_exporter_records_pop._config.EXPORT_PATH,
        )
        expected = [
            "items/x/index.html",
            "datasets/y/index.html",
            "records/x.html",
            "records/x.json",
            "records/x.xml",
        ]
        fx_exporter_records_pop._records[record_id].identification.identifiers.append(
            Identifier(
                identifier="datasets/y", href="https://data.bas.ac.uk/datasets/y", namespace="alias.data.bas.ac.uk"
            )
        )

        fx_exporter_records_pop.publish_record(fx_record_minimal_item_catalogue.file_identifier)

        result = s3_utils._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys

    def test_export_all(self, fx_exporter_records_pop: RecordsExporter):
        """Can export all records."""
        fx_exporter_records_pop.export()

        result = list(fx_exporter_records_pop._config.EXPORT_PATH.glob("**/*.*"))
        assert len(result) > 0

    def test_publish_all(self, fx_exporter_records_pop: RecordsExporter):
        """Can export all records."""
        bucket = fx_exporter_records_pop._config.AWS_S3_BUCKET
        s3_utils = S3Utils(
            logger=fx_exporter_records_pop._logger,
            s3=fx_exporter_records_pop._s3_client,
            s3_bucket=bucket,
            relative_base=fx_exporter_records_pop._config.EXPORT_PATH,
        )

        fx_exporter_records_pop.publish()

        result = s3_utils._s3.list_objects(Bucket=bucket)
        keys = [o["Key"] for o in result["Contents"]]
        assert len(keys) > 0
