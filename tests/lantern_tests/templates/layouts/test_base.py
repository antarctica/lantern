import json

from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.models.site import SiteMeta


class TestLayoutBase:
    """Test base layout template."""

    @staticmethod
    def _render(site_meta: SiteMeta) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = """{% extends "_layouts/base.html.j2" %}{% block content %}...{% endblock %}"""
        return jinja.from_string(template).render(meta=site_meta)

    def test_head(self, fx_site_meta: SiteMeta):
        """Can set common page elements."""
        fx_site_meta.html_title = "x"
        fx_site_meta.html_open_graph = {"x": "y"}
        fx_site_meta.html_schema_org = json.dumps({"x": "y"})
        html = BeautifulSoup(self._render(fx_site_meta), parser="html.parser", features="lxml")

        assert html.head.title.string == fx_site_meta.html_title_suffixed

        for key, val in fx_site_meta.html_open_graph.items():
            assert html.head.find(name="meta", property=key)["content"] == val

        schema_org_item = json.loads(fx_site_meta.html_schema_org)
        schema_org_page = json.loads(html.head.find(name="script", type="application/ld+json").string)
        assert schema_org_item == schema_org_page

    def test_cache_busting(self, fx_site_meta: SiteMeta):
        """Can set cache busting query string param on relevant resources."""
        fx_site_meta.build_key = "x"
        html = BeautifulSoup(self._render(fx_site_meta), parser="html.parser", features="lxml")

        main_css = html.head.find("link", rel="stylesheet", href=lambda h: h and h.startswith("/static/css/main.css"))
        assert main_css["href"].endswith(f"?v={fx_site_meta.build_key}")

        favicon_rels = ["shortcut icon", "icon", "apple-touch-icon", "manifest"]
        for rel in favicon_rels:
            assert html.head.find("link", rel=rel)["href"].endswith(f"?v={fx_site_meta.build_key}")
