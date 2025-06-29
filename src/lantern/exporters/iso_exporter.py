import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord, MetadataRecordConfigV4
from bas_metadata_library.standards.iso_19115_common.utils import _decode_date_properties
from lxml.etree import XSLT, ElementTree, fromstring, tostring
from lxml.etree import parse as parse_xml
from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter as BaseExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import ResourceExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class IsoXmlExporter(ResourceExporter):
    """
    ISO 19115 XML exporter.

    Exports a Record as ISO 19115/19139 using the BAS Metadata Library [1].

    Intended for interoperability with clients that prefer ISO XML, or need access to the full underlying record.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client, record: Record, export_base: Path) -> None:
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
        configuration = MetadataRecordConfigV4(**_decode_date_properties(self._record.dumps()))
        record = MetadataRecord(configuration=configuration)
        return record.generate_xml_document().decode()


class IsoXmlHtmlExporter(ResourceExporter):
    """
    ISO 19115 XML (HTML) exporter.

    Exports a Record as ISO 19115/19139 using an XML stylesheet [1] to present as a low-level HTML representation of
    the record, preserving ISO 19115 structure and terminology without needing to interpret raw XML syntax.

    Uses a server-side transformation to avoid loading XML stylesheets client side and overriding media types.

    Intended for human inspection of ISO records, typically for evaluation or debugging.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#iso-html
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client, record: Record, export_base: Path) -> None:
        """Initialise exporter."""
        export_name = f"{record.file_identifier}.html"
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name=export_name
        )
        self._xsl_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.xsl"

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
            xsl_doc = parse_xml(entrypoint_path)  # noqa: S320

            record_xml = IsoXmlExporter(
                config=self._config,
                logger=self._logger,
                s3=self._s3_client,
                record=self._record,
                export_base=self._export_path.parent,
            ).dumps()
            record_doc = ElementTree(fromstring(record_xml.encode()))  # noqa: S320

            transform = XSLT(xsl_doc)
            return tostring(transform(record_doc), method="html", pretty_print=True, encoding="utf-8").decode()
