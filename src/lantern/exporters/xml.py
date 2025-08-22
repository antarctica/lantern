import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from lxml import etree
from mypy_boto3_s3 import S3Client

from lantern.config import Config
from lantern.exporters.base import Exporter as BaseExporter
from lantern.exporters.base import ResourceExporter
from lantern.models.record.revision import RecordRevision


class IsoXmlExporter(ResourceExporter):
    """
    ISO 19115 XML exporter.

    Exports a Record as ISO 19115/19139 using the BAS Metadata Library [1].

    Intended for interoperability with clients that prefer ISO XML, or need access to the full underlying record.
    """

    def __init__(
        self, config: Config, logger: logging.Logger, s3: S3Client, record: RecordRevision, export_base: Path
    ) -> None:
        export_name = f"{record.file_identifier}.xml"
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name=export_name
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "ISO XML"

    def dumps(self) -> str:
        """Encode record as XML using ISO 19139 schemas."""
        return self._record.dumps_xml()


class IsoXmlHtmlExporter(ResourceExporter):
    """
    ISO 19115 XML (HTML) exporter.

    Exports a Record as ISO 19115/19139 using an XML stylesheet [1] to present as a low-level HTML representation of
    the record, preserving ISO 19115 structure and terminology without needing to interpret raw XML syntax.

    Uses a server-side transformation to avoid loading XML stylesheets client side and overriding media types.

    Intended for human inspection of ISO records, typically for evaluation or debugging.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#iso-html
    """

    def __init__(
        self, config: Config, logger: logging.Logger, s3: S3Client, record: RecordRevision, export_base: Path
    ) -> None:
        """Initialise exporter."""
        export_name = f"{record.file_identifier}.html"
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name=export_name
        )
        self._xsl_src_ref = "lantern.resources.xsl"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "ISO XML HTML"

    def dumps(self) -> str:
        """
        Apply ISO 19115 HTML stylesheet to XML encoded record.

        Uses the output of the `IsoXmlExporter` as XML input.
        """
        # noinspection PyTypeChecker
        with TemporaryDirectory() as tmp_path:
            xsl_path = Path(tmp_path) / "xsl"
            BaseExporter._dump_package_resources(src_ref=self._xsl_src_ref, dest_path=xsl_path)

            entrypoint_path = xsl_path / "iso-html" / "xml-to-html-ISO.xsl"
            xsl_doc = etree.parse(entrypoint_path)

            record_xml = IsoXmlExporter(
                config=self._config,
                logger=self._logger,
                s3=self._s3_client,
                record=self._record,
                export_base=self._export_path.parent,
            ).dumps()
            record_doc = etree.ElementTree(etree.fromstring(record_xml.encode()))

            transform = etree.XSLT(xsl_doc)
            return etree.tostring(transform(record_doc), method="html", pretty_print=True, encoding="utf-8").decode()
