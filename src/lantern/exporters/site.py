import json
import logging
import shutil
from pathlib import Path
from shutil import copy

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files
from mypy_boto3_s3 import S3Client

from lantern.config import Config
from lantern.exporters.base import Exporter, ResourcesExporter
from lantern.exporters.base import Exporter as BaseExporter
from lantern.exporters.records import RecordsExporter
from lantern.exporters.waf import WebAccessibleFolderExporter
from lantern.exporters.website import WebsiteSearchExporter
from lantern.models.site import ExportMeta, SitePageMeta
from lantern.stores.base import SelectRecordsProtocol, Store
from lantern.utils import dumps_redirect, get_jinja_env, get_record_aliases, prettify_html


class SiteResourcesExporter(Exporter):
    """
    Static site resource exporters.

    A non-record specific exporter for static resources used across the static site (CSS, JS, fonts, etc.).
    """

    def __init__(self, meta: ExportMeta, logger: logging.Logger, s3: S3Client) -> None:
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._css_src_ref = "lantern.resources.css"
        self._fonts_src_ref = "lantern.resources.fonts"
        self._img_src_ref = "lantern.resources.img"
        self._txt_src_ref = "lantern.resources.txt"
        self._js_src_ref = "lantern.resources.js"
        self._export_base = self._meta.export_path / "static"

    def _dump_css(self) -> None:
        """
        Copy CSS to directory if not already present.

        The source CSS file needs generating from `resources/templates/_assets/css/main.css.j2` using the `css` dev task.
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

    def _dump_js(self) -> None:
        """
        Copy JS files to directory if not already present.

        Some JS files need generating from `resources/templates/_assets/*.j2` first using the `js` dev task.
        """
        BaseExporter._dump_package_resources(src_ref=self._js_src_ref, dest_path=self._export_base.joinpath("js"))

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

    def _publish_js(self) -> None:
        """Upload JS files as S3 objects if they do not already exist."""
        self._s3_utils.upload_package_resources(
            src_ref=self._js_src_ref, base_key=self._s3_utils.calc_key(self._export_base.joinpath("js"))
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Resources"

    def export(self) -> None:
        """Copy site resources to their respective directories."""
        self._logger.info("Exporting site resources.")
        self._dump_css()
        self._dump_fonts()
        self._dump_favicon_ico()
        self._dump_img()
        self._dump_txt()
        self._dump_js()

    def publish(self) -> None:
        """Copy site resources to S3 bucket."""
        self._logger.info("Publishing site resources.")
        self._publish_css()
        self._publish_fonts()
        self._publish_favicon_ico()
        self._publish_img()
        self._publish_txt()
        self._publish_js()


class SiteIndexExporter(ResourcesExporter):
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
        select_records: SelectRecordsProtocol,
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3, select_records=select_records)
        self._jinja = get_jinja_env()
        self._template_path = "_views/-/index.html.j2"
        self._index_path = self._meta.export_path / "-" / "index" / "index.html"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Index"

    @property
    def _data(self) -> dict:
        """Assemble index data."""
        idx_records = []
        idx_aliases = []

        for record in self._select_records():
            idx_records.append(
                {
                    "type": record.hierarchy_level.name,
                    "file_identifier": record.file_identifier,
                    "title": record.identification.title,
                    "edition": record.identification.edition,
                }
            )
            identifiers = get_record_aliases(record)
            idx_aliases.extend(
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
            "records": idx_records,
            "aliases": idx_aliases,
        }

    def _dumps(self) -> str:
        """Generate index."""
        self._meta.html_title = "Index"
        raw = self._jinja.get_template(self._template_path).render(meta=self._meta.site_metadata, data=self._data)
        return prettify_html(raw)

    def export(self) -> None:
        """Export proto index to directory."""
        self._logger.info("Exporting site index.")
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        with self._index_path.open("w") as f:
            f.write(self._dumps())

    def publish(self) -> None:
        """Publish proto index to S3."""
        self._logger.info("Publishing site index.")
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
        self._templates: dict[str, SitePageMeta] = {
            "_views/404.html.j2": SitePageMeta(title="Not Found", url="-", meta=False),
            "_views/legal/accessibility.html.j2": SitePageMeta(
                title="Accessibility Statement",
                url=f"{self._meta.base_url}/legal/accessibility",
                description="Basic accessibility check for the BAS Data Catalogue",
            ),
            "_views/legal/cookies.html.j2": SitePageMeta(
                title="Cookies Policy",
                url=f"{self._meta.base_url}/legal/cookies",
                description="Cookies policy for the BAS Data Catalogue",
            ),
            "_views/legal/copyright.html.j2": SitePageMeta(
                title="Copyright Policy",
                url=f"{self._meta.base_url}/legal/copyright",
                description="Copyright policy for the BAS Data Catalogue",
            ),
            "_views/legal/privacy.html.j2": SitePageMeta(
                title="Privacy Policy",
                url=f"{self._meta.base_url}/legal/privacy",
                description="Privacy policy for the BAS Data Catalogue",
            ),
            "_views/guides/formatting.html.j2": SitePageMeta(
                title="Formatting Guide",
                url=f"{self._meta.base_url}/guides/formatting",
                description="Formatting guide for content items",
            ),
        }

    def _get_page_path(self, template_path: str) -> Path:
        """Get path within exported site for a page based on its template."""
        if template_path == "_views/404.html.j2":
            return self._meta.export_path / "404.html"
        return self._meta.export_path / template_path.replace("_views/", "").split(".")[0] / "index.html"

    def _dumps(self, template_path: str) -> str:
        """Build a page."""
        page_meta: SitePageMeta = self._templates[template_path]
        self._meta.html_title = page_meta.title
        self._meta.html_open_graph = page_meta.open_graph
        self._meta.html_schema_org = page_meta.schema_org
        raw = self._jinja.get_template(template_path).render(meta=self._meta)
        return prettify_html(raw)

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

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Pages"

    def export(self) -> None:
        """Export static pages to directory."""
        self._logger.info("Exporting site pages.")
        for template in self._templates:
            self._export_page(template_path=template)

    def publish(self) -> None:
        """Publish static pages to S3."""
        self._logger.info("Publishing site pages.")
        for template in self._templates:
            self._publish_page(template_path=template)


class SiteApiExporter(Exporter):
    """
    Site API resources exporter.

    Renders API Catalogue and OpenAPI schema, as JSON and interactive HTML documentation from Jinja2 templates.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._jinja = get_jinja_env()
        self._export_base = self._meta.export_path
        self._catalog_path = self._export_base / "static" / "json" / "api-catalog.json"
        self._catalog_well_known_path = self._export_base / ".well-known" / "api-catalog"
        self._schema_path = self._export_base / "static" / "json" / "openapi.json"
        self._docs_path = self._export_base / "guides" / "api" / "index.html"

    def _dumps_catalog(self) -> dict:
        """Build RFC 9727 API Catalog as a JSON document."""
        return {
            "linkset": [
                {
                    "anchor": f"{self._meta.base_url}/",
                    "service-desc": [
                        {
                            "href": f"{self._meta.base_url}/static/json/openapi.json",
                            "type": "application/vnd.oai.openapi+json;version=3.1",
                        }
                    ],
                }
            ]
        }

    @staticmethod
    def _dumps_catalog_redirect() -> str:
        """Generate redirect from .well-known path to API Catalog."""
        return dumps_redirect("/static/json/api-catalog.json")

    def _dumps_openapi_schema(self) -> dict:
        """Build OpenAPI JSON schema."""
        return json.loads(self._jinja.get_template("_assets/json/openapi.json.j2").render(version=self._meta.version))

    def _dumps_api_docs(self) -> str:
        """Build OpenAPI JSON schema."""
        page_meta: SitePageMeta = SitePageMeta(
            title="API Documentation",
            url=f"{self._meta.base_url}/legal/accessibility",
            description="API documentation explorer for the BAS Data Catalogue",
        )
        self._meta.html_title = page_meta.title
        self._meta.html_open_graph = page_meta.open_graph
        self._meta.html_schema_org = page_meta.schema_org
        raw = self._jinja.get_template("_views/guides/api.html.j2").render(meta=self._meta)
        return prettify_html(raw)

    def _export_catalog(self) -> None:
        """Export API Catalog to directory."""
        self._logger.info("Exporting API Catalog.")
        self._catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with self._catalog_path.open("w") as f:
            json.dump(self._dumps_catalog(), f, indent=2)
        self._catalog_well_known_path.parent.mkdir(parents=True, exist_ok=True)
        with self._catalog_well_known_path.open("w") as f:
            f.write(self._dumps_catalog_redirect())

    def _export_openapi_schema(self) -> None:
        """Export OpenAPI schema to directory."""
        self._logger.info("Exporting OpenAPI schema.")
        self._schema_path.parent.mkdir(parents=True, exist_ok=True)
        with self._schema_path.open("w") as f:
            json.dump(self._dumps_openapi_schema(), f, indent=2)

    def _export_api_docs(self) -> None:
        """Export API documentation guide to directory."""
        self._logger.info("Exporting API guide page.")
        self._docs_path.parent.mkdir(parents=True, exist_ok=True)
        with self._docs_path.open("w") as f:
            f.write(self._dumps_api_docs())

    def _publish_catalog(self) -> None:
        """Publish API Catalog to S3."""
        self._logger.info("Publishing API Catalog.")
        catalogue_key = self._s3_utils.calc_key(self._catalog_path)
        redirect_key = self._s3_utils.calc_key(self._catalog_well_known_path)
        media_type = "application/linkset+json; profile=https://www.rfc-editor.org/info/rfc9727"
        self._s3_utils.upload_content(
            key=catalogue_key, content_type=media_type, body=json.dumps(self._dumps_catalog(), indent=2)
        )
        self._s3_utils.upload_content(
            key=redirect_key, content_type="text/html", body=self._dumps_catalog_redirect(), redirect=catalogue_key
        )

    def _publish_openapi_schema(self) -> None:
        """Publish OpenAPI schema to S3."""
        self._logger.info("Publishing OpenAPI schema.")
        key = self._s3_utils.calc_key(self._schema_path)
        media_type = "application/vnd.oai.openapi+json;version=3.1"
        data = json.dumps(self._dumps_openapi_schema(), indent=2)
        self._s3_utils.upload_content(key=key, content_type=media_type, body=data)

    def _publish_api_docs(self) -> None:
        """Publish API documentation guide to S3."""
        self._logger.info("Publishing API guide page.")
        key = self._s3_utils.calc_key(self._docs_path)
        data = self._dumps_api_docs()
        self._s3_utils.upload_content(key=key, content_type="text/html", body=data)

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site API"

    def export(self) -> None:
        """Export API resources to directory."""
        self._export_catalog()
        self._export_openapi_schema()
        self._export_api_docs()

    def publish(self) -> None:
        """Publish API resources to S3."""
        self._publish_catalog()
        self._publish_openapi_schema()
        self._publish_api_docs()


