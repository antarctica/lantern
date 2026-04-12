import logging
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from lantern.models.checks import CheckType
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
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
        assert base.check_type == CheckType.NONE
        assert base._object_meta == {}
        assert base.content == []

    def test_checks(
        self, mocker: MockerFixture, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_site_content: SiteContent
    ):
        """Can use default logic to generate checks from content."""
        base = FakeOutputBase(logger=fx_logger, meta=fx_export_meta)
        mocker.patch.object(type(base), "content", new_callable=PropertyMock, return_value=[fx_site_content])

        results = base.checks
        assert len(results) == 1


class TestSiteOutput:
    """Test site output via fake output class."""

    @pytest.mark.cov()
    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta):
        """Can create a site output."""
        site = FakeOutputSite(logger=fx_logger, meta=fx_export_meta, name="Fake Base", check_type=CheckType.NONE)

        assert isinstance(site, OutputSite)
        assert site._jinja is not None


class TestRecordOutput:
    """Test record output via fake output class."""

    @pytest.mark.cov()
    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision):
        """Can create a record output."""
        record = FakeOutputRecord(
            logger=fx_logger,
            meta=fx_export_meta,
            name="Fake Base",
            check_type=CheckType.NONE,
            record=fx_revision_model_min,
        )

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
        record = FakeOutputRecord(
            logger=fx_logger,
            meta=fx_export_meta,
            name="Fake Base",
            check_type=CheckType.NONE,
            record=fx_revision_model_min,
        )

        assert record._strip_admin != trusted


class TestRecordsOutput:
    """Test records output via fake output class."""

    @pytest.mark.cov()
    def test_init(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records: SelectRecordsProtocol
    ):
        """Can create a records output."""
        record = FakeOutputRecords(
            logger=fx_logger,
            meta=fx_export_meta,
            name="Fake Base",
            check_type=CheckType.NONE,
            select_records=fx_select_records,
        )
        assert isinstance(record, OutputRecords)
