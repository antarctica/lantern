import logging
from pathlib import Path

import pytest

from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.site_index import SiteIndexOutput
from lantern.stores.base import SelectRecordsProtocol


class TestSiteIndexOutput:
    """
    Test site index output.

    This class is not tested comprehensively.
    """

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_select_records: SelectRecordsProtocol,
    ):
        """Can create a site index output."""
        output = SiteIndexOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records)
        assert isinstance(output, SiteIndexOutput)
        assert output.name == "Site Index"

    @pytest.mark.cov()
    def test_no_build_ref(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records_fixed: SelectRecordsProtocol
    ):
        """Can not include build ref where not in site meta."""
        fx_export_meta.build_repo_ref = None
        output = SiteIndexOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records_fixed)

        results = output.outputs
        assert len(results) == 1
        result = results[0]
        assert "build_ref" not in result.object_meta

    def test_outputs(
        self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records_fixed: SelectRecordsProtocol
    ):
        """Can generate site content items."""
        output = SiteIndexOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records_fixed)

        results = output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        assert "<!DOCTYPE html>" in result.content
        assert result.path == Path("-/index/index.html")
        assert result.media_type == "text/html"
