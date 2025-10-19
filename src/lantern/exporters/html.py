import logging

# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from collections.abc import Callable

from mypy_boto3_s3 import S3Client

from lantern.exporters.base import ResourceExporter, get_jinja_env, get_record_aliases, prettify_html
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta


class HtmlExporter(ResourceExporter):
    """
    Data Catalogue HTML item exporter.

    Exports a Record as ItemCatalogue HTML.

    Intended as the primary human-readable representation of a record.
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        record: RecordRevision,
        get_record: Callable[[str], RecordRevision],
    ) -> None:
        """
        Initialise.

        `get_record` requires a callable to get items related to the subject record.
        """
        export_base = meta.export_path / "items" / record.file_identifier
        export_name = "index.html"
        super().__init__(
            logger=logger, meta=meta, s3=s3, record=record, export_base=export_base, export_name=export_name
        )
        self._get_record = get_record
        self._jinja = get_jinja_env()
        self._template_path = "_views/item.html.j2"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Item HTML"

    def _item_class(self) -> type[ItemCatalogue]:
        """Get the ItemCatalogue (sub-)class to use for this record."""
        if ItemCataloguePhysicalMap.matches(self._record):
            return ItemCataloguePhysicalMap
        return ItemCatalogue

    def dumps(self) -> str:
        """Encode record as data catalogue item in HTML."""
        item_class = self._item_class()
        item = item_class(
            site_meta=self._meta.site_metadata,
            record=self._record,
            admin_meta_keys=self._meta.admin_meta_keys,
            trusted_context=self._meta.trusted,
            get_record=self._get_record,
        )

        raw = self._jinja.get_template(self._template_path).render(item=item, meta=item.site_metadata)
        return prettify_html(raw)


class HtmlAliasesExporter(ResourceExporter):
    """
    HTML aliases exporter.

    Creates redirects back to Data Catalogue item pages for any aliases set within a Record.

    Uses S3 object redirects with a minimal HTML page as a fallback.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client, record: RecordRevision) -> None:
        """
        Initialise.

        The `export_name` parameter required by the base Exporter is not used by this class, its value is not used.

        The `export_base` parameter MUST be the root of the overall site/catalogue output directory, so aliases under
        various prefixes can be generated.
        """
        export_base = meta.export_path
        export_name = f"--{record.file_identifier}--"
        self._site_base = export_base
        super().__init__(
            logger=logger, meta=meta, s3=s3, record=record, export_base=export_base, export_name=export_name
        )

    def _get_aliases(self) -> list[str]:
        """Get optional aliases for record as relative file paths / S3 keys."""
        identifiers = get_record_aliases(self._record)
        return [(identifier.href or "").replace(f"https://{CATALOGUE_NAMESPACE}/", "") for identifier in identifiers]

    @property
    def target(self) -> str:
        """Redirect location."""
        return f"/items/{self._record.file_identifier}/"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Item Aliases"

    def dumps(self) -> str:
        """Generate redirect page for record."""
        html = ET.Element("html", attrib={"lang": "en-GB"})
        head = ET.SubElement(html, "head")
        title = ET.SubElement(head, "title")
        title.text = "BAS Data Catalogue"
        ET.SubElement(head, "meta", attrib={"http-equiv": "refresh", "content": f"0;url={self.target}"})
        body = ET.SubElement(html, "body")
        a = ET.SubElement(body, "a", attrib={"href": self.target})
        a.text = "Click here if you are not redirected after a few seconds."
        html_str = ET.tostring(html, encoding="unicode", method="html")
        return f"<!DOCTYPE html>\n{html_str}"

    def export(self) -> None:
        """Write redirect pages for each alias to export directory."""
        for alias in self._get_aliases():
            alias_path = self._export_path.parent / alias / "index.html"
            alias_path.parent.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Writing file: {alias_path.resolve()}")
            with alias_path.open("w") as alias_file:
                alias_file.write(self.dumps())

    def publish(self) -> None:
        """Write redirect pages with redirect headers to S3."""
        location = f"{self.target}index.html"
        for alias in self._get_aliases():
            self._s3_utils.upload_content(
                key=f"{alias}/index.html", content_type="text/html", body=self.dumps(), redirect=location
            )
