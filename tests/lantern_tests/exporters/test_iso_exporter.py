import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from lantern.exporters.xml import IsoXmlExporter, IsoXmlHtmlExporter
from lantern.models.record.revision import RecordRevision


class TestIsoXmlExporter:
    """Test ISO 19115 XML exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
    ):
        """Can create an ISO XML Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        expected = output_path.joinpath(f"{fx_revision_model_min.file_identifier}.xml")

        exporter = IsoXmlExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_revision_model_min,
            export_base=output_path,
        )

        assert isinstance(exporter, IsoXmlExporter)
        assert exporter.name == "ISO XML"
        assert exporter._export_path == expected

    def test_dumps(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
    ):
        """Can encode record as ISO 19139 XML string."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = IsoXmlExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_revision_model_min,
            export_base=output_path,
        )

        result = exporter.dumps()
        assert "<gmi:MI_Metadata" in result


class TestIsoXmlHtmlExporter:
    """Test ISO 19115 XML HTML exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_s3_bucket_name: str,
        fx_logger: logging.Logger,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
    ):
        """Can create an ISO XML HTML Exporter."""
        with TemporaryDirectory() as tmp_path:
            base_path = Path(tmp_path)
            exports_path = base_path.joinpath("exports")
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=base_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

        exporter = IsoXmlHtmlExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_revision_model_min,
            export_base=exports_path,
        )
        expected = exports_path.joinpath(f"{fx_revision_model_min.file_identifier}.html")

        assert isinstance(exporter, IsoXmlHtmlExporter)
        assert exporter.name == "ISO XML HTML"
        assert exporter._export_path == expected

    def test_dumps(self, fx_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can apply stylesheet to string from IsoXmlExporter."""
        expected = "<html xmlns:gco"
        result = fx_exporter_iso_xml_html.dumps()
        assert expected in result
