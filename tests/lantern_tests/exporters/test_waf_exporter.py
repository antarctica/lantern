import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from lxml import etree
from pytest_mock import MockerFixture

from lantern.exporters.waf import WebAccessibleFolderExporter
from lantern.models.site import ExportMeta
from tests.conftest import _get_record_open


class TestWebAccessibleFolderExporter:
    """Test web accessible folder exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = WebAccessibleFolderExporter(meta=meta, s3=s3_client, logger=fx_logger, get_record=_get_record_open)

        assert isinstance(exporter, WebAccessibleFolderExporter)
        assert exporter.name == "Web Accessible Folder"

    def test_dumps(self, fx_exporter_waf_sel: WebAccessibleFolderExporter):
        """Can dump WAF index."""
        html = BeautifulSoup(fx_exporter_waf_sel._dumps(), parser="html.parser", features="lxml")
        for file_identifier in fx_exporter_waf_sel.selected_identifiers:
            link = html.find("a", string=file_identifier)
            assert link is not None

    def test_export(self, fx_exporter_waf_sel: WebAccessibleFolderExporter):
        """Can export WAF to a local directory."""
        site_path = fx_exporter_waf_sel._meta.export_path
        expected = site_path / "waf" / "iso-19139-all" / "index.html"

        fx_exporter_waf_sel.export()

        assert expected.exists()

    def test_publish(self, fx_exporter_waf_sel: WebAccessibleFolderExporter, fx_s3_bucket_name: str):
        """Can publish WAF to S3."""
        site_path = fx_exporter_waf_sel._meta.export_path
        expected = "waf/iso-19139-all/index.html"

        fx_exporter_waf_sel.publish()

        output = fx_exporter_waf_sel._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=fx_exporter_waf_sel._s3_utils.calc_key(site_path.joinpath(expected)),
        )
        assert output["ResponseMetadata"]["HTTPStatusCode"] == 200

    @staticmethod
    def _parse_waf(base_url: str, content: str) -> list[dict[str, str]]:
        """
        `_parse_waf` method from PyCSW, modified to run standalone and only to collect record references.

        Changes:
        - function signature changed to:
          - take HTML content string to avoid HTTP request
          - rename record to base_url for clarity
          - add return type hint
        - `content = util.http_request("GET", record)` removed to avoid HTTP request
        - logging calls removed
        - removed logic to fetch discovered records as this is out of scope
        - refactored `recobj` objects to simple dicts with source keys only

        Linting violations are ignored here as this is vendored code.

        Source: https://github.com/geopython/pycsw/blob/2.6/pycsw/core/metadata.py#L261
        """
        etree.XMLParser(resolve_entities=False)
        record = base_url

        recobjs = []

        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(content, parser)
        except Exception as err:
            raise Exception("Could not parse WAF: %s" % str(err)) from err  # noqa: TRY002, UP031

        up = urlparse(record)
        links = []

        for link in tree.xpath("//a/@href"):
            link = link.strip()
            if not link:
                continue
            if link.find("?") != -1:
                continue
            if not link.endswith(".xml"):
                continue
            if "/" in link:  # path is embedded in link
                if link[-1] == "/":  # directory, skip
                    continue
                if link[0] == "/":
                    # strip path of WAF URL
                    link = "%s://%s%s" % (up.scheme, up.netloc, link)  # noqa: UP031
            else:  # tack on href to WAF URL
                link = "%s/%s" % (record, link)  # noqa: UP031
            links.append(link)

        for link in links:
            recobj = {"source": link}
            recobjs.append(recobj)

        return recobjs

    def test_harvest(self, fx_exporter_waf_sel: WebAccessibleFolderExporter):
        """
        Can parse WAF index.

        Using the `_parse_waf` method from PyCSW - https://github.com/geopython/pycsw/blob/2.6/pycsw/core/metadata.py#L261
        """
        unexpected = "https://invalid.com"
        results = self._parse_waf(base_url=unexpected, content=fx_exporter_waf_sel._dumps())
        assert len(results) == 1
        assert unexpected not in results[0]
