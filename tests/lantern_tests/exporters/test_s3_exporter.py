import logging

import pytest
from mypy_boto3_s3 import S3Client

from lantern.exporters.s3 import S3Exporter
from lantern.models.site import SiteContent


class TestS3Exporter:
    """Test S3 exporter."""

    def test_init(self, fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str):
        """Can create a local exporter."""
        s3 = S3Exporter(logger=fx_logger, s3=fx_s3_client, bucket=fx_s3_bucket_name)
        assert isinstance(s3, S3Exporter)
        assert s3.name == "S3"

    @pytest.mark.parametrize("value", ["x", b"x"])
    @pytest.mark.parametrize("meta", [False, True])
    @pytest.mark.parametrize("redirect", [False, True])
    def test_export(
        self, fx_s3_exporter: S3Exporter, fx_site_content: SiteContent, value: str | bytes, meta: bool, redirect: bool
    ):
        """Can export some content."""
        expected_meta = {"x": "x"} if meta else {}
        expected_redirect = "x"
        fx_site_content.content = value
        fx_site_content.object_meta = expected_meta
        if redirect:
            fx_site_content.redirect = expected_redirect

        fx_s3_exporter.export(content=[fx_site_content])
        result = fx_s3_exporter._s3.get_object(Bucket=fx_s3_exporter._bucket, Key=str(fx_site_content.path))
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        if redirect:
            assert result["WebsiteRedirectLocation"] == expected_redirect

    @pytest.mark.cov()
    @pytest.mark.parametrize("empty", [False, True])
    def test_empty(self, fx_s3_exporter: S3Exporter, empty: bool):
        """Can empty bucket contents some content."""
        if not empty:
            fx_s3_exporter._s3.put_object(Bucket=fx_s3_exporter._bucket, Key="x", Body="x", ContentType="text/plain")
            before = fx_s3_exporter._s3.list_objects(Bucket=fx_s3_exporter._bucket)
            assert len(before["Contents"]) == 1
        else:
            before = fx_s3_exporter._s3.list_objects(Bucket=fx_s3_exporter._bucket)
            assert "contents" not in before

        fx_s3_exporter._empty_bucket()
        after = fx_s3_exporter._s3.list_objects(Bucket=fx_s3_exporter._bucket)
        assert "contents" not in after
