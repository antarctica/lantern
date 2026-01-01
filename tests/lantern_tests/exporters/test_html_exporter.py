import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from boto3 import client as S3Client  # noqa: N812
from pytest_mock import MockerFixture

from lantern.exporters.html import HtmlAliasesExporter, HtmlExporter
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordProtocol


class TestHtmlExporter:
    """Test Data Catalogue HTML exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
        fx_select_record: SelectRecordProtocol,
    ):
        """Can create an HTML Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")
        expected = output_path / "items" / f"{fx_revision_model_min.file_identifier}/index.html"

        exporter = HtmlExporter(
            meta=meta, logger=fx_logger, s3=fx_s3_client, record=fx_revision_model_min, select_record=fx_select_record
        )

        assert isinstance(exporter, HtmlExporter)
        assert exporter.name == "Item HTML"
        assert exporter._export_path == expected

    @pytest.mark.parametrize("expected", [ItemCatalogue, ItemCataloguePhysicalMap])
    def test_item_class(
        self,
        fx_exporter_html: HtmlExporter,
        fx_item_config_min_physical_map: dict,
        expected: type[ItemCatalogue],
    ):
        """Can determine which Data Catalogue item class to use based on record."""
        if expected == ItemCataloguePhysicalMap:
            fx_exporter_html._record = RecordRevision.loads(fx_item_config_min_physical_map)

        result = fx_exporter_html._item_class()
        assert result == expected

    def test_dumps(self, fx_exporter_html: HtmlExporter):
        """Can encode record as a form of Data Catalogue item page."""
        result = fx_exporter_html.dumps()
        assert "<!DOCTYPE html>" in result


class TestHtmlAliasesExporter:
    """Test HTML alias redirect exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_s3_bucket_name: str,
        fx_s3_client: S3Client,
        fx_revision_model_min: RecordRevision,
    ):
        """Can create an HTML alias Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = HtmlAliasesExporter(meta=meta, logger=fx_logger, s3=fx_s3_client, record=fx_revision_model_min)

        assert isinstance(exporter, HtmlAliasesExporter)
        assert exporter.name == "Item Aliases"

    def test_get_aliases(self, fx_exporter_html_alias: HtmlAliasesExporter):
        """Can process any alias identifiers in record."""
        result = fx_exporter_html_alias._get_aliases()
        assert result == ["datasets/x"]

    def test_dumps(self, fx_exporter_html_alias: HtmlAliasesExporter):
        """Can generate fallback redirection page."""
        expected = fx_exporter_html_alias._record.file_identifier

        result = fx_exporter_html_alias.dumps()
        assert "<!DOCTYPE html>" in result
        assert f'refresh" content="0;url=/items/{expected}' in result

    def test_export(self, fx_exporter_html_alias: HtmlAliasesExporter):
        """Can write fallback redirection page to a file."""
        expected = fx_exporter_html_alias._site_base / "datasets" / "x" / "index.html"

        fx_exporter_html_alias.export()
        assert expected.exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_exporter_html_alias: HtmlAliasesExporter):
        """Can upload fallback redirection page as a bucket object with redirect metadata."""
        expected = "/items/x/index.html"
        fx_exporter_html_alias.publish()

        result = fx_exporter_html_alias._s3_client.get_object(Bucket=fx_s3_bucket_name, Key="datasets/x/index.html")
        assert result["WebsiteRedirectLocation"] == expected
