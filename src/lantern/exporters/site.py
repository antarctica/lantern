import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from shutil import copy

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from mypy_boto3_s3 import S3Client

from lantern.config import Config
from lantern.exporters.base import Exporter, get_jinja_env, get_record_aliases, prettify_html
from lantern.exporters.base import Exporter as BaseExporter
from lantern.exporters.records import RecordsExporter
from lantern.exporters.website import WebsiteSearchExporter
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta


class SiteResourcesExporter(Exporter):
    """
    Static site resource exporters.

    A non-record specific exporter for static resources used across the static site (CSS, fonts, etc.).
    """

    def __init__(self, meta: ExportMeta, logger: logging.Logger, s3: S3Client) -> None:
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._css_src_ref = "lantern.resources.css"
        self._fonts_src_ref = "lantern.resources.fonts"
        self._img_src_ref = "lantern.resources.img"
        self._txt_src_ref = "lantern.resources.txt"
        self._export_base = self._meta.export_path / "static"

    def _dump_css(self) -> None:
        """
        Copy CSS to directory if not already present.

        The source CSS file needs generating from `main.css.j2` using the `tailwind` dev task.
        """
        with resources_as_file(resources_files(self._css_src_ref)) as src_base:
            src_path = src_base / "main.css"
            dst_path = self._export_base / "css" / src_path.name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            copy(src_path, dst_path)

    def _dump_fonts(self) -> None:
        """Copy fonts to directory if not already present."""
        BaseExporter._dump_package_resources(src_ref=self._fonts_src_ref, dest_path=self._export_base.joinpath("fonts"))

    def _dump_favicon_ico(self) -> None:
        """
        Copy favicon.ico to conventional path if not already present.

        Fallback for `favicon.ico` where clients don't respect `<link rel="shortcut icon">` in HTML.
        """
        with resources_as_file(resources_files(self._img_src_ref)) as src_base:
            name = "favicon.ico"
            src_path = src_base / name
            dst_path = self._export_base.parent / name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            copy(src_path, dst_path)

    def _dump_img(self) -> None:
        """Copy image files to directory if not already present."""
        BaseExporter._dump_package_resources(src_ref=self._img_src_ref, dest_path=self._export_base.joinpath("img"))

    def _dump_txt(self) -> None:
        """Copy text files to directory if not already present."""
        BaseExporter._dump_package_resources(src_ref=self._txt_src_ref, dest_path=self._export_base.joinpath("txt"))

    def _publish_css(self) -> None:
        """Upload CSS as an S3 object."""
        name = "main.css"
        with resources_as_file(resources_files(self._css_src_ref)) as src_base:
            src_path = src_base / name
            with src_path.open("r") as css_file:
                content = css_file.read()

        key = self._s3_utils.calc_key(self._export_base.joinpath("css", name))
        self._s3_utils.upload_content(key=key, content_type="text/css", body=content)

    def _publish_favicon_ico(self) -> None:
        """Upload favicon.ico as an S3 object."""
        name = "favicon.ico"
        with resources_as_file(resources_files(self._img_src_ref)) as src_base:
            src_path = src_base / name
            with src_path.open("rb") as favicon_file:
                content = favicon_file.read()

        key = self._s3_utils.calc_key(self._export_base.parent.joinpath(name))
        self._s3_utils.upload_content(key=key, content_type="image/x-icon", body=content)

    def _publish_fonts(self) -> None:
        """Upload fonts as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._fonts_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("fonts"))
        )

    def _publish_img(self) -> None:
        """Upload images as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._img_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("img"))
        )

    def _publish_txt(self) -> None:
        """Upload text files as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._txt_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("txt"))
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Resources"

    def export(self) -> None:
        """Copy site resources to their respective directories."""
        self._dump_css()
        self._dump_fonts()
        self._dump_favicon_ico()
        self._dump_img()
        self._dump_txt()

    def publish(self) -> None:
        """Copy site resources to S3 bucket."""
        self._publish_css()
        self._publish_fonts()
        self._publish_favicon_ico()
        self._publish_img()
        self._publish_txt()


class SiteIndexExporter(Exporter):
    """
    Proto Data Catalogue index exporter.

    Note: Intended for internal use only and intentionally unstyled.

    Generates a basic site index from a set of record summaries.
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        get_record: Callable[[str], RecordRevision],
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._jinja = get_jinja_env()
        self._template_path = "_views/-/index.html.j2"
        self._index_path = self._meta.export_path / "-" / "index" / "index.html"
        self._get_record = get_record
        self._selected_identifiers: set[str] = set()

    @property
    def selected_identifiers(self) -> set[str]:
        """Selected file identifiers."""
        return self._selected_identifiers

    @selected_identifiers.setter
    def selected_identifiers(self, identifiers: set[str]) -> None:
        """Selected file identifiers."""
        self._selected_identifiers = identifiers

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Index"

    @property
    def _data(self) -> dict:
        """Assemble index data."""
        records = []
        aliases = []

        for file_identifier in self._selected_identifiers:
            record = self._get_record(file_identifier)
            records.append(
                {
                    "type": record.hierarchy_level.name,
                    "file_identifier": record.file_identifier,
                    "title": record.identification.title,
                    "edition": record.identification.edition,
                }
            )
            identifiers = get_record_aliases(record)
            aliases.extend(
                [
                    {
                        "alias": (identifier.href or "").replace("https://data.bas.ac.uk/", ""),
                        "href": f"/items/{record.file_identifier}",
                        "file_identifier": record.file_identifier,
                        "title": record.identification.title,
                    }
                    for identifier in identifiers
                ]
            )

        return {
            "records": records,
            "aliases": aliases,
        }

    def _dumps(self) -> str:
        """Generate index."""
        self._meta.html_title = "Index"
        raw = self._jinja.get_template(self._template_path).render(meta=self._meta.site_metadata, data=self._data)
        return prettify_html(raw)

    def export(self) -> None:
        """Export proto index to directory."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        with self._index_path.open("w") as f:
            f.write(self._dumps())

    def publish(self) -> None:
        """Publish proto index to S3."""
        index_key = self._s3_utils.calc_key(self._index_path)
        self._s3_utils.upload_content(key=index_key, content_type="text/html", body=self._dumps())


class SitePagesExporter(Exporter):
    """
    Static site pages exporter.

    Renders static site pages from Jinja2 templates for legal pages, 404, etc.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._jinja = get_jinja_env()
        self._templates = [
            "_views/404.html.j2",
            "_views/legal/accessibility.html.j2",
            "_views/legal/cookies.html.j2",
            "_views/legal/copyright.html.j2",
            "_views/legal/privacy.html.j2",
            "_views/-/formatting.html.j2",
        ]
        self._html_title = {
            "_views/404.html.j2": "Not Found",
            "_views/legal/accessibility.html.j2": "Accessibility Statement",
            "_views/legal/cookies.html.j2": "Cookies Policy",
            "_views/legal/copyright.html.j2": "Copyright Policy",
            "_views/legal/privacy.html.j2": "Privacy Policy",
            "_views/-/formatting.html.j2": "Supported Formatting Guide",
        }

    def _get_page_path(self, template_path: str) -> Path:
        """Get path within exported site for a page based on its template."""
        if template_path == "_views/404.html.j2":
            return self._meta.export_path / "404.html"
        return self._meta.export_path / template_path.replace("_views/", "").split(".")[0] / "index.html"

    def _dumps(self, template_path: str) -> str:
        """Build a page."""
        self._meta.html_title = self._html_title[template_path]
        raw = self._jinja.get_template(template_path).render(meta=self._meta)
        return prettify_html(raw)

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Pages"

    def _export_page(self, template_path: str) -> None:
        """Export a page to directory."""
        page_path = self._get_page_path(template_path)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        with page_path.open("w") as f:
            f.write(self._dumps(template_path))

    def _publish_page(self, template_path: str) -> None:
        """Publish a page to S3."""
        page_path = self._get_page_path(template_path)
        page_key = self._s3_utils.calc_key(page_path)
        self._s3_utils.upload_content(key=page_key, content_type="text/html", body=self._dumps(template_path))

    def export(self) -> None:
        """Export static pages to directory."""
        for template in self._templates:
            self._export_page(template_path=template)

    def publish(self) -> None:
        """Publish static pages to S3."""
        for template in self._templates:
            self._publish_page(template_path=template)


