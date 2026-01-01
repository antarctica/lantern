import logging
from abc import ABC, abstractmethod
from mimetypes import guess_type
from pathlib import Path
from shutil import copytree

from bs4 import BeautifulSoup
from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from jinja2 import Environment, PackageLoader, select_autoescape
from mypy_boto3_s3 import S3Client

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordsProtocol


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


def get_record_aliases(record: Record) -> list[Identifier]:
    """Get optional aliases for record as relative file paths / S3 keys."""
    return record.identification.identifiers.filter(namespace=ALIAS_NAMESPACE)


def get_jinja_env() -> Environment:
    """Get Jinja environment with app templates."""
    _loader = PackageLoader("lantern", "resources/templates")
    return Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)


def prettify_html(html: str) -> str:
    """
    Prettify HTML string, removing any empty lines.

    Without very careful whitespace control, Jinja templates quickly look messy where conditionals and other logic are
    used. Whilst this doesn't strictly matter, it is nicer if output looks well-formed by removing empty lines.

    This gives a 'flat' structure when viewed as source. Browser dev tools will reformat this into a tree structure.
    The `prettify()` method is not used as it splits all elements onto new lines, which causes layout/spacing bugs.
    """
    return str(BeautifulSoup(html, parser="html.parser", features="lxml"))
