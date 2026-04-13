import logging
import threading
import time
from collections.abc import Collection

from boto3 import client as S3Client  # noqa: N812
from joblib import Parallel, delayed
from mypy_boto3_s3 import S3Client as S3ClientT

from lantern.exporters.base import ExporterBase
from lantern.models.site import SiteContent


class S3Exporter(ExporterBase):
    """
    (AWS) S3 exporter.

    For use with S3 compatible object stores.
    """

    def __init__(self, logger: logging.Logger, s3: S3ClientT, bucket: str, parallel_jobs: int) -> None:
        super().__init__(logger=logger, name="S3")
        self._s3 = s3
        self._bucket = bucket

        self._thread_local = threading.local()
        self._workers = parallel_jobs

    def _get_client(self) -> S3ClientT:
        """Create per-thread S3 client."""
        if not hasattr(self._thread_local, "s3"):
            # Hack to copy access key from existing client
            _key = self._s3._request_signer._credentials.get_frozen_credentials()  # ty:ignore[unresolved-attribute]

            self._thread_local.s3 = S3Client(
                "s3",
                aws_access_key_id=_key.access_key,
                aws_secret_access_key=_key.secret_key,
                region_name=self._s3.meta.region_name,
            )

        return self._thread_local.s3

    def _upload_object(
        self,
        s3: S3ClientT,
        key: str,
        content_type: str,
        body: str | bytes,
        redirect: str | None = None,
        meta: dict | None = None,
    ) -> None:
        """
        Upload file.

        Overwrites any existing file.

        Supports optional object redirect [1].

        Requires S3 client as a parameter for use in parallel jobs.

        [1] https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata
        """
        params = {"Bucket": self._bucket, "Key": key, "Body": body, "ContentType": content_type}
        if isinstance(body, str):
            params["Body"] = body.encode("utf-8")
        if redirect is not None:
            params["WebsiteRedirectLocation"] = redirect
        if meta:
            params["Metadata"] = meta
        self._logger.info(f"Putting {key} as {content_type}")
        s3.put_object(**params)

    def _upload_item(self, item: SiteContent) -> None:
        self._upload_object(
            s3=self._get_client(),  # per-thread client
            key=str(item.path),
            content_type=item.media_type,
            body=item.content,
            redirect=item.redirect,
            meta=item.object_meta,
        )

    def _empty_bucket(self) -> None:
        """Delete all keys from S3 bucket."""
        for page in self._s3.get_paginator("list_objects_v2").paginate(Bucket=self._bucket):
            keys = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not keys:
                continue
            self._s3.delete_objects(Bucket=self._bucket, Delete={"Objects": keys})

    def export(self, content: Collection[SiteContent]) -> None:
        """
        Persist content.

        Uploads are processed in parallel using a threaded pool to avoid issues with picking the S3 client.
        """
        start = time.monotonic()
        Parallel(n_jobs=self._workers, backend="threading")(delayed(self._upload_item)(c) for c in content)
        self._logger.info(
            f"Exported {len(content)} items to 's3://{self._bucket}' in {round(time.monotonic() - start)} seconds"
        )
