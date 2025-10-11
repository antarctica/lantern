from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.models.site import SiteMeta


class TestLayoutPage:
    """Test page layout template."""

    @staticmethod
    def _render(template: str, site_meta: SiteMeta) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        return jinja.from_string(template).render(meta=site_meta)

    def test_page_header(self, fx_site_meta: SiteMeta):
        """Can set page header title."""
        expected = "x"
        template = (
            "{% extends '_layouts/page.html.j2' %} {% set header_main='"
            + expected
            + "' %} {% block page_content %}...{% endblock %}"
        )
        html = BeautifulSoup(self._render(template, site_meta=fx_site_meta), parser="html.parser", features="lxml")

        assert html.select_one("h1").text.strip() == expected
