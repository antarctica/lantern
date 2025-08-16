import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from lantern.exporters.base import Exporter, ResourceExporter, S3Utils, get_record_aliases
from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.item.base.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from tests.resources.exporters.fake_exporter import FakeExporter, FakeResourceExporter


class TestS3Utils:
    """Test S3 utility methods."""

    def test_init(self, fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str):
        """Can create instance."""
        with TemporaryDirectory() as tmp_path:
            path = Path(tmp_path)

        s3_utils = S3Utils(s3=fx_s3_client, logger=fx_logger, s3_bucket=fx_s3_bucket_name, relative_base=path)
        assert isinstance(s3_utils, S3Utils)

    def test_calc_s3_key(self, fx_s3_utils: S3Utils):
        """Can get S3 key from path relative to site base."""
        expected = "x/y/z.txt"
        path = fx_s3_utils._relative_base.joinpath(expected)

        actual = fx_s3_utils.calc_key(path=path)
        assert actual == expected

    def test_upload_content(self, caplog: pytest.LogCaptureFixture, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can write output to an object at a low level."""
        expected = "x"

        fx_s3_utils.upload_content(key=expected, content_type="text/plain", body="x")

        result = fx_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1
        result = result["Contents"][0]
        assert result["Key"] == expected
        assert f"s3://{fx_s3_bucket_name}/{expected}" in caplog.text

    def test_upload_content_redirect(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can write output to an object with an object redirect."""
        key = "x"
        expected = "y"

        fx_s3_utils.upload_content(key=key, content_type="text/plain", body="x", redirect="y")

        result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert result["WebsiteRedirectLocation"] == expected

    def test_upload_package_resources(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can upload package resources to S3 bucket."""
        expected = "static/xsl/iso-html/xml-to-html-ISO.xsl"
        fx_s3_utils.upload_package_resources(
            src_ref="lantern.resources.xsl.iso-html",
            base_key="static/xsl/iso-html",
        )

        result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_upload_package_resources_exists(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can keep existing objects if already copied to S3 bucket from package resources."""
        src_ref = "lantern.resources.xsl.iso-html"
        base_key = "static/xsl/iso-html"
        key = "static/xsl/iso-html/xml-to-html-ISO.xsl"

        fx_s3_utils.upload_package_resources(src_ref=src_ref, base_key=base_key)
        initial = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)

        fx_s3_utils.upload_package_resources(src_ref=src_ref, base_key=base_key)
        repeat = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert initial["LastModified"] == repeat["LastModified"]

    def test_empty_bucket(self, caplog: pytest.LogCaptureFixture, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can empty all objects in bucket."""
        fx_s3_utils.upload_content(key="x", content_type="text/plain", body="x")
        result = fx_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

        fx_s3_utils.empty_bucket()
        result = fx_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert "contents" not in result


class TestBaseExporter:
    """Test base exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()

        base = FakeExporter(config=mock_config, logger=fx_logger, s3=s3_client)

        assert isinstance(base, Exporter)

    def test_dump_package_resources(self, fx_exporter_base: Exporter):
        """Can copy package resources to directory if not already present."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        src_ref = "lantern.resources.xsl.iso-html"
        dest_path = output_path / "xsl" / "iso-html"

        fx_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)

        assert dest_path.exists()

    @pytest.mark.cov()
    def test_dump_package_resources_repeat(self, fx_exporter_base: Exporter):
        """Can skip coping package resources to directory if already present."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        src_ref = "lantern.resources.xsl.iso-html"
        dest_path = output_path / "xsl" / "iso-html"

        fx_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)
        init_time = dest_path.stat().st_mtime

        fx_exporter_base._dump_package_resources(src_ref=src_ref, dest_path=dest_path)
        rpt_time = dest_path.stat().st_mtime

        assert init_time == rpt_time


class TestBaseResourceExporter:
    """Test base resource exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_exporter_base: Exporter,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_record_minimal_item: Record,
    ):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        fx_exporter_base._config = mock_config

        exporter = FakeResourceExporter(
            config=mock_config,
            logger=fx_logger,
            s3=fx_s3_client,
            record=fx_record_minimal_item,
            export_base=output_path.joinpath("x"),
            export_name="x.txt",
        )
        assert isinstance(exporter, ResourceExporter)

    def test_invalid_record(self, fx_exporter_resource_base: ResourceExporter, fx_record_minimal_iso: Record):
        """Cannot create an ItemBase with an invalid record."""
        with pytest.raises(ValueError, match="File identifier must be set to export record."):
            FakeResourceExporter(
                config=fx_exporter_resource_base._config,
                logger=fx_exporter_resource_base._logger,
                s3=fx_exporter_resource_base._s3_client,
                record=fx_record_minimal_iso,
                export_base=fx_exporter_resource_base._export_path.parent,
                export_name="x",
            )

    def test_init_invalid_base_path(self, fx_exporter_resource_base: ResourceExporter):
        """Cannot create an ItemBase with a base path that isn't relative to overall output_path."""
        with TemporaryDirectory() as tmp_path_exporter:
            alt_path = Path(tmp_path_exporter)
        with pytest.raises(ValueError, match="Export base must be relative to EXPORT_PATH."):
            FakeResourceExporter(
                config=fx_exporter_resource_base._config,
                logger=fx_exporter_resource_base._logger,
                s3=fx_exporter_resource_base._s3_client,
                record=fx_exporter_resource_base._record,
                export_base=alt_path,
                export_name="x",
            )

    def test_export(self, fx_exporter_resource_base: ResourceExporter):
        """Can write output to a file at a high level."""
        fx_exporter_resource_base.export()
        assert fx_exporter_resource_base._export_path.exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_exporter_resource_base: ResourceExporter):
        """Can write output to an object at a high level."""
        fx_exporter_resource_base.publish()

        result = fx_exporter_resource_base._s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

    def test_publish_unknown_media_type(self, fx_s3_bucket_name: str, fx_exporter_resource_base: ResourceExporter):
        """Can write output with default media type where unknown to an object."""
        fx_exporter_resource_base._export_path = fx_exporter_resource_base._export_path / "x.unknown"
        fx_exporter_resource_base.publish()

        result = fx_exporter_resource_base._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key="x/x.txt/x.unknown")
        assert result["ContentType"] == "application/octet-stream"


class TestGetRecordAliases:
    """Test get_record_aliases function."""

    def test_get_record_aliases(self, fx_record_minimal_item: Record):
        """Can get any aliases in a record."""
        alias = Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)

        fx_record_minimal_item.identification.identifiers.append(alias)
        result = get_record_aliases(fx_record_minimal_item)
        assert len(result) == 1
        assert result[0] == alias
