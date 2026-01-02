import json
from datetime import UTC, datetime

import pytest
from bs4 import BeautifulSoup
from freezegun.api import FrozenDateTimeFactory
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.models.site import SiteMeta
from tests.conftest import freezer_time


class TestMacrosSite:
    """Test site template macros."""

    @staticmethod
    def _site_meta() -> SiteMeta:
        return SiteMeta(
            base_url="x",
            build_key="x",
            build_time=freezer_time(),
            html_title="x",
            sentry_src="x",
            plausible_domain="x",
            embedded_maps_endpoint="x",
            items_enquires_endpoint="x",
            items_enquires_turnstile_key="x",
            generator="x",
            version="x",
        )

    @staticmethod
    def _render(template: str, site_meta: SiteMeta | None = None) -> str:
        if site_meta is None:
            site_meta = TestMacrosSite._site_meta()
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        return jinja.from_string(template).render(meta=site_meta)

    def test_head_meta(self):
        """
        Can get static HTML character set.

        Basic sanity check.
        """
        template = """{% import '_macros/site.html.j2' as site %}{{ site.head_meta(meta) }}"""
        meta = self._site_meta()
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")
        assert html.head.meta["charset"] == "utf-8"

    def test_head_title(self):
        """Can get <title> with expected value from page."""
        expected = "x | BAS Data Catalogue"
        template = """{% import '_macros/site.html.j2' as site %}{{ site.head_title(meta.html_title_suffixed) }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.head.title.string == expected

    def test_head_open_graph(self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime):
        """
        Can get Open Graph <meta> tags with expected values from page.

        This only checks that Open Graph properties are rendered. The specific properties that should (not) be
        included are tested elsewhere.
        """
        freezer.move_to(fx_freezer_time)
        expected = {"x": "y"}
        template = """{% import '_macros/site.html.j2' as site %}{{ site.head_open_graph(meta.html_open_graph) }}"""
        meta = self._site_meta()
        meta.html_open_graph = expected
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")

        for key, val in expected.items():
            assert html.head.find(name="meta", property=key)["content"] == val

    def test_head_favicon(self):
        """Can get static favicon."""
        template = """{% import '_macros/site.html.j2' as site %}{{ site.head_favicon() }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.head.find(name="link", rel="icon") is not None

    @pytest.mark.parametrize(
        "href", ["https://cdn.web.bas.ac.uk/libs/font-awesome-pro/5.13.0/css/all.min.css", "/static/css/main.css"]
    )
    def test_head_styles(self, href: str):
        """Can get static CSS references."""
        template = """{% import '_macros/site.html.j2' as site %}{{ site.head_styles() }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.head.find("link", rel="stylesheet", href=lambda h: h and h.startswith(href)) is not None

    def test_script_sentry(self):
        """Can get Sentry script from page."""
        expected = "/static/js/sentry-preload.js?v=000"
        template = """{% import '_macros/site.html.j2' as site %}{{ site.script_sentry('000', meta.sentry_src) }}"""
        meta = self._site_meta()
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")
        assert html.head.find(name="script", src=expected) is not None
        assert html.head.find(name="script", src=meta.sentry_src) is not None

    def test_script_plausible(self):
        """Can get Plausible script from page."""
        template = """{% import '_macros/site.html.j2' as site %}{{ site.script_plausible(meta.plausible_domain) }}"""
        meta = self._site_meta()
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")
        assert html.head.find(name="script", attrs={"data-domain": meta.plausible_domain}) is not None

    def test_script_enhancements(self):
        """Can get progressive enhancements script from page."""
        expected = "/static/js/enhancements.js?v=000"
        template = """{% import '_macros/site.html.j2' as site %}{{ site.script_enhancements('000') }}"""
        meta = self._site_meta()
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")
        assert html.head.find(name="script", src=expected) is not None

    def test_head_schema_org(self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime):
        """
        Can get schema.org script content with expected values from page.

        This only checks that schema.org properties are rendered. The specific properties that should (not) be
        included are tested elsewhere.
        """
        freezer.move_to(fx_freezer_time)
        expected = {"x": "y"}
        template = """{% import '_macros/site.html.j2' as site %}{{ site.script_schema_org(meta.html_schema_org) }}"""
        meta = self._site_meta()
        meta.html_schema_org = json.dumps(expected)
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")
        data = json.loads(html.head.find(name="script", type="application/ld+json").string)

        assert expected == data

    @pytest.mark.parametrize(
        "meta",
        [
            SiteMeta(
                base_url="x",
                build_key="000",
                build_time=freezer_time(),
                html_title="x",
                sentry_src="x",
                plausible_domain="x",
                embedded_maps_endpoint="x",
                items_enquires_endpoint="x",
                items_enquires_turnstile_key="x",
                generator="x",
                version="x",
            ),
            SiteMeta(
                base_url="x",
                build_key="000",
                html_title="x",
                sentry_src="x",
                plausible_domain="x",
                embedded_maps_endpoint="x",
                items_enquires_endpoint="x",
                items_enquires_turnstile_key="x",
                generator="x",
                version="x",
                build_time=freezer_time(),
                build_repo_ref="x",
                build_repo_base_url="x",
                html_open_graph={"x": "y"},
                html_schema_org=json.dumps({"x": "y"}),
                html_description="x",
            ),
        ],
    )
    def test_html_head(self, meta: SiteMeta):
        """
        Can get HTML head elements.

        Integration test for head HTML macro. Checks dynamic elements only.
        Also acts as an implicit integration test for `head_scripts` macro.
        """
        cf_turnstile = "https://challenges.cloudflare.com/turnstile/v0/api.js"
        template = """{% import '_macros/site.html.j2' as site %}{{ site.html_head(meta) }}"""
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")

        assert html.head.meta["charset"] == "utf-8"
        assert html.head.title.string == meta.html_title_suffixed

        assert html.head.find("meta", attrs={"name": "generator"})["content"] == meta.generator
        assert html.head.find("meta", attrs={"name": "version"})["content"] == meta.version
        assert html.head.find("meta", attrs={"name": "generated"})["content"] == meta.build_time.isoformat()
        if meta.build_ref:
            assert html.head.find("meta", attrs={"name": "store-ref"})["content"] == meta.build_ref.value
        if meta.html_description:
            assert html.head.find("meta", attrs={"name": "description"})["content"] == meta.html_description

        assert html.head.find(name="script", src="/static/js/sentry-preload.js?v=000") is not None
        assert html.head.find(name="script", src=meta.sentry_src) is not None
        assert html.head.find(name="script", src=cf_turnstile) is not None
        assert html.head.find(name="script", attrs={"data-domain": meta.plausible_domain}) is not None
        assert html.head.find(name="script", src="/static/js/enhancements.js?v=000") is not None

        if meta.html_open_graph:
            open_graph_key = next(iter(meta.html_open_graph.keys()))
            open_graph_val = meta.html_open_graph[open_graph_key]
            assert html.head.find(name="meta", property=open_graph_key)["content"] == open_graph_val
        else:
            # check no open graph meta tags are defined
            assert all("og:" not in tag.get("property", "") for tag in html.head.find_all(name="meta"))

        if meta.html_schema_org:
            assert html.head.find(name="script", type="application/ld+json") is not None
        else:
            assert html.head.find(name="script", type="application/ld+json") is None

    def test_top_anchor(self):
        """Can get static page top anchor."""
        template = """{% import '_macros/site.html.j2' as site %}{{ site.top_anchor() }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.find(id="site-top") is not None

    def test_navbar_title(self):
        """Can get site title in navbar with expected static value."""
        template = """{% import '_macros/site.html.j2' as site %}{{ site.navbar() }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.find(id="site-title").string.strip() == "BAS Data Catalogue"

    def test_navbar_primary_nav(self):
        """Can get expected primary navigation links from navbar."""
        expected_labels = ["Part of British Antarctic Survey"]
        template = """{% import '_macros/site.html.j2' as site %}{{ site.navbar() }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        for label in expected_labels:
            assert any(label in a.text for a in html.find(id="site-nav").find_all("a"))

    def test_dev_phase(self):
        """Can get site dev phase label with expected static value."""
        template = """{% import '_macros/site.html.j2' as site %}{{ site.dev_phase() }}"""
        html = BeautifulSoup(self._render(template), parser="html.parser", features="lxml")

        assert html.find(id="site-dev-phase").string.strip() == "alpha"

    def test_footer(self, freezer: FrozenDateTimeFactory, fx_freezer_time: datetime):
        """Can get static site footer."""
        freezer.move_to(fx_freezer_time)
        expected = datetime.now(tz=UTC)
        template = """{% import '_macros/site.html.j2' as site %}{{ site.footer(meta) }}"""
        meta = self._site_meta()
        meta.build_time = expected
        html = BeautifulSoup(self._render(template, meta), parser="html.parser", features="lxml")

        assert html.find(id="site-footer") is not None
        assert str(expected.year) in html.find(id="site-footer").text
