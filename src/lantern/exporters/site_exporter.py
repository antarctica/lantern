import logging
import shutil
from pathlib import Path
from shutil import copy

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from jinja2 import Environment, PackageLoader, select_autoescape
from mypy_boto3_s3 import S3Client

from assets_tracking_service.config import Config
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.base_exporter import Exporter as BaseExporter
from assets_tracking_service.lib.bas_data_catalogue.exporters.records_exporter import RecordsExporter
from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary
from assets_tracking_service.lib.bas_data_catalogue.models.templates import PageMetadata


class SiteResourcesExporter(Exporter):
    """
    Static site resource exporters.

    A non-record specific exporter for static resources used across the static site (CSS, fonts, etc.).

    Due to its global nature, does not subclass the BaseExporter to avoid hacking around its requirements.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        super().__init__(config=config, logger=logger, s3=s3)
        self._css_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.css"
        self._fonts_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.fonts"
        self._img_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.img"
        self._txt_src_ref = "assets_tracking_service.lib.bas_data_catalogue.resources.txt"
        self._export_base = config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.joinpath("static")

    def _dump_css(self) -> None:
        """
        Copy CSS to directory if not already present.

        The source CSS file needs generating from `main.css.j2` using the `scripts/recreate-css.py` script.
        Note: the source `main.css` contains an environment specific output path and MUST NOT be checked into git.
        """
        with resources_as_file(resources_files(self._css_src_ref)) as src_base:
            name = "main.css"
            src_path = src_base / name
            dst_path = self._export_base.joinpath("css", name)
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
            dst_path = self._export_base.parent.joinpath(name)
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

    Note: Intended for internal use only and unstyled.

    Generates a basic site index from a set of record summaries.

    Due to its global nature, does not subclass the BaseExporter to avoid hacking around its requirements.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(config=config, logger=logger, s3=s3)
        self._index_path = self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "-" / "index" / "index.html"
        self._summaries: list[RecordSummary] = []
        self._records: list[Record] = []
        self._record_ids = set()

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Index"

    def loads(self, summaries: list[RecordSummary], records: list[Record]) -> None:
        """Populate exporter."""
        self._summaries = summaries
        self._records = records
        self._record_ids = {record.file_identifier for record in records}

    @property
    def _aliases(self) -> list[dict]:
        """Get a list of aliases from records."""
        aliases = []
        for record in self._records:
            identifiers = record.identification.identifiers.filter(namespace="alias.data.bas.ac.uk")
            aliases.extend(
                [
                    {
                        "alias": identifier.href.replace("https://data.bas.ac.uk/", ""),
                        "href": f"/items/{record.file_identifier}",
                        "file_identifier": record.file_identifier,
                        "title": record.identification.title,
                    }
                    for identifier in identifiers
                ]
            )
        return aliases

    def _dumps_v1(self) -> str:
        """Version 1 implementation."""
        item_links = "\n".join(
            [
                f'<li><a href="/items/{summary.file_identifier}/index.html">[{summary.hierarchy_level.name}] {summary.file_identifier} - {summary.title} ({summary.edition})</a></li>'
                for summary in self._summaries
            ]
        )
        return f"<section><h2>V1</h2><ul>{item_links}</ul></section>"

    def _dumps_v2(self) -> str:
        """Version 2 implementation."""
        summary_rows = "\n".join(
            [
                f"""
                <tr>
                    <td>ItemSummary</td>
                    <td>{summary.hierarchy_level.name}</td>
                    <td>{summary.file_identifier}</td>
                    <td>{summary.title}</td>
                    <td>{summary.edition}</td>
                    <td>-</td>
                </tr>
                """
                for summary in self._summaries
                if summary.file_identifier not in self._record_ids
            ]
        )
        record_rows = "\n".join(
            [
                f"""
                        <tr>
                            <td>Item</td>
                            <td>{record.hierarchy_level.name}</td>
                            <td><a href="/items/{record.file_identifier}/index.html">{record.file_identifier}</a></td>
                            <td>{record.identification.title}</td>
                            <td>{record.identification.edition}</td>
                            <td>-</td>
                        </tr>
                        """
                for record in self._records
            ]
        )
        alias_rows = "\n".join(
            [
                f"""
                <tr>
                    <td>Alias</td>
                    <td>-</td>
                    <td><a href="{alias["href"]}">{alias["file_identifier"]}</a></td>
                    <td>{alias["title"]}</td>
                    <td>-</td>
                    <td><a href="/{alias["alias"]}">{alias["alias"]}</a></td>
                </tr>
                """
                for alias in self._aliases
            ]
        )
        return f"""
        <section>
            <h2>V2</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>Kind</th>
                        <th>Type</th>
                        <th>File Identifier</th>
                        <th>Title</th>
                        <th>Edition</th>
                        <th>Alias</th>
                    </tr>
                </thead>
                <tbody>
                    {summary_rows}
                    {record_rows}
                    {alias_rows}
                </tbody>
            </table>
        </section>
        """

    def _dumps(self) -> str:
        """Build proto/backstage index."""
        return f"""
        <html>
            <head>
                <meta charset="utf-8">
                <title>Proto Items Index</title>
            </head>
            <body>
                <h1>Proto Items Index</h1>
                {self._dumps_v2()}
                {self._dumps_v1()}
            </body>
        </html>
        """

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

    Due to its global nature, does not subclass the BaseExporter to avoid hacking around its requirements.
    """

    def __init__(self, config: Config, s3: S3Client, logger: logging.Logger) -> None:
        """Initialise exporter."""
        super().__init__(config=config, logger=logger, s3=s3)
        _loader = PackageLoader("assets_tracking_service.lib.bas_data_catalogue", "resources/templates")
        self._jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        self._templates = ["404.html.j2", "legal/cookies.html.j2", "legal/copyright.html.j2", "legal/privacy.html.j2"]

    def _get_page_metadata(self, template_path: str) -> PageMetadata:
        """Get metadata for a page based on its template."""
        mapping = {
            "404.html.j2": "Not Found",
            "legal/cookies.html.j2": "Cookies Policy",
            "legal/copyright.html.j2": "Copyright Policy",
            "legal/privacy.html.j2": "Privacy Policy",
        }
        return PageMetadata(
            sentry_src=self._config.EXPORTER_DATA_CATALOGUE_SENTRY_SRC,
            plausible_domain=self._config.EXPORTER_DATA_CATALOGUE_PLAUSIBLE_DOMAIN,
            html_title=mapping[template_path],
        )

    def _get_page_path(self, template_path: str) -> Path:
        """Get path within exported site for a page based on its template."""
        if template_path == "404.html.j2":
            return self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / "404.html"
        return self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH / template_path.split(".")[0] / "index.html"

    def _dumps(self, template_path: str) -> str:
        """Build a page."""
        return self._jinja.get_template(template_path).render(meta=self._get_page_metadata(template_path))

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Pages"

    def export_page(self, template_path: str) -> None:
        """Export a page to directory."""
        page_path = self._get_page_path(template_path)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        with page_path.open("w") as f:
            f.write(self._dumps(template_path))

    def publish_page(self, template_path: str) -> None:
        """Publish a page to S3."""
        page_path = self._get_page_path(template_path)
        page_key = self._s3_utils.calc_key(page_path)
        self._s3_utils.upload_content(key=page_key, content_type="text/html", body=self._dumps(template_path))

    def export(self) -> None:
        """Export static pages to directory."""
        for template in self._templates:
            self.export_page(template_path=template)

    def publish(self) -> None:
        """Publish static pages to S3."""
        for template in self._templates:
            self.publish_page(template_path=template)


