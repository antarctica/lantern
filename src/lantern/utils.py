import logging

# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from pathlib import Path

import sysrsync
from boto3 import client as S3Client  # noqa: N812
from bs4 import BeautifulSoup
from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from jinja2 import Environment, PackageLoader, select_autoescape
from mypy_boto3_s3 import S3Client as S3ClientT

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE
from lantern.models.record.record import Record
from lantern.stores.gitlab import GitLabSource, GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore


class S3Utils:
    """Wrapper around Boto S3 client with high-level and/or convenience methods."""

    def __init__(self, logger: logging.Logger, s3: S3ClientT, s3_bucket: str, relative_base: Path) -> None:
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

    def upload_object(
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

    @staticmethod
    def _get_img_media_type(path: Path) -> str:
        """Map select file extensions to media types."""
        if path.suffix == ".png":
            return "image/png"
        if path.suffix == ".ico":
            return "image/x-icon"
        if path.suffix == ".svg":
            return "image/svg+xml"
        msg = f"Unsupported image file extension: {path.suffix}"
        raise ValueError(msg) from None

    def upload_directory(self, src_path: Path, base_key: str, content_type: str) -> None:
        """Upload contents of a directory as S3 objects if they do not already exist."""
        if not src_path.is_dir():
            msg = "Source path must be a directory"
            raise FileNotFoundError(msg) from None

        for path in src_path.glob("**/*.*"):
            file_content_type = content_type
            relative_path = path.relative_to(src_path)
            if file_content_type == "image/*":
                file_content_type = self._get_img_media_type(path)
            self._s3.upload_file(
                Filename=str(path),
                Bucket=self._bucket,
                Key=f"{base_key}/{relative_path}",
                ExtraArgs={"ContentType": file_content_type},
            )

    def upload_package_resources(self, src_ref: str, base_key: str, content_type: str) -> None:
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
            self.upload_directory(src_path=resources_path, base_key=base_key, content_type=content_type)

    def empty_bucket(self) -> None:
        """Delete all keys from the S3 bucket."""
        for page in self._s3.get_paginator("list_objects_v2").paginate(Bucket=self._bucket):
            keys = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if not keys:
                continue
            # noinspection PyTypeChecker
            self._s3.delete_objects(Bucket=self._bucket, Delete={"Objects": keys})


class RsyncUtils:
    """Wrapper around https://github.com/gchamon/sysrsync client with high-level and/or convenience methods."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def put(self, src_path: Path, target_path: Path, target_host: str | None = None) -> None:
        """
        Copy contents of source path to target on local or remote server.

        The source and target path MUST be directories.

        E.g. for a source path './items' containing './items/123/index.html' and a target path of '/data/', this will
        create '/data/123/index.html'.

        Rsync options:
        - `-rlD`      : recurse, symlinks, devices/specials
        - `--no-perms`: don't chmod — new files/dirs inherit default ACLs automatically
        - `--no-times : don't set timestamps (as this requires ownership of the parent directory)

        Note: `-a` not used as it implies: `-p` (perms), `-o` (owner), `-g` (group), `-t` (times) — all of which can
        fail for non-owners.

        Explanation:
        > These options are necessary because rsync `-a/-p` for example tries to call chmod() on the target to match
        > source permissions. Even if the target directory has group-write, only the directory owner can chmod() it —
        > this is a Linux kernel restriction, not a permission bit issue. I.e. if the target was created by `alice`,
        > `bob` cannot change their permissions even with group-write access.
        """
        if not target_host and not target_path.exists():
            self._logger.info("Ensuring target local path exists.")
            target_path.mkdir(parents=True, exist_ok=True)

        target = f"{target_host}:{target_path}" if target_host else str(target_path)
        kwargs = {
            "source": str(src_path.resolve()),
            "sync_source_contents": True,
            "destination": str(target_path),
            "options": ["-rlD", "--no-perms", "--no-times"],  # to work around POSIX group-write limitations
        }
        if target_host:
            kwargs["destination_ssh"] = target_host

        self._logger.info(f"Syncing '{src_path.resolve()}' to '{target}'")
        sysrsync.run(strict=True, **kwargs)


def init_gitlab_store(
    logger: logging.Logger, config: Config, branch: str | None = None, cached: bool = False, frozen: bool = False
) -> GitLabStore | GitLabCachedStore:
    """
    Initialise a GitLab store from app Config.

    Store is not cached by default to allow switching between branches efficiently.
    Store is not frozen by default to allow fetching changes before processing.
    """
    if not cached and frozen:
        msg = "Cannot create a frozen GitLab store without caching."
        raise ValueError(msg) from None

    branch_ = branch or config.STORE_GITLAB_BRANCH
    source = GitLabSource(endpoint=config.STORE_GITLAB_ENDPOINT, project=config.STORE_GITLAB_PROJECT_ID, ref=branch_)

    if not cached:
        return GitLabStore(logger=logger, source=source, access_token=config.STORE_GITLAB_TOKEN)

    return GitLabCachedStore(
        logger=logger,
        source=source,
        access_token=config.STORE_GITLAB_TOKEN,
        parallel_jobs=config.PARALLEL_JOBS,
        cache_dir=config.STORE_GITLAB_CACHE_PATH,
        frozen=frozen,
    )


def init_s3_client(config: Config) -> S3ClientT:
    """Initialise an S3 client from app Config."""
    return S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )


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


def dumps_redirect(target: str) -> str:
    """Generate a minimal HTML redirect page."""
    """Generate redirect page for record."""
    html = ET.Element("html", attrib={"lang": "en-GB"})
    head = ET.SubElement(html, "head")
    title = ET.SubElement(head, "title")
    title.text = "BAS Data Catalogue"
    ET.SubElement(head, "meta", attrib={"http-equiv": "refresh", "content": f"0;url={target}"})
    body = ET.SubElement(html, "body")
    a = ET.SubElement(body, "a", attrib={"href": target})
    a.text = "Click here if you are not redirected after a few seconds."
    html_str = ET.tostring(html, encoding="unicode", method="html")
    return f"<!DOCTYPE html>\n{html_str}"
