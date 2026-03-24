import logging

import pytest

from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.outputs.base import OutputBase, OutputRecord, OutputRecords, OutputSite
from lantern.stores.base import SelectRecordsProtocol
from tests.resources.outputs.fake_outputs import FakeOutputBase, FakeOutputRecord, FakeOutputRecords, FakeOutputSite


class TestBaseOutput:
    """Test base output via fake output class."""

    @pytest.mark.cov()
    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create an output."""
        base = FakeOutputBase(logger=fx_logger, meta=fx_export_meta)

        assert isinstance(base, OutputBase)
        assert base.name == "Fake Base"
        assert base._object_meta == {}
        assert base.outputs == []


class TestSiteOutput:
    """Test site output via fake output class."""

    @pytest.mark.cov()
    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site output."""
        site = FakeOutputSite(logger=fx_logger, meta=fx_export_meta)

        assert isinstance(site, OutputSite)
        assert site._jinja is not None


class TestRecordOutput:
    """Test record output via fake output class."""

    @pytest.mark.cov()
    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision):
        """Can create a record output."""
        record = FakeOutputRecord(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)

        assert isinstance(record, OutputRecord)

    @pytest.mark.parametrize("trusted", [False, True])
    def test_strip_admin(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_revision_model_min: RecordRevision,
        trusted: bool,
    ):
        """Can determine whether admin metadata should be stripped from a record within output."""
        fx_export_meta.trusted = trusted
        record = FakeOutputRecord(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)

        assert record._strip_admin != trusted


class TestRecordsOutput:
    """Test records output via fake output class."""

    @pytest.mark.cov()
    def test_init(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records: SelectRecordsProtocol
    ):
        """Can create a records output."""
        record = FakeOutputRecords(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records)
        assert isinstance(record, OutputRecords)
