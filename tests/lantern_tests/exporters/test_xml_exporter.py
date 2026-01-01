import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from lantern.exporters.xml import IsoXmlExporter, IsoXmlHtmlExporter
from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, set_admin
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta


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
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")
        expected = output_path / "records" / f"{fx_revision_model_min.file_identifier}.xml"

        exporter = IsoXmlExporter(meta=meta, logger=fx_logger, s3=fx_s3_client, record=fx_revision_model_min)

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
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = IsoXmlExporter(meta=meta, logger=fx_logger, s3=fx_s3_client, record=fx_revision_model_min)

        result = exporter.dumps()
        assert "<gmi:MI_Metadata" in result

    def test_dumps_no_admin_metadata(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_admin_meta_keys: AdministrationKeys,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
    ):
        """Can verify dumped records do not include administrative metadata."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE = PropertyMock(
            return_value=fx_admin_meta_keys.encryption_private
        )
        type(mock_config).ADMIN_METADATA_SIGNING_KEY_PUBLIC = PropertyMock(
            return_value=fx_admin_meta_keys.signing_public
        )
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        value_admin = Administration(id=fx_revision_model_min.file_identifier)
        set_admin(keys=fx_admin_meta_keys, record=fx_revision_model_min, admin_meta=value_admin)

        exporter = IsoXmlExporter(meta=meta, logger=fx_logger, s3=fx_s3_client, record=fx_revision_model_min)

        result = exporter.dumps()
        assert "<gmi:MI_Metadata" in result
        assert "administrative_metadata" not in result


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
            exports_path = base_path.joinpath("records")
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=base_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = IsoXmlHtmlExporter(meta=meta, logger=fx_logger, s3=fx_s3_client, record=fx_revision_model_min)
        expected = exports_path.joinpath(f"{fx_revision_model_min.file_identifier}.html")

        assert isinstance(exporter, IsoXmlHtmlExporter)
        assert exporter.name == "ISO XML HTML"
        assert exporter._export_path == expected

    def test_dumps(self, fx_exporter_iso_xml_html: IsoXmlHtmlExporter):
        """Can apply stylesheet to string from IsoXmlExporter."""
        expected = "<html xmlns:gco"
        result = fx_exporter_iso_xml_html.dumps()
        assert expected in result
