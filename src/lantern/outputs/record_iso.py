from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from lxml import etree

from lantern.models.record.revision import RecordRevision
from lantern.models.site import SiteContent
from lantern.outputs.base import OutputRecord


class RecordIsoJsonOutput(OutputRecord):
    """
    ISO 19115 JSON Record output.

    Outputs a Record as BAS ISO 19115:2003 / 19115-2:2009 v4 JSON [1] via the BAS Metadata Library.

    Intended for interoperability within the BAS Metadata ecosystem.

    Supports trusted publishing (via export meta).

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas
    """

    @property
    def name(self) -> str:
        """Output name."""
        return "Record ISO JSON"

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
    def outputs(self) -> list[SiteContent]:
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

    Supports trusted publishing (via export meta).
    """

    @property
    def name(self) -> str:
        """Output name."""
        return "Record ISO XML"

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
    def outputs(self) -> list[SiteContent]:
        """Output content for record."""
        return [
            SiteContent(
                path=Path("records") / f"{self._record.file_identifier}.xml",
                content=self._content,
                media_type="application/xml",
                object_meta=self._object_meta,
            )
        ]


class RecordIsoHtmlOutput(OutputRecord):
    """
    ISO 19115 XML (HTML) Record output.

    Outputs a Record as ISO 19139 with an XML stylesheet [1] applied to present the structure of the record as HTML for
    improved readability.

    Returns the rendered HTML output after applying the stylesheet to avoid issues with loading XML stylesheets client
    side and overriding media types. Uses the RecordIsoXmlOutput to get input XML.

    Intended for human inspection of ISO records, typically for evaluation or debugging.

    Supports trusted publishing (via export meta).

    Note: This output class is very inefficient.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#iso-html
    """

    @property
    def name(self) -> str:
        """Output name."""
        return "Record ISO HTML"

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {
            "file_identifier": self._record.file_identifier,
            "file_revision": self._record.file_revision,
        }

    @staticmethod
    def _load_xsl(package_ref: str) -> TemporaryDirectory:
        """Copy XSL files from package to a temporary directory."""
        xsl_dir = TemporaryDirectory()
        xsl_path = Path(xsl_dir.name) / "xsl"
        with resources_as_file(resources_files(package_ref)) as resources_path:
            xsl_path.parent.mkdir(parents=True, exist_ok=True)
            copytree(resources_path, xsl_path)
        return xsl_dir

    def _apply_iso_html_xslt(self, record: RecordRevision) -> str:
        """Apply XSLT to record and return rendered output."""
        xsl_path = self._load_xsl(package_ref="lantern.resources.xsl")
        try:
            entrypoint_path = Path(xsl_path.name) / "xsl" / "iso-html" / "xml-to-html-ISO.xsl"
            xsl_doc = etree.parse(entrypoint_path)

            record_xml: str = RecordIsoXmlOutput(logger=self._logger, meta=self._meta, record=record).outputs[0].content  # ty:ignore[invalid-assignment]
            record_doc = etree.ElementTree(etree.fromstring(record_xml.encode()))

            transform = etree.XSLT(xsl_doc)
            return etree.tostring(transform(record_doc), method="html", pretty_print=True, encoding="utf-8").decode()
        finally:
            xsl_path.cleanup()

    @property
    def _content(self) -> str:
        """Encode record as ISO 19139 XML with HTML stylesheet."""
        return self._apply_iso_html_xslt(record=self._record)

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content for record."""
        return [
            SiteContent(
                path=Path("records") / f"{self._record.file_identifier}.html",
                content=self._content,
                media_type="text/html",
                object_meta=self._object_meta,
            )
        ]
