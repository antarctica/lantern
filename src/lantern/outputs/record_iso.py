import logging
from pathlib import Path

from importlib_resources import files as resources_files
from lxml import etree

from lantern.models.checks import Check, CheckType, RecordChecks
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputRecord


class RecordIsoJsonOutput(OutputRecord):
    """
    ISO 19115 JSON Record output.

    Outputs a Record as BAS ISO 19115:2003 / 19115-2:2009 v4 JSON [1] via the BAS Metadata Library.

    Intended for interoperability within the BAS Metadata ecosystem.

    Supports trusted publishing (via export meta).

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, record: RecordRevision) -> None:
        super().__init__(
            logger=logger, meta=meta, name="Record ISO JSON", check_type=CheckType.RECORD_PAGES_JSON, record=record
        )

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {
            "file_identifier": self._record.file_identifier,
            "file_revision": self._record.file_revision,
        }

    @property
    def _content(self) -> str:
        """Encode record as BAS ISO JSON."""
        return self._record.dumps_json(strip_admin=self._strip_admin)

    @property
    def content(self) -> list[SiteContent]:
        """Output content for record."""
        return [
            SiteContent(
                content=self._content,
                path=Path("records") / f"{self._record.file_identifier}.json",
                media_type="application/json",
                object_meta=self._object_meta,
            )
        ]


class RecordIsoXmlOutput(OutputRecord):
    """
    ISO 19115 XML Record output.

    Outputs a Record as ISO 19139:2007 / 19139-2:2012 via the BAS Metadata Library.

    Intended for interoperability with clients that prefer ISO XML, or need access to the full underlying record.

    Attaches additional record based checks.

    Supports trusted publishing (via export meta).
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, record: RecordRevision) -> None:
        super().__init__(
            logger=logger, meta=meta, name="Record ISO XML", check_type=CheckType.RECORD_PAGES_XML, record=record
        )

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {
            "file_identifier": self._record.file_identifier,
            "file_revision": self._record.file_revision,
        }

    @property
    def _content(self) -> str:
        """Encode record as ISO 19139 XML."""
        return self._record.dumps_xml(strip_admin=self._strip_admin)

    @property
    def content(self) -> list[SiteContent]:
        """Output content for record."""
        return [
            SiteContent(
                path=Path("records") / f"{self._record.file_identifier}.xml",
                content=self._content,
                media_type="application/xml",
                object_meta=self._object_meta,
            )
        ]

    @property
    def checks(self) -> list[Check]:
        """
        Output checks.

        Includes additional checks generated from the contents of the record (e.g. DOIs and distributions).
        """
        checks = super().checks
        record_checks = RecordChecks(record=self._record)
        checks.extend(record_checks.checks)
        return checks


class RecordIsoHtmlOutput(OutputRecord):
    """
    ISO 19115 XML (HTML) Record output.

    Outputs a Record as ISO 19139 with an XML stylesheet [1] applied to present the structure of the record as HTML for
    improved readability.

    Returns the rendered HTML output after applying the stylesheet to avoid issues with loading XML stylesheets client
    side and overriding media types. Uses the RecordIsoXmlOutput to get input XML.

    Intended for human inspection of ISO records, typically for evaluation or debugging.

    Supports trusted publishing (via export meta).

    An existing XSLT transformer can be provided to avoid recreating on each run in parallel processing contexts.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#iso-html
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        record: RecordRevision,
        transform: etree.XSLT | None = None,
    ) -> None:
        super().__init__(
            logger=logger, meta=meta, name="Record ISO HTML", check_type=CheckType.RECORD_PAGES_HTML, record=record
        )
        self._transform = transform

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {
            "file_identifier": self._record.file_identifier,
            "file_revision": self._record.file_revision,
        }

    @staticmethod
    def create_xslt_transformer() -> etree.XSLT:
        """Create XSLT transformer for the ISO XML to HTML stylesheet."""
        combined = resources_files("lantern.resources.xsl").joinpath("xml-to-html-ISO-combined.xsl")
        xsl_bytes = combined.read_bytes()
        xsl_doc = etree.fromstring(xsl_bytes)
        return etree.XSLT(xsl_doc)

    def _apply_iso_html_xslt(self, record: RecordRevision) -> str:
        """
        Apply XSLT to record and return rendered output.

        Uses an existing XSLT transformer if available (for performance in parallel processing).
        """
        if self._transform is None:
            self._transform = self.create_xslt_transformer()

        # Build XML document from the record XML string
        record_xml = RecordIsoXmlOutput(logger=self._logger, meta=self._meta, record=record).content[0].content
        record_bytes = bytes(record_xml) if isinstance(record_xml, (bytes, bytearray)) else str(record_xml).encode()
        record_doc = etree.ElementTree(etree.fromstring(record_bytes))

        # Apply transformation
        result = self._transform(record_doc)
        return etree.tostring(result, method="html", pretty_print=True, encoding="utf-8").decode()

    @property
    def _content(self) -> str:
        """Encode record as ISO 19139 XML with HTML stylesheet."""
        return self._apply_iso_html_xslt(record=self._record)

    @property
    def content(self) -> list[SiteContent]:
        """Output content for record."""
        return [
            SiteContent(
                path=Path("records") / f"{self._record.file_identifier}.html",
                content=self._content,
                media_type="text/html",
                object_meta=self._object_meta,
            )
        ]
