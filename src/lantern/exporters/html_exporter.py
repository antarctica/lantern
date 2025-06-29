import logging
from collections.abc import Callable
from pathlib import Path

from mypy_boto3_s3 import S3Client

from lantern.config import Config
from lantern.exporters.base_exporter import ResourceExporter
from lantern.models.item.catalogue import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record import Record
from lantern.models.record.summary import RecordSummary


class HtmlExporter(ResourceExporter):
    """
    Data Catalogue HTML item exporter.

    Exports a Record as ItemCatalogue HTML.

    Intended as the primary human-readable representation of a record.
    """

    def __init__(
        self,
        config: Config,
        logger: logging.Logger,
        s3: S3Client,
        record: Record,
        export_base: Path,
        get_record_summary: Callable[[str], RecordSummary],
        get_record: Callable[[str], Record],
    ) -> None:
        """
        Initialise.

        `get_record_summary` requires a callable to get a RecordSummary for a given identifier (used for related items).
        """
        export_base = export_base / record.file_identifier
        export_name = "index.html"
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name=export_name
        )
        self._get_summary = get_record_summary
        self._get_record = get_record

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
        return item_class(
            config=self._config,
            record=self._record,
            get_record_summary=self._get_summary,
            get_record=self._get_record,
        ).render()


class HtmlAliasesExporter(ResourceExporter):
    """
    HTML aliases exporter.

    Creates redirects back to Data Catalogue item pages for any aliases set within a Record.

    Uses S3 object redirects with a minimal HTML page as a fallback.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client, record: Record, site_base: Path) -> None:
        """
        Initialise.

        The `export_base` and `export_name` parameters required by the base Exporter aren't used by this class. The
        values used can be ignored.

        The `site_base` parameter MUST be the root of the overall site/catalogue output directory, so aliases under
        various prefixes can be generated.
        """
        export_name = f"{record.file_identifier}.html"
        export_base = site_base
        self._site_base = site_base
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name=export_name
        )

    def _get_aliases(self) -> list[str]:
        """Get optional aliases for record as relative file paths / S3 keys."""
        identifiers = self._record.identification.identifiers.filter(namespace="alias.data.bas.ac.uk")
        return [identifier.href.replace("https://data.bas.ac.uk/", "") for identifier in identifiers]

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Item Aliases"

    def dumps(self) -> str:
        """Generate redirect page for record."""
        target = f"/items/{self._record.file_identifier}/"
        return f"""
<!DOCTYPE html>
<html lang="en-GB">
    <head><title>BAS Data Catalogue</title><meta http-equiv="refresh" content="0;url={target}" /></head>
    <body>Click <a href="{target}">here</a> if you are not redirected after a few seconds.</body>
</html>
        """

    def export(self) -> None:
        """Write redirect pages for each alias to export directory."""
        for alias in self._get_aliases():
            alias_path = self._site_base / alias / "index.html"
            alias_path.parent.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Writing file: {alias_path.resolve()}")
            with alias_path.open("w") as alias_file:
                alias_file.write(self.dumps())

    def publish(self) -> None:
        """Write redirect pages with redirect headers to S3."""
        location = f"/items/{self._record.file_identifier}/index.html"
        for alias in self._get_aliases():
            self._s3_utils.upload_content(
                key=f"{alias}/index.html", content_type="text/html", body=self.dumps(), redirect=location
            )
