import logging
from pathlib import Path

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput


class TestRecordIsoJsonOutput:
    """Test ISO record JSON output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision):
        """Can create a record JSON output."""
        output = RecordIsoJsonOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)
        assert isinstance(output, RecordIsoJsonOutput)
        assert output.name == "Record ISO JSON"

    def test_outputs(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision
    ):
        """Can generate site content items."""
        output = RecordIsoJsonOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)
        results = output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        assert '{\n  "$schema": "https://' in result.content
        assert result.path == Path(f"records/{fx_revision_model_min.file_identifier}.json")
        assert result.media_type == "application/json"
        assert result.object_meta == {
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
        }


class TestRecordIsoXmlOutput:
    """Test ISO record XML output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision):
        """Can create a record XML output."""
        output = RecordIsoXmlOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)
        assert isinstance(output, RecordIsoXmlOutput)
        assert output.name == "Record ISO XML"

    @pytest.mark.parametrize("trusted", [False, True])
    def test_content_trusted(
        self, fx_record_iso_xml_output: RecordIsoXmlOutput, fx_admin_meta_keys: AdministrationKeys, trusted: bool
    ):
        """Can strip or retain administration metadata based on trusted context status."""
        value_admin = AdministrationMetadata(id=fx_record_iso_xml_output._record.file_identifier)
        set_admin(keys=fx_admin_meta_keys, record=fx_record_iso_xml_output._record, admin_meta=value_admin)
        fx_record_iso_xml_output._strip_admin = not trusted

        result = fx_record_iso_xml_output._content
        assert "<gmi:MI_Metadata" in result
        if trusted:
            assert "admin_metadata" in result
        else:
            assert "admin_metadata" not in result

    def test_outputs(
        self,
        fx_record_iso_xml_output: RecordIsoXmlOutput,
        fx_export_meta: ExportMeta,
        fx_revision_model_min: RecordRevision,
    ):
        """Can generate site content items."""
        results = fx_record_iso_xml_output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        assert "<gmi:MI_Metadata" in result.content
        assert result.path == Path(f"records/{fx_revision_model_min.file_identifier}.xml")
        assert result.media_type == "application/xml"
        assert result.object_meta == {
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
        }


class TestRecordIsoHtmlOutput:
    """Test ISO record HTML output."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision):
        """Can create a record HTML output."""
        output = RecordIsoHtmlOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)
        assert isinstance(output, RecordIsoHtmlOutput)
        assert output.name == "Record ISO HTML"

    def test_outputs(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision
    ):
        """Can generate site content items."""
        output = RecordIsoHtmlOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)
        results = output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        assert "<html xmlns:gco" in result.content
        assert result.path == Path(f"records/{fx_revision_model_min.file_identifier}.html")
        assert result.media_type == "text/html"
        assert result.object_meta == {
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
        }

    @pytest.mark.cov()
    def test_existing_transform(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision
    ):
        """Can use an existing transform if provided."""
        transform = RecordIsoHtmlOutput.create_xslt_transformer()
        output = RecordIsoHtmlOutput(
            logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min, transform=transform
        )
        results = output.outputs
        assert len(results) == 1