class SiteHealthExporter(Exporter):
    """
    Site health check exporter.

    Generates health and monitoring endpoint as static JSON.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client, store: Store) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._store = store
        self._jinja = get_jinja_env()
        self._export_base = self._meta.export_path
        self._health_check_route = "static/json/health.json"
        self._health_alias_route = "-/health"
        self._health_check_path = self._export_base / self._health_check_route
        self._health_alias_path = self._export_base / self._health_alias_route

    def _dumps_health_check(self) -> dict:
        """
        Build Draft API Health Check as a JSON document.

        [1] https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check
        """
        return {
            "status": "pass",
            "version": "1",
            "releaseId": f"{self._meta.version}",
            "notes": [
                "This endpoint is intended for both liveness and readiness checks.",
                f"It is a static resource, representing the health of this service at: {self._meta.build_time.isoformat()}.",
            ],
            "description": "Health of BAS Data Catalogue (Lantern)",
            "checks": {
                "site:records": {
                    "componentId": "Site records",
                    "componentType": "datastore",
                    "observedValue": len(self._store),
                    "observedUnit": "items",
                    "status": "pass",
                    "affectedEndpoints": [f"{self._meta.base_url}/records/{{fileIdentifier}}.json"],
                    "time": f"{self._meta.build_time.isoformat()}",
                }
            },
            "links": {
                "about": "https://github.com/antarctica/lantern",
                "describedby": f"https://github.com/antarctica/lantern/blob/v{self._meta.version}/docs/monitoring.md#health-check-endpoint",
            },
        }

    def _dumps_health_redirect(self) -> str:
        """
        Generate redirect to static health response.

        In advance of the health check being dynamic and not served as a static file.
        """
        return dumps_redirect(f"/{self._health_check_route}")

    def _export_health(self) -> None:
        """Export health check and alias to directory."""
        self._logger.info("Exporting health check.")
        self._health_check_path.parent.mkdir(parents=True, exist_ok=True)
        with self._health_check_path.open("w") as f:
            json.dump(self._dumps_health_check(), f, indent=2)
        self._health_alias_path.parent.mkdir(parents=True, exist_ok=True)
        with self._health_alias_path.open("w") as f:
            f.write(self._dumps_health_redirect())

    def _publish_health(self) -> None:
        """Publish health check and alias to S3."""
        self._logger.info("Publishing health check.")
        health_key = self._s3_utils.calc_key(self._health_check_path)
        redirect_key = self._s3_utils.calc_key(self._health_alias_path)
        media_type = "application/health+json"
        self._s3_utils.upload_content(
            key=health_key, content_type=media_type, body=json.dumps(self._dumps_health_check(), indent=2)
        )
        self._s3_utils.upload_content(
            key=redirect_key, content_type="text/html", body=self._dumps_health_redirect(), redirect=health_key
        )

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site Health"

    def export(self) -> None:
        """Export health checks to directory."""
        self._export_health()

    def publish(self) -> None:
        """Publish health checks to S3."""
        self._publish_health()


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
        store: Store,
        selected_identifiers: set[str] | None = None,
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3)
        self._store = store

        self._resources_exporter = SiteResourcesExporter(logger=logger, meta=meta, s3=self._s3_client)
        self._pages_exporter = SitePagesExporter(logger=logger, meta=meta, s3=self._s3_client)
        self._api_exporter = SiteApiExporter(logger=logger, meta=meta, s3=self._s3_client)
        self._health_exporter = SiteHealthExporter(logger=logger, meta=meta, s3=self._s3_client, store=self._store)
        self._records_exporter = RecordsExporter(
            logger=logger,
            config=config,
            meta=meta,
            s3=self._s3_client,
            store=self._store,
            selected_identifiers=selected_identifiers,
        )
        self._index_exporter = SiteIndexExporter(
            logger=logger,
            meta=meta,
            s3=self._s3_client,
            select_records=self._store.select,
        )
        self._waf_exporter = WebAccessibleFolderExporter(
            logger=logger,
            meta=meta,
            s3=self._s3_client,
            select_records=self._store.select,
        )
        self._website_exporter = WebsiteSearchExporter(
            logger=logger,
            meta=meta,
            s3=self._s3_client,
            select_records=self._store.select,
        )

        self._exporters: list[Exporter] = [
            self._resources_exporter,
            self._pages_exporter,
            self._api_exporter,
            self._health_exporter,
            self._records_exporter,
            self._index_exporter,
            self._waf_exporter,
            self._website_exporter,
        ]

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

    def export(self) -> None:
        """Export site contents to a directory."""
        for exporter in self._exporters:
            exporter.export()

    def publish(self) -> None:
        """Publish site contents to S3."""
        for exporter in self._exporters:
            exporter.publish()
