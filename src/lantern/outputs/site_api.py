import json
import logging
from pathlib import Path

from lantern.models.site import ExportMeta, SiteContent, SitePageMeta, SiteRedirect
from lantern.outputs.base import OutputSite
from lantern.utils import prettify_html


class SiteApiOutput(OutputSite):
    """
    Site API schemas and documentation output.

    Generates an API Catalogue and OpenAPI schema as JSON, and interactive OpenAPI documentation.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        """Initialise."""
        super().__init__(logger, meta)
        self._catalog_path = Path("static") / "json" / "api-catalog.json"
        self._docs_path = Path("guides") / "api" / "index.html"
        self._openapi_template_path = "_assets/json/openapi.json.j2"
        self._api_docs_template_path = "_views/guides/api.html.j2"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Site API"

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {"build_key": self._meta.build_key}

    @property
    def _catalog_content(self) -> str:
        """Generate RFC 9727 API Catalog as a JSON document."""
        return json.dumps(
            {
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
            },
            indent=2,
            ensure_ascii=False,
        )

    @property
    def _schema_content(self) -> str:
        """Generate OpenAPI schema JSON."""
        return self._jinja.get_template(self._openapi_template_path).render(version=self._meta.version)

    @property
    def _docs_content(self) -> str:
        """Generate OpenAPI HTML using Scalar.js."""
        page_meta: SitePageMeta = SitePageMeta(
            title="API Documentation",
            url=f"{self._meta.base_url}/{self._docs_path}",
            description="API documentation explorer for the BAS Data Catalogue",
        )
        self._meta.html_title = page_meta.title
        self._meta.html_open_graph = page_meta.open_graph
        self._meta.html_schema_org = page_meta.schema_org
        raw = self._jinja.get_template(self._api_docs_template_path).render(meta=self._meta)
        return prettify_html(raw)

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content for site."""
        return [
            SiteContent(
                content=self._catalog_content,
                path=self._catalog_path,
                media_type="application/linkset+json; profile=https://www.rfc-editor.org/info/rfc9727",
            ),
            SiteRedirect(
                path=Path(".well-known") / "api-catalog",
                target=self._meta.base_url + "/" + str(self._catalog_path),
            ),
            SiteContent(
                content=self._schema_content,
                path=Path("static") / "json" / "openapi.json",
                media_type="application/vnd.oai.openapi+json;version=3.1",
            ),
            SiteContent(
                content=self._docs_content,
                path=self._docs_path,
                media_type="text/html",
                object_meta=self._object_meta,
            ),
        ]
