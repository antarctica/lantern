import logging
from collections.abc import Iterable

from mypy_boto3_s3 import S3Client

from lantern.exporters.base import ExporterBase
from lantern.models.site import SiteContent


class S3Exporter(ExporterBase):
    """
    (AWS) S3 exporter.

    For use with S3 compatible object stores.
    """

    def __init__(self, logger: logging.Logger, s3: S3Client, bucket: str) -> None:
        """Initialise."""
        super().__init__(logger=logger)
        self._s3 = s3
        self._bucket = bucket

    @property
    def name(self) -> str:
        """Exporter name."""
        return "S3"

    def _upload_object(
        self, key: str, content_type: str, body: str | bytes, redirect: str | None = None, meta: dict | None = None
    ) -> None:
        """
        Upload file.

        Overwrites any existing file.

        Supports optional object redirect [1].

        [1] https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata
        """
        params = {"Bucket": self._bucket, "Key": key, "Body": body, "ContentType": content_type}
        if isinstance(body, str):
            params["Body"] = body.encode("utf-8")
        if redirect is not None:
            params["WebsiteRedirectLocation"] = redirect
        if meta:
            # noinspection PyTypeChecker
            params["Metadata"] = meta
        self._logger.info(f"Putting {key} as {content_type}")
        self._s3.put_object(**params)

    def _empty_bucket(self) -> None:
        """Delete all keys from S3 bucket."""
        for page in self._s3.get_paginator("list_objects_v2").paginate(Bucket=self._bucket):
            keys = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not keys:
                continue
            # noinspection PyTypeChecker
            self._s3.delete_objects(Bucket=self._bucket, Delete={"Objects": keys})

    def export(self, content: Iterable[SiteContent]) -> None:
        """Persist content."""
        _count = 0
        for item in content:
            self._upload_object(
                key=str(item.path),
                content_type=item.media_type,
                body=item.content,
                redirect=item.redirect,
                meta=item.object_meta,
            )
            _count += 1
        self._logger.info(f"Exported {_count} items to 'https://{self._bucket}'")
