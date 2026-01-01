import logging
from abc import ABC, abstractmethod
from mimetypes import guess_type
from pathlib import Path
from shutil import copytree

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from mypy_boto3_s3 import S3Client

from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordsProtocol
from lantern.utils import S3Utils


class Exporter(ABC):
    """
    Abstract base class for exporters.

    Exporters typically:
    - produce some form of content or output, typically for specific resources via a `dumps` method
    - persist this output as files, stored on a local file system and/or remote object store (AWS S3)

    Some providers act at a site level, such as SiteExporter (which coordinates other exporters).

    This base exporter class is intended to be generic with subclasses being more opinionated.

    Exporters include an ExportMetadata instance which extends SiteMetadata to provide both internal information such
    as the local export path and information intended for templates such as the build time.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client) -> None:
        """Initialise exporter."""
        self._logger = logger
        self._meta = meta
        self._s3_client = s3
        self._s3_utils = S3Utils(
            logger=logger,
            s3=self._s3_client,
            s3_bucket=self._meta.s3_bucket,
            relative_base=self._meta.export_path,
        )

    @staticmethod
    def _dump_package_resources(src_ref: str, dest_path: Path) -> None:
        """
        Copy package resources to directory.

        `src_ref` MUST be a reference to a directory within a Python package compatible with `importlib_resources.files`.
        All files within this directory will be copied to `dest_path`, any matching existing files will be overwritten.
        """
        if dest_path.exists():
            return

        with resources_as_file(resources_files(src_ref)) as resources_path:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            copytree(resources_path, dest_path)

    @property
    @abstractmethod
    def name(self) -> str:
        """Exporter name."""
        ...

    @abstractmethod
    def export(self) -> None:
        """Save dumped output to local export directory."""
        ...

    @abstractmethod
    def publish(self) -> None:
        """Save dumped output to remote S3 bucket."""
        ...


class ResourcesExporter(Exporter, ABC):
    """Base class for exporters handling multiple Record or Item instances."""

    def __init__(
        self, logger: logging.Logger, meta: ExportMeta, s3: S3Client, select_records: SelectRecordsProtocol
    ) -> None:
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._select_records: SelectRecordsProtocol = select_records


class ResourceExporter(Exporter, ABC):
    """Base class for exporters handling an individual Record or Item instance."""

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        record: RecordRevision,
        export_base: Path,
        export_name: str,
    ) -> None:
        """
        Initialise resource exporter.

        Where:
        - export_base is a directory for the exporter type
        - export_name is a name of the file to be created in export_base based on the associated record
        """
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._export_path = export_base.joinpath(export_name)
        self._validate(export_base)
        self._record = record

    def _validate(self, export_base: Path) -> None:
        """Validate exporter configuration."""
        try:
            _ = export_base.relative_to(self._meta.export_path)
        except ValueError as e:
            msg = "Export base must be relative to EXPORT_PATH."
            raise ValueError(msg) from e

    @abstractmethod
    def dumps(self) -> str:
        """Encode resource as a particular format."""
        ...

    def export(self) -> None:
        """Save dumped output to local export directory."""
        self._export_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger.debug(f"Writing file: {self._export_path.resolve()}")
        with self._export_path.open("w") as record_file:
            record_file.write(self.dumps())

    def publish(self) -> None:
        """Save dumped output to remote S3 bucket."""
        media_type = guess_type(self._export_path.name)[0] or "application/octet-stream"
        key = self._s3_utils.calc_key(self._export_path)
        meta = {"file_identifier": self._record.file_identifier, "file_revision": self._record.file_revision}
        self._s3_utils.upload_content(key=key, content_type=media_type, body=self.dumps(), meta=meta)
