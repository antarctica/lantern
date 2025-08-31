import logging
from abc import ABC, abstractmethod
from mimetypes import guess_type
from pathlib import Path
from shutil import copytree

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from mypy_boto3_s3 import S3Client

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record import Record
from lantern.models.record.const import ALIAS_NAMESPACE
from lantern.models.record.revision import RecordRevision


class S3Utils:
    """Wrapper around Boto S3 client with high-level and/or convenience methods."""

    def __init__(self, logger: logging.Logger, s3: S3Client, s3_bucket: str, relative_base: Path) -> None:
        self._logger = logger
        self._s3 = s3
        self._bucket = s3_bucket
        self._relative_base = relative_base

    def calc_key(self, path: Path) -> str:
        """
        Calculate `path` relative to `self._config.EXPORT_PATH`.

        E.g. `/data/site/html/123/index.html` gives `html/123/index.html` where EXPORT_PATH is `/data/site/`.
        """
        return str(path.relative_to(self._relative_base))

    def upload_content(
        self, key: str, content_type: str, body: str | bytes, redirect: str | None = None, meta: dict | None = None
    ) -> None:
        """
        Upload string or binary content as an S3 object.

        Optionally, a redirect can be set to redirect to another object as per [1].

        [1] https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata
        """
        params = {"Bucket": self._bucket, "Key": key, "Body": body, "ContentType": content_type}
        if isinstance(body, str):
            params["Body"] = body.encode("utf-8")
        if redirect is not None:
            params["WebsiteRedirectLocation"] = redirect
        if meta is not None:
            # noinspection PyTypeChecker
            params["Metadata"] = meta

        self._logger.debug(f"Writing key: s3://{self._bucket}/{key}")
        self._s3.put_object(**params)

    def upload_package_resources(self, src_ref: str, base_key: str) -> None:
        """
        Upload package resources as S3 objects if they do not already exist.

        `src_ref` MUST be a reference to a directory within a Python package compatible with `importlib_resources.files`.
        All files within this directory will be uploaded under a `base_key` if it does not already exist.
        """
        # abort if base_key already exists in bucket
        response = self._s3.list_objects_v2(Bucket=self._bucket, Prefix=base_key, MaxKeys=1)
        if "Contents" in response:
            return

        with resources_as_file(resources_files(src_ref)) as resources_path:
            for path in resources_path.glob("**/*.*"):
                relative_path = path.relative_to(resources_path)
                self._s3.upload_file(Filename=path, Bucket=self._bucket, Key=f"{base_key}/{relative_path}")

    def empty_bucket(self) -> None:
        """Delete all keys from the S3 bucket."""
        for page in self._s3.get_paginator("list_objects_v2").paginate(Bucket=self._bucket):
            keys = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not keys:
                continue
            # noinspection PyTypeChecker
            self._s3.delete_objects(Bucket=self._bucket, Delete={"Objects": keys})


class Exporter(ABC):
    """
    Abstract base class for exporters.

    Exporters typically:
    - produce some form of content or output, typically for specific resources via a `dumps` method
    - persist this output as files, stored on a local file system and/or remote object store (AWS S3)

    Some providers act at a site level, such as SiteExporter (which coordinates other exporters).

    This base exporter class is intended to be generic with subclasses being more opinionated.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        """
        Initialise exporter.

        Where `export_base` is an output directory for each export type which MUST be relative to
        `Config.EXPORT_PATH`, so that a base S3 key can be generated from it.
        """
        self._config = config
        self._logger = logger
        self._s3_client = s3
        self._s3_utils = S3Utils(
            logger=logger,
            s3=self._s3_client,
            s3_bucket=self._config.AWS_S3_BUCKET,
            relative_base=self._config.EXPORT_PATH,
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


class ResourceExporter(Exporter, ABC):
    """
    Base exporter for resource records or items.

    Base class for exporters related to Record and Item variants created for resources.
    """

    def __init__(
        self,
        config: Config,
        logger: logging.Logger,
        s3: S3Client,
        record: RecordRevision,
        export_base: Path,
        export_name: str,
    ) -> None:
        super().__init__(config=config, logger=logger, s3=s3)
        self._export_path = export_base.joinpath(export_name)
        self._validate(export_base)
        self._record = record

    def _validate(self, export_base: Path) -> None:
        """Validate exporter configuration."""
        try:
            _ = export_base.relative_to(self._config.EXPORT_PATH)
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


def get_record_aliases(record: Record) -> list[Identifier]:
    """Get optional aliases for record as relative file paths / S3 keys."""
    return record.identification.identifiers.filter(namespace=ALIAS_NAMESPACE)
