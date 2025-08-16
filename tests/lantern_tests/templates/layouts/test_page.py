import json
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.models.templates import PageMetadata


class TestLayoutPage:
    """Test page layout template."""

    @property
    def page_metadata(self) -> PageMetadata:
        """Get page metadata."""
        return PageMetadata(
            build_key="x",
            build_time=datetime.now(tz=UTC),
            html_title="x",
            sentry_src="x",
            plausible_domain="x",
            html_open_graph={"x": "y"},
            html_schema_org=json.dumps({"x": "y"}),
        )

    def _render(self, template: str) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        return jinja.from_string(template).render(meta=self.page_metadata)

    def test_page_header(self):
        """Can set page header title."""
        expected = "x"
        template = (
            "{% extends '_layouts/page.html.j2' %} {% set header_main='"
            + expected
            + "' %} {% block page_content %}...{% endblock %}"
        )
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.select_one("h1").text.strip() == expected
