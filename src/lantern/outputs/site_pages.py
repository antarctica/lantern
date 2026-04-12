import logging
from http import HTTPStatus
from pathlib import Path

from lantern.models.checks import Check, CheckType
from lantern.models.site import ExportMeta, SiteContent, SitePageMeta
from lantern.outputs.base import OutputSite
from lantern.utils import prettify_html


class SitePagesOutput(OutputSite):
    """
    Site supporting pages exporter.

    Generates pages from Jinja2 view templates for legal policies, guides, 404, etc.

    Note: Static pages may also be generated in other output classes (e.g. `lantern.outputs.site_api.SiteApiOutput`).
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        super().__init__(logger=logger, meta=meta, name="Site Pages", check_type=CheckType.SITE_PAGES)

    @property
    def _object_meta(self) -> dict[str, str]:
        return {"build_key": self._meta.build_key}

    @staticmethod
    def _page_path(template_path: str) -> Path:
        """Get relative static path based on page view."""
        if template_path == "_views/404.html.j2":
            return Path("404.html")
        return Path(template_path.replace("_views/", "").split(".")[0]) / "index.html"

    @property
    def _page_meta(self) -> dict[str, SitePageMeta]:
        """Site metadata per page view."""
        return {
            "_views/404.html.j2": SitePageMeta(title="Not Found", url="-", inc_meta=False),
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
            "_views/guides/map-purchasing.html.j2": SitePageMeta(
                title="Map Purchasing",
                url=f"{self._meta.base_url}/guides/map-purchasing",
                description="How to order BAS published maps",
            ),
        }

    def _page_content(self, template_path: str) -> str:
        """Page content per page view."""
        page_meta: SitePageMeta = self._page_meta[template_path]
        self._meta.apply_page_meta(page_meta)
        raw = self._jinja.get_template(template_path).render(meta=self._meta)
        return prettify_html(raw)

    @property
    def content(self) -> list[SiteContent]:
        """Output content for site pages."""
        return [
            SiteContent(
                content=self._page_content(page_view),
                path=self._page_path(page_view),
                media_type="text/html",
                object_meta=self._object_meta,
            )
            for page_view in self._page_meta
        ]

    @property
    def checks(self) -> list[Check]:
        """Output checks."""
        checks = super().checks
        checks.append(
            Check(
                type=CheckType.SITE_404,
                url=f"{self._meta.base_url}/invalid",
                http_status=HTTPStatus.NOT_FOUND,
            )
        )
        return checks