class SiteExporter(Exporter):
    """
    Data Catalogue static site exporter.

    Combines exporters for records and static resources to create a standalone static website.
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(config=config, logger=logger, s3=s3)
        self._resources_exporter = SiteResourcesExporter(config=self._config, logger=logger, s3=self._s3_client)
        self._pages_exporter = SitePagesExporter(config=self._config, logger=logger, s3=self._s3_client)
        self._index_exporter = SiteIndexExporter(config=self._config, logger=logger, s3=self._s3_client)
        self._records_exporter = RecordsExporter(config=self._config, logger=logger, s3=self._s3_client)

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site"

    def purge(self) -> None:
        """Empty file system export directory and S3 publishing bucket."""
        if self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH.exists():
            self._logger.info("Purging file system export directory")
            shutil.rmtree(self._config.EXPORTER_DATA_CATALOGUE_OUTPUT_PATH)
        self._logger.info("Purging S3 publishing bucket")
        self._s3_utils.empty_bucket()

    def loads(self, summaries: list[RecordSummary], records: list[Record]) -> None:
        """Populate exporter."""
        self._records_exporter.loads(summaries=summaries, records=records)
        self._index_exporter.loads(summaries=summaries, records=records)

    def export(self) -> None:
        """Export site contents to a directory."""
        self._resources_exporter.export()
        self._pages_exporter.export()
        self._records_exporter.export()
        self._index_exporter.export()

    def publish(self) -> None:
        """Publish site contents to S3."""
        self._resources_exporter.publish()
        self._pages_exporter.publish()
        self._records_exporter.publish()
        self._index_exporter.publish()
