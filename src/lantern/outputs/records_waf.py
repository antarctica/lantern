import logging
from pathlib import Path

from lxml import etree as ET  # noqa: N812

from lantern.models.checks import CheckType
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputRecords
from lantern.stores.base import SelectRecordsProtocol


class RecordsWafOutput(OutputRecords):
    """
    Web Accessible Folder (WAF) records output.

    Generates a minimal HTML page listing links to ISO 19139 XML metadata for all records in a store.

    Intended for use by automated harvesting tools.

    Note: It is assumed these XML metadata records already exist
    (i.e. via the `lantern.outputs.records_iso.RecordIsoXmlOutput` output class).
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, select_records: SelectRecordsProtocol) -> None:
        super().__init__(
            logger=logger,
            meta=meta,
            name="Web Accessible Folder",
            check_type=CheckType.WAF_PAGES,
            select_records=select_records,
        )

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {"build_ref": self._meta.build_repo_ref} if self._meta.build_repo_ref else {}

    @property
    def _content(self) -> str:
        """
        Generate listing of selected records.

        Link URLs are fully qualified for external access.
        """
        time = self._meta.build_time.isoformat()

        html = ET.Element("html")
        body = ET.SubElement(html, "body")
        h1 = ET.SubElement(body, "h1")
        h1.text = "BAS Data Catalogue - Web Accessible Folder (WAF)"
        aside = ET.SubElement(body, "aside")
        p1 = ET.SubElement(aside, "p")
        p1.text = "This page contains links to ISO 19139 XML metadata records within this catalogue, for use by clients that harvest metadata records in bulk."
        p2 = ET.SubElement(aside, "p")
        p2.text = "This endpoint was last updated at "
        time_elem = ET.SubElement(p2, "time", attrib={"datetime": time})
        time_elem.text = time
        time_elem.tail = ". It is maintained by magic@bas.ac.uk."

        main = ET.SubElement(body, "main")
        ul = ET.SubElement(main, "ul")
        for record in self._select_records():
            fid = record.file_identifier
            li = ET.SubElement(ul, "li")
            a = ET.SubElement(li, "a", attrib={"href": f"{self._meta.base_url}/records/{fid}.xml"})
            a.text = fid

        return ET.tostring(html, encoding="unicode", method="html")

    @property
    def content(self) -> list[SiteContent]:
        """Output content for record."""
        return [
            SiteContent(
                content=self._content,
                path=Path("waf") / "iso-19139-all" / "index.html",
                media_type="text/html",
                object_meta=self._object_meta,
            )
        ]
