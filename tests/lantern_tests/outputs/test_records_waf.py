import logging
from pathlib import Path

from bs4 import BeautifulSoup

from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.stores.base import SelectRecordsProtocol


class TestRecordsWafOutput:
    """Test Web Accessible Folder records output."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_select_records: SelectRecordsProtocol,
    ):
        """Can create a Web Accessible Folder output."""
        output = RecordsWafOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records)
        assert isinstance(output, RecordsWafOutput)
        assert output.name == "Web Accessible Folder"

    def test_content(self, fx_records_waf_output: RecordsWafOutput, fx_select_records_fixed: SelectRecordsProtocol):
        """Can generate WAF index."""
        fx_records_waf_output._select_records = fx_select_records_fixed
        html = BeautifulSoup(fx_records_waf_output._content, parser="html.parser", features="lxml")
        records = fx_records_waf_output._select_records()

        assert len(records) > 0
        for record in records:
            link = html.find("a", string=record.file_identifier)
            assert link is not None

    def test_outputs(self, fx_records_waf_output: RecordsWafOutput, fx_select_records_fixed: SelectRecordsProtocol):
        """Can generate site content items."""
        build_ref = "x"
        fx_records_waf_output._meta.build_repo_ref = build_ref
        fx_records_waf_output._select_records = fx_select_records_fixed

        results = fx_records_waf_output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        assert "html" in result.content
        assert result.path == Path("waf/iso-19139-all/index.html")
        assert result.media_type == "text/html"
        assert result.object_meta == {"build_ref": build_ref}
