import logging

from mypy_boto3_s3 import S3Client

from lantern.exporters.base import ResourceExporter
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta


class JsonExporter(ResourceExporter):
    """
    Data Catalogue / Metadata Library JSON configuration exporter.

    Exports a Record as JSON using the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema [1].

    Intended for interoperability within the BAS Metadata ecosystem.

    [1] https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client, record: RecordRevision) -> None:
        export_base = meta.export_path / "records"
        export_name = f"{record.file_identifier}.json"
        super().__init__(
            logger=logger, meta=meta, s3=s3, record=record, export_base=export_base, export_name=export_name
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "BAS JSON"

    def dumps(self) -> str:
        """Encode record as data catalogue record config in JSON."""
        return self._record.dumps_json()
