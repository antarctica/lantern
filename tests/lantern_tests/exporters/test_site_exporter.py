import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar
from unittest.mock import PropertyMock

import pytest
from bs4 import BeautifulSoup
from pytest_mock import MockerFixture

from lantern.exporters.site import SiteExporter, SiteIndexExporter, SitePagesExporter, SiteResourcesExporter
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordsProtocol
from tests.conftest import _init_fake_store


class TestSiteIndexExporter:
    """Test site index exporter."""

    def test_init(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_select_records: SelectRecordsProtocol,
    ):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = SiteIndexExporter(meta=meta, s3=s3_client, logger=fx_logger, select_records=fx_select_records)

        assert isinstance(exporter, SiteIndexExporter)
        assert exporter.name == "Site Index"

    def test_dumps(self, fx_exporter_site_index_sel: SiteIndexExporter):
        """Can dump site index."""
        html = BeautifulSoup(fx_exporter_site_index_sel._dumps(), parser="html.parser", features="lxml")
        assert html.select_one("h1:-soup-contains('Catalogue index')")

    def test_export(self, fx_exporter_site_index_sel: SiteIndexExporter):
        """Can export site index to a local file."""
        site_path = fx_exporter_site_index_sel._meta.export_path
        expected = site_path.joinpath("-", "index", "index.html")

        fx_exporter_site_index_sel.export()

        result = list(fx_exporter_site_index_sel._meta.export_path.glob("**/*.*"))
        assert expected in result

    def test_publish(self, fx_exporter_site_index_sel: SiteIndexExporter, fx_s3_bucket_name: str):
        """Can publish site index to S3."""
        site_path = fx_exporter_site_index_sel._meta.export_path

        fx_exporter_site_index_sel.publish()

        output = fx_exporter_site_index_sel._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=fx_exporter_site_index_sel._s3_utils.calc_key(site_path.joinpath("-", "index", "index.html")),
        )
        assert output["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestSitePageExporter:
    """Test site pages exporter."""

    relative_paths: ClassVar[list[str]] = [
        "404.html",
        "legal/accessibility/index.html",
        "legal/cookies/index.html",
        "legal/copyright/index.html",
        "legal/privacy/index.html",
        "-/formatting/index.html",
    ]

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = SitePagesExporter(meta=meta, s3=s3_client, logger=fx_logger)

        assert isinstance(exporter, SitePagesExporter)
        assert exporter.name == "Site Pages"

    def test_dumps(self, fx_exporter_site_pages: SitePagesExporter):
        """Can dump a site page with expected title and site title."""
        expected = "Privacy Policy | BAS Data Catalogue"
        result = fx_exporter_site_pages._dumps("_views/legal/privacy.html.j2")
        html = BeautifulSoup(result, parser="html.parser", features="lxml")

        assert html.head.title.string == expected
        assert "This website has links to other websites for which we are not responsible." in result

    def test_export_page(self, fx_exporter_site_pages: SitePagesExporter):
        """Can export a site page to a local file."""
        site_path = fx_exporter_site_pages._meta.export_path
        expected = site_path.joinpath("legal/privacy/index.html")

        fx_exporter_site_pages._export_page("_views/legal/privacy.html.j2")

        assert expected.exists()

    def test_publish_page(self, fx_exporter_site_pages: SitePagesExporter, fx_s3_bucket_name: str):
        """Can publish a site page to S3."""
        expected = "legal/privacy/index.html"

        fx_exporter_site_pages._publish_page("_views/legal/privacy.html.j2")

        result = fx_exporter_site_pages._s3_utils._s3.get_object(Bucket=fx_s3_bucket_name, Key=expected)
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_export(self, fx_exporter_site_pages: SitePagesExporter):
        """Can export site pages to local files."""
        site_path = fx_exporter_site_pages._meta.export_path
        expected = [site_path.joinpath(path) for path in self.relative_paths]

        fx_exporter_site_pages.export()

        result = list(fx_exporter_site_pages._meta.export_path.glob("**/*.*"))
        for path in expected:
            assert path in result

    def test_publish(self, fx_exporter_site_pages: SitePagesExporter, fx_s3_bucket_name: str):
        """Can publish site pages to S3."""
        expected = self.relative_paths

        fx_exporter_site_pages.publish()

        result = fx_exporter_site_pages._s3_utils._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys


class TestSiteResourcesExporter:
    """Test site exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = SiteResourcesExporter(meta=meta, logger=fx_logger, s3=s3_client)

        assert isinstance(exporter, SiteResourcesExporter)
        assert exporter.name == "Site Resources"

    def test_dump_css(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy CSS to output path."""
        expected = fx_exporter_site_resources._export_base.joinpath("css/main.css")

        fx_exporter_site_resources._dump_css()
        assert expected.exists()

    def test_dump_fonts(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy fonts to output path."""
        expected = fx_exporter_site_resources._export_base.joinpath("fonts/open-sans.ttf")

        fx_exporter_site_resources._dump_fonts()
        assert expected.exists()

    def test_dump_favicon_ico(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy favicon.ico to output path."""
        expected = fx_exporter_site_resources._export_base.parent.joinpath("favicon.ico")

        fx_exporter_site_resources._dump_favicon_ico()
        assert expected.exists()

    def test_dump_img(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy images to output path."""
        expected = fx_exporter_site_resources._export_base.joinpath("img/favicon.ico")

        fx_exporter_site_resources._dump_img()
        assert expected.exists()

    def test_dump_txt(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy text files to output path."""
        expected = [
            fx_exporter_site_resources._export_base.joinpath("txt/heartbeat.txt"),
            fx_exporter_site_resources._export_base.joinpath("txt/manifest.webmanifest"),
        ]

        fx_exporter_site_resources._dump_txt()
        for path in expected:
            assert path.exists()

    def test_dump_js(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy JavaScript files to output path."""
        expected = [
            fx_exporter_site_resources._export_base.joinpath("js/sentry-preload.js"),
            fx_exporter_site_resources._export_base.joinpath("js/enhancements.js"),
        ]

        fx_exporter_site_resources._dump_js()
        for path in expected:
            assert path.exists()

    def test_publish_css(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload CSS to S3."""
        expected = "static/css/main.css"

        fx_exporter_site_resources._publish_css()
        result = fx_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_fonts(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload fonts to S3."""
        expected = "static/fonts/open-sans.ttf"

        fx_exporter_site_resources._publish_fonts()
        result = fx_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_favicon_ico(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload favicon.ico to S3."""
        expected = "favicon.ico"

        fx_exporter_site_resources._publish_favicon_ico()
        result = fx_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_img(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload images to S3."""
        expected = "static/img/favicon.ico"

        fx_exporter_site_resources._publish_img()
        result = fx_exporter_site_resources._s3_utils._s3.get_object(
            Bucket=fx_exporter_site_resources._s3_utils._bucket, Key=expected
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_txt(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload text files to S3."""
        expected = ["static/txt/heartbeat.txt", "static/txt/manifest.webmanifest"]

        fx_exporter_site_resources._publish_txt()
        for key in expected:
            result = fx_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_exporter_site_resources._s3_utils._bucket, Key=key
            )
            assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_publish_js(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload JavaScript files to S3."""
        expected = ["static/js/sentry-preload.js", "static/js/enhancements.js"]

        fx_exporter_site_resources._publish_js()
        for key in expected:
            result = fx_exporter_site_resources._s3_utils._s3.get_object(
                Bucket=fx_exporter_site_resources._s3_utils._bucket, Key=key
            )
            assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_export(self, fx_exporter_site_resources: SiteResourcesExporter):
        """Can copy resources to output path."""
        fx_exporter_site_resources.export()
        assert fx_exporter_site_resources._export_base.joinpath("css/main.css").exists()
        assert fx_exporter_site_resources._export_base.joinpath("fonts/open-sans.ttf").exists()
        assert fx_exporter_site_resources._export_base.joinpath("img/favicon.ico").exists()
        assert fx_exporter_site_resources._export_base.joinpath("txt/heartbeat.txt").exists()
        assert fx_exporter_site_resources._export_base.joinpath("js/enhancements.js").exists()

    def test_publish(self, fx_s3_bucket_name: str, fx_exporter_site_resources: SiteResourcesExporter):
        """Can upload resources to S3."""
        expected = [
            "static/css/main.css",
            "static/fonts/open-sans.ttf",
            "static/img/favicon.ico",
            "static/txt/heartbeat.txt",
            "static/js/enhancements.js",
        ]

        fx_exporter_site_resources.publish()

        result = fx_exporter_site_resources._s3_utils._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys


class TestSiteExporter:
    """Test site index exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = SiteExporter(
            config=mock_config,
            meta=meta,
            s3=s3_client,
            logger=fx_logger,
            init_store=_init_fake_store,
            selected_identifiers=set(),
        )

        assert isinstance(exporter, SiteExporter)
        assert exporter.name == "Site"

    def test_purge(
        self,
        mocker: MockerFixture,
        fx_exporter_site: SiteExporter,
        fx_s3_bucket_name: str,
    ):
        """Can empty export directory and publishing bucket."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
            mock_config = mocker.Mock()
            type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
            meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")
            fx_exporter_site._meta = meta

            fx_exporter_site._meta.export_path.joinpath("x").touch()
            fx_exporter_site._s3_utils.upload_content(key="x", content_type="text/plain", body="x")

            fx_exporter_site.purge()

            assert fx_exporter_site._meta.export_path.joinpath("x").exists() is False
            result = fx_exporter_site._s3_client.list_objects(Bucket=fx_s3_bucket_name)
            assert "contents" not in result

    @pytest.mark.cov()
    def test_purge_empty(
        self,
        mocker: MockerFixture,
        fx_exporter_site: SiteExporter,
        fx_revision_model_min: RecordRevision,
        fx_s3_bucket_name: str,
    ):
        """Can empty export directory and publishing bucket when neither exist."""
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=Path("/non/existent/path"))
        fx_exporter_site._config = mock_config

        fx_exporter_site.purge()

        assert list(fx_exporter_site._meta.export_path.glob("**/*.*")) == []
        result = fx_exporter_site._s3_client.list_objects(Bucket=fx_s3_bucket_name)
        assert "contents" not in result

    def test_export(self, fx_exporter_site: SiteExporter):
        """Can export all site components to local files."""
        record = fx_exporter_site._store.select()[0]
        site_path = fx_exporter_site._meta.export_path
        expected = [
            site_path.joinpath("favicon.ico"),
            site_path.joinpath("404.html"),
            site_path.joinpath("static", "css", "main.css"),
            site_path.joinpath("items", record.file_identifier, "index.html"),
            site_path.joinpath("records", f"{record.file_identifier}.xml"),
            site_path.joinpath("legal", "privacy", "index.html"),
            site_path.joinpath("-", "index", "index.html"),
            site_path.joinpath("waf", "iso-19139-all", "index.html"),
            site_path.joinpath("-", "public-website-search", "items.json"),
        ]  # representative sample

        fx_exporter_site.export()

        result = list(fx_exporter_site._meta.export_path.glob("**/*.*"))
        for path in expected:
            assert path in result

    def test_html_titles(self, fx_exporter_site: SiteExporter, fx_revision_model_min: RecordRevision):
        """
        Check all pages have a unique and non-default HTML title value.

        As a guard against `lantern.models.site.SiteMeta.from_config_store` setting title to an empty string.
        """
        fx_exporter_site.export()

        result = list(fx_exporter_site._meta.export_path.glob("**/*.html"))
        for path in result:
            with path.open() as f:
                html = BeautifulSoup(f.read(), parser="html.parser", features="lxml")
            if html.head is None:
                continue
            assert html.head.title.string != " | BAS Data Catalogue"

    def test_publish(self, fx_s3_bucket_name: str, fx_exporter_site: SiteExporter):
        """
        Can publish site index to S3 or external services.

        Skips public website search publishing.
        """
        s3 = fx_exporter_site._index_exporter._s3_utils._s3
        record = fx_exporter_site._store.select()[0]
        expected = [
            "favicon.ico",
            "404.html",
            "static/css/main.css",
            f"items/{record.file_identifier}/index.html",
            f"records/{record.file_identifier}.html",
            "legal/privacy/index.html",
            "-/index/index.html",
            "waf/iso-19139-all/index.html",
            "-/public-website-search/items.json",
        ]  # representative sample

        fx_exporter_site.publish()

        result = s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = [o["Key"] for o in result["Contents"]]
        for key in expected:
            assert key in keys
