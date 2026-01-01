import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from lantern.exporters.base import (
    Exporter,
    ResourceExporter,
    ResourcesExporter,
)
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordsProtocol
from tests.resources.exporters.fake_exporter import FakeExporter, FakeResourceExporter, FakeResourcesExporter


class TestBaseExporter:
    """Test base exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create an Exporter."""
        s3_client = mocker.MagicMock()

        base = FakeExporter(logger=fx_logger, meta=fx_export_meta, s3=s3_client)

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


class TestBaseResourcesExporter:
    """Test base resources exporter."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_s3_client: S3Client,
        fx_select_records: SelectRecordsProtocol,
    ):
        """Can create an Exporter."""
        exporter = FakeResourcesExporter(
            logger=fx_logger,
            meta=fx_export_meta,
            s3=fx_s3_client,
            select_records=fx_select_records,
        )
        assert isinstance(exporter, ResourcesExporter)


class TestBaseResourceExporter:
    """Test base resource exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
    ):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = FakeResourceExporter(
            logger=fx_logger,
            meta=meta,
            s3=fx_s3_client,
            record=fx_revision_model_min,
            export_base=output_path.joinpath("x"),
            export_name="x.txt",
        )
        assert isinstance(exporter, ResourceExporter)

    def test_init_invalid_base_path(self, fx_exporter_resource_base: ResourceExporter):
        """Cannot create an ItemBase with a base path that isn't relative to overall output_path."""
        with TemporaryDirectory() as tmp_path_exporter:
            alt_path = Path(tmp_path_exporter)
        with pytest.raises(ValueError, match=r"Export base must be relative to EXPORT_PATH."):
            FakeResourceExporter(
                logger=fx_exporter_resource_base._logger,
                meta=fx_exporter_resource_base._meta,
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

        key = result["Contents"][0]["Key"]
        result2 = fx_exporter_resource_base._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        meta_keys = ["file_identifier", "file_revision"]
        assert all(key in result2["Metadata"] for key in meta_keys)

    def test_publish_unknown_media_type(self, fx_s3_bucket_name: str, fx_exporter_resource_base: ResourceExporter):
        """Can write output with default media type where unknown to an object."""
        fx_exporter_resource_base._export_path = fx_exporter_resource_base._export_path / "x.unknown"
        fx_exporter_resource_base.publish()

        result = fx_exporter_resource_base._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key="x/x.txt/x.unknown")
        assert result["ContentType"] == "application/octet-stream"
