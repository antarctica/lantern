import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from boto3 import client as S3Client  # noqa: N812
from jinja2 import Environment
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import (
    RsyncUtils,
    S3Utils,
    dumps_redirect,
    get_jinja_env,
    get_record_aliases,
    init_gitlab_store,
    init_s3_client,
    prettify_html,
)


class TestS3Utils:
    """Test S3 utility methods."""

    def test_init(self, fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str):
        """Can create instance."""
        with TemporaryDirectory() as tmp_path:
            path = Path(tmp_path)

        s3_utils = S3Utils(s3=fx_s3_client, logger=fx_logger, s3_bucket=fx_s3_bucket_name, relative_base=path)
        assert isinstance(s3_utils, S3Utils)

    def test_calc_s3_key(self, fx_s3_utils: S3Utils):
        """Can get S3 key from path relative to site base."""
        expected = "x/y/z.txt"
        path = fx_s3_utils._relative_base.joinpath(expected)

        actual = fx_s3_utils.calc_key(path=path)
        assert actual == expected

    def test_upload_content(self, caplog: pytest.LogCaptureFixture, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can write output to an object at a low level."""
        expected = "x"

        fx_s3_utils.upload_content(key=expected, content_type="text/plain", body="x", meta={expected: "..."})

        result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["Metadata"][expected] == "..."
        assert f"s3://{fx_s3_bucket_name}/{expected}" in caplog.text

    def test_upload_content_redirect(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can write output to an object with an object redirect."""
        key = "x"
        expected = "y"

        fx_s3_utils.upload_content(key=key, content_type="text/plain", body="x", redirect="y")

        result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert result["WebsiteRedirectLocation"] == expected

    @pytest.mark.parametrize(
        ("ext", "expected"), [(None, None), (".png", "image/png"), (".ico", "image/x-icon"), (".svg", "image/svg+xml")]
    )
    def test_get_img_media_type(self, fx_s3_utils: S3Utils, ext: str | None, expected: str | None):
        """Can get media type for select image extensions."""
        if ext is None:
            path = Path("x.x")
            expected = f"Unsupported image file extension: {path.suffix}"
            with pytest.raises(ValueError, match=expected):
                fx_s3_utils._get_img_media_type(path=path)
            return

        path = Path("x")
        path = path.with_suffix(ext)

        result = fx_s3_utils._get_img_media_type(path=path)
        assert result == expected

    def test_upload_directory(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can upload directory of resources to S3 bucket."""
        with TemporaryDirectory() as tmp_path:
            output_base = Path(tmp_path) / "output"
        output_img = output_base / "bar" / "x.png"
        output_not_image = output_base / "bar" / "x.txt"
        output_img.parent.mkdir(parents=True, exist_ok=True)
        output_img.touch()
        output_not_image.touch()

        expected = ["foo/bar/x.png", "foo/bar/x.txt"]
        fx_s3_utils.upload_directory(
            src_path=output_base,
            base_key="foo",
            content_type="text/plain",
        )

        for expected_key in expected:
            result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected_key)
            assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_upload_directory_missing(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can't upload directory that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            fx_s3_utils.upload_directory(
                src_path=Path("/invalid"),
                base_key="",
                content_type="text/plain",
            )

    def test_upload_package_resources(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can upload package resources to S3 bucket."""
        expected = "static/xsl/iso-html/xml-to-html-ISO.xsl"
        fx_s3_utils.upload_package_resources(
            src_ref="lantern.resources.xsl.iso-html",
            base_key="static/xsl/iso-html",
            content_type="application/xml",
        )

        result = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_upload_package_resources_exists(self, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can keep existing objects if already copied to S3 bucket from package resources."""
        src_ref = "lantern.resources.xsl.iso-html"
        base_key = "static/xsl/iso-html"
        key = "static/xsl/iso-html/xml-to-html-ISO.xsl"

        fx_s3_utils.upload_package_resources(src_ref=src_ref, base_key=base_key, content_type="application/xml")
        initial = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)

        fx_s3_utils.upload_package_resources(src_ref=src_ref, base_key=base_key, content_type="application/xml")
        repeat = fx_s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=key)
        assert initial["LastModified"] == repeat["LastModified"]

    def test_empty_bucket(self, caplog: pytest.LogCaptureFixture, fx_s3_bucket_name: str, fx_s3_utils: S3Utils):
        """Can empty all objects in bucket."""
        fx_s3_utils.upload_content(key="x", content_type="text/plain", body="x")
        result = fx_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert len(result["Contents"]) == 1

        fx_s3_utils.empty_bucket()
        result = fx_s3_utils._s3.list_objects_v2(Bucket=fx_s3_bucket_name)
        assert "contents" not in result


class TestRsyncUtils:
    """Test Rsync utility methods."""

    def test_init(self, fx_logger: logging.Logger):
        """Can create instance."""
        rsync_utils = RsyncUtils(logger=fx_logger)
        assert isinstance(rsync_utils, RsyncUtils)

    @pytest.mark.cov()
    @pytest.mark.parametrize("exists", [True, False])
    def test_target_path_handling(self, mocker: MockerFixture, fx_logger: logging.Logger, exists: bool):
        """Can create target path if missing and local."""
        with TemporaryDirectory() as tmp_path:
            target_path = Path(tmp_path) / "t"
        if exists:
            target_path.mkdir(parents=True, exist_ok=True)
        mock = mocker.MagicMock()
        # noinspection SpellCheckingInspection
        mock.returncode = 0
        mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)
        rsync_utils = RsyncUtils(logger=fx_logger)

        rsync_utils.put(src_path=Path("x"), target_path=target_path, target_host=None)
        assert target_path.exists()

    @pytest.mark.parametrize("host", [None, "h"])
    def test_put(self, mocker: MockerFixture, fx_logger: logging.Logger, host: str | None):
        """Can generate expected rsync command."""
        with TemporaryDirectory() as tmp_path:
            target_path = Path(tmp_path) / "y"
        mock = mocker.MagicMock()
        # noinspection SpellCheckingInspection
        mock.returncode = 0
        mock_subproc = mocker.patch("sysrsync.runner.subprocess.run", return_value=mock)

        source = Path("/x")
        target = target_path
        expected_target = f"{host}:{target}" if host else str(target)
        expected = f"rsync -a {source.resolve()}/ {expected_target}"
        rsync_utils = RsyncUtils(logger=fx_logger)

        rsync_utils.put(src_path=source, target_path=target, target_host=host)
        mock_subproc.assert_called_once_with(expected.split(" "), cwd=str(Path.cwd()), shell=False)


@pytest.mark.cov()
class TestUtils:
    """Test app utils not tested elsewhere."""

    @pytest.mark.parametrize("cached", [True, False])
    @pytest.mark.parametrize("frozen", [True, False])
    def test_gitlab_store(self, fx_logger: logging.Logger, fx_config: Config, cached: bool, frozen: bool) -> None:
        """
        Can init GitLab store.

        Only called in dev-tasks so not considered as run in coverage.
        """
        if not cached and frozen:
            with pytest.raises(ValueError, match=r"Cannot create a frozen GitLab store without caching."):
                init_gitlab_store(logger=fx_logger, config=fx_config, cached=cached, frozen=frozen)
            return

        store = init_gitlab_store(logger=fx_logger, config=fx_config, cached=cached, frozen=frozen)
        assert isinstance(store, GitLabStore)
        assert isinstance(store, GitLabCachedStore) == cached
        if isinstance(store, GitLabCachedStore):
            assert store.frozen == frozen

    def test_s3_client(self, fx_logger: logging.Logger, fx_config: Config):
        """
        Can init S3 client.

        Initially a coverage only check.
        """
        client = init_s3_client(config=fx_config)
        assert client is not None

    def test_get_record_aliases(self, fx_revision_model_min: RecordRevision):
        """Can get any aliases in a record."""
        alias = Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)

        fx_revision_model_min.identification.identifiers.append(alias)
        result = get_record_aliases(fx_revision_model_min)
        assert len(result) == 1
        assert result[0] == alias

    def test_get_jinja_env(self):
        """Can get app Jinja environment."""
        result = get_jinja_env()
        assert isinstance(result, Environment)
        assert "_macros/common.html.j2" in result.loader.list_templates()

    def test_prettify_html(self):
        """Can format HTML."""
        assert (
            prettify_html(html="<html>\n\n\n\n\n<body><p>...</p></body></html>")
            == "<html>\n<body><p>...</p></body></html>"
        )

    def test_dumps_redirect(self):
        """Can generate HTML redirection page."""
        expected = "/x"
        result = dumps_redirect(expected)
        assert "<!DOCTYPE html>" in result
        assert f'refresh" content="0;url={expected}"' in result
