import logging

from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config
from lantern.exporters.base import Exporter, ResourceExporter
from lantern.exporters.html import HtmlAliasesExporter, HtmlExporter
from lantern.exporters.json import JsonExporter
from lantern.exporters.xml import IsoXmlExporter, IsoXmlHtmlExporter
from lantern.lib.metadata_library.models.record import Record


class RecordsExporter(Exporter):
    """
    Data Catalogue records exporter.

    Combines format specific exporters for a set of records.

    Records and summaries handling is intentionally simple and not intended for large numbers of records.
    It will be replaced with a more capable record repository in the future.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(config=config, logger=logger, s3=s3)
        self._records: dict[str, Record] = {}

    def _get_record(self, identifier: str) -> Record:
        """
        Get record for a record identifier.

        Crude implementation of a record repository interface.
        """
        return self._records[identifier]

    def _get_html_exporter(self, record: Record) -> HtmlExporter:
        """Record as item HTML."""
        output_path = self._config.EXPORT_PATH / "items"
        return HtmlExporter(
            config=self._config,
            logger=self._logger,
            s3=self._s3_client,
            record=record,
            export_base=output_path,
            get_record=self._get_record,
        )

    def _get_html_aliases_exporter(self, record: Record) -> HtmlAliasesExporter:
        """Record aliases as redirects to item HTML."""
        output_path = self._config.EXPORT_PATH
        return HtmlAliasesExporter(
            config=self._config, logger=self._logger, s3=self._s3_client, record=record, site_base=output_path
        )

    def _get_json_exporter(self, record: Record) -> JsonExporter:
        """Record as BAS Metadata Library JSON."""
        output_path = self._config.EXPORT_PATH / "records"
        return JsonExporter(
            config=self._config, logger=self._logger, s3=self._s3_client, record=record, export_base=output_path
        )

    def _get_iso_xml_exporter(self, record: Record) -> IsoXmlExporter:
        """Record as ISO XML."""
        output_path = self._config.EXPORT_PATH / "records"
        return IsoXmlExporter(
            config=self._config, logger=self._logger, s3=self._s3_client, record=record, export_base=output_path
        )

    def _get_iso_xml_html_exporter(self, record: Record) -> IsoXmlHtmlExporter:
        """Record as ISO XML with HTML stylesheet."""
        output_path = self._config.EXPORT_PATH / "records"
        return IsoXmlHtmlExporter(
            config=self._config, logger=self._logger, s3=self._s3_client, record=record, export_base=output_path
        )

    def _get_exporters(self, record: Record) -> list[ResourceExporter]:
        """Get exporters for record."""
        return [
            self._get_html_exporter(record),
            self._get_html_aliases_exporter(record),
            self._get_json_exporter(record),
            self._get_iso_xml_exporter(record),
            self._get_iso_xml_html_exporter(record),
        ]

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Records"

    def loads(self, records: list[Record]) -> None:
        """Populate exporter."""
        self._records = {record.file_identifier: record for record in records}

    def export_record(self, file_identifier: str) -> None:
        """Export a record to a directory."""
        self._logger.info(f"Exporting record '{file_identifier}'")
        record = self._records[file_identifier]
        for exporter in self._get_exporters(record):
            self._logger.debug(f"Exporting record '{file_identifier}' using {exporter.name} exporter")
            exporter.export()

    def publish_record(self, file_identifier: str) -> None:
        """Publish a records to S3."""
        self._logger.info(f"Publishing record '{file_identifier}'")
        record = self._records[file_identifier]
        for exporter in self._get_exporters(record):
            self._logger.debug(f"Publishing record '{file_identifier}' using {exporter.name} exporter")
            exporter.publish()

    def export(self) -> None:
        """Export all records to a directory."""
        for file_identifier in self._records:
            self.export_record(file_identifier)

    def publish(self) -> None:
        """Publish all records to S3."""
        for file_identifier in self._records:
            self.publish_record(file_identifier)
