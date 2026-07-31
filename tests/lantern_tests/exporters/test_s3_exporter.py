from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from lantern.exporters.s3 import S3Exporter

if TYPE_CHECKING:
    import logging

    from mypy_boto3_s3 import S3Client

    from lantern.models.site import SiteContent


class TestS3Exporter:
    """Test S3 exporter."""

    def test_init(self, fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str):
        """Can create a local exporter."""
        s3 = S3Exporter(logger=fx_logger, s3=fx_s3_client, bucket=fx_s3_bucket_name, parallel_jobs=1)
        assert isinstance(s3, S3Exporter)

    @pytest.mark.parametrize("value", ["x", b"x"])
    @pytest.mark.parametrize("meta", [False, True])
    @pytest.mark.parametrize("redirect", [False, True])
    @pytest.mark.parametrize("cache", [True, False])
    def test_export(
        self,
        fx_s3_exporter: S3Exporter,
        fx_site_content: SiteContent,
        value: str | bytes,
        meta: bool,
        redirect: bool,
        cache: bool,
    ):
        """Can export some content."""
        expected_meta = {"x": "x"} if meta else {}
        expected_redirect = "x"
        fx_site_content.content = value
        fx_site_content.object_meta = expected_meta
        if redirect:
            fx_site_content.redirect = expected_redirect
        if not cache:
            fx_site_content.prevent_caching = True

        fx_s3_exporter.export(content=[fx_site_content])
        result = fx_s3_exporter._s3.get_object(Bucket=fx_s3_exporter._bucket, Key=str(fx_site_content.path))
        assert result["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        if redirect:
            assert result["WebsiteRedirectLocation"] == expected_redirect
        if not cache:
            assert result["CacheControl"] == "no-store"
        else:
            assert "CacheControl" not in result
