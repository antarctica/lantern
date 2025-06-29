import logging
from json import dumps as json_dumps
from pathlib import Path

from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import ResourceExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record


class JsonExporter(ResourceExporter):
    """
    Data Catalogue / Metadata Library JSON configuration exporter.

    Exports a Record as JSON using the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema [1].

    Intended for interoperability within the BAS Metadata ecosystem.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client, record: Record, export_base: Path) -> None:
        export_name = f"{record.file_identifier}.json"
        super().__init__(
            config=config, logger=logger, s3=s3, record=record, export_base=export_base, export_name=export_name
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "BAS JSON"

    def dumps(self) -> str:
        """Encode record as data catalogue record config in JSON."""
        return json_dumps(self._record.dumps(), indent=2)
