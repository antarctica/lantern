import logging

# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from collections.abc import Callable

from mypy_boto3_s3 import S3Client

from lantern.exporters.base import ResourcesExporter
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta


class WebAccessibleFolderExporter(ResourcesExporter):
    """
    Web Accessible Folder (WAF) exporter.

    Generates a minimal HTML page listing links to ISO 19139 XML metadata records generated elsewhere.
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        get_record: Callable[[str], RecordRevision],
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3, get_record=get_record)
        self._get_record = get_record
        self._export_path = self._meta.export_path / "waf" / "iso-19139-all" / "index.html"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Web Accessible Folder"

    def _dumps(self) -> str:
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
        for fid in self._selected_identifiers:
            li = ET.SubElement(ul, "li")
            a = ET.SubElement(li, "a", attrib={"href": f"{self._meta.base_url}/records/{fid}.xml"})
            a.text = fid

        return ET.tostring(html, encoding="unicode", method="html")

    def export(self) -> None:
        """Export listing to local directory."""
        self._export_path.parent.mkdir(parents=True, exist_ok=True)
        with self._export_path.open("w") as f:
            f.write(self._dumps())

    def publish(self) -> None:
        """Publish listing to S3."""
        index_key = self._s3_utils.calc_key(self._export_path)
        self._s3_utils.upload_content(key=index_key, content_type="text/html", body=self._dumps())
