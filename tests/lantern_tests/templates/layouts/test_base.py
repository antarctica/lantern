import json

from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.models.templates import PageMetadata


class TestLayoutBase:
    """Test base layout template."""

    @property
    def page_metadata(self) -> PageMetadata:
        """Get page metadata."""
        return PageMetadata(
            build_key="x",
            html_title="x",
            sentry_src="x",
            plausible_domain="x",
            html_open_graph={"x": "y"},
            html_schema_org=json.dumps({"x": "y"}),
        )

    def _render(self) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = """{% extends "_layouts/base.html.j2" %}{% block content %}...{% endblock %}"""
        return jinja.from_string(template).render(meta=self.page_metadata)

    def test_head(self):
        """Can set common page elements."""
        meta = self.page_metadata
        html = BeautifulSoup(self._render(), parser="html.parser", features="lxml")

        assert html.head.title.string == meta.html_title

        for key, val in meta.html_open_graph.items():
            assert html.head.find(name="meta", property=key)["content"] == val

        schema_org_item = json.loads(meta.html_schema_org)
        schema_org_page = json.loads(html.head.find(name="script", type="application/ld+json").string)
        assert schema_org_item == schema_org_page

    def test_cache_busting(self):
        """Can set cache busting query string param on relevant resources."""
        meta = self.page_metadata
        html = BeautifulSoup(self._render(), parser="html.parser", features="lxml")

        main_css = html.head.find("link", rel="stylesheet", href=lambda h: h and h.startswith("/static/css/main.css"))
        assert main_css["href"].endswith(f"?v={meta.build_key}")

        favicon_rels = ["shortcut icon", "icon", "apple-touch-icon", "manifest"]
        for rel in favicon_rels:
            assert html.head.find("link", rel=rel)["href"].endswith(f"?v={meta.build_key}")