class SiteExporter(Exporter):
    """
    Data Catalogue static site exporter.

    Combines exporters for records and static resources to create a standalone static website.

    Config instance needed for RecordsExporter.
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        meta: ExportMeta,
        s3: S3Client,
        get_record: Callable[[str], RecordRevision],
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._resources_exporter = SiteResourcesExporter(logger=logger, meta=meta, s3=self._s3_client)
        self._pages_exporter = SitePagesExporter(logger=logger, meta=meta, s3=self._s3_client)
        self._index_exporter = SiteIndexExporter(logger=logger, meta=meta, s3=self._s3_client, get_record=get_record)
        self._records_exporter = RecordsExporter(
            logger=logger, config=config, meta=meta, s3=self._s3_client, get_record=get_record
        )
        self._website_exporter = WebsiteSearchExporter(
            logger=logger, meta=meta, s3=self._s3_client, get_record=get_record
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site"

    def purge(self) -> None:
        """Empty file system export directory and S3 publishing bucket."""
        if self._meta.export_path.exists():
            self._logger.info("Purging file system export directory")
            shutil.rmtree(self._meta.export_path)
        self._logger.info("Purging S3 publishing bucket")
        self._s3_utils.empty_bucket()

    def select(self, file_identifiers: set[str]) -> None:
        """
        Select a subset of records to export and/or publish.

        Only applies to exporters that relate to individual resources.
        """
        self._records_exporter.selected_identifiers = file_identifiers
        self._index_exporter.selected_identifiers = file_identifiers
        self._website_exporter.selected_identifiers = file_identifiers

    def export(self) -> None:
        """Export site contents to a directory."""
        self._resources_exporter.export()
        self._pages_exporter.export()
        self._records_exporter.export()
        self._index_exporter.export()
        self._website_exporter.export()

    def publish(self) -> None:
        """Publish site contents to S3."""
        self._resources_exporter.publish()
        self._pages_exporter.publish()
        self._records_exporter.publish()
        self._index_exporter.publish()
        self._website_exporter.publish()
