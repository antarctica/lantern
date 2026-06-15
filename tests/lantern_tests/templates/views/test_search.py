from bs4 import BeautifulSoup

from lantern.models.site import SiteMeta
from lantern.utils import get_jinja_env


class TestSearchTemplate:
    """Test base catalogue item template."""

    def test_script_algolia(self, fx_site_meta: SiteMeta):
        """Can get Algolia scripts from page."""
        expected = "/static/js/search.js?v="

        jinja = get_jinja_env()
        html = BeautifulSoup(
            jinja.get_template("_views/search.html.j2").render(meta=fx_site_meta), parser="html.parser", features="lxml"
        )
        assert html.head.find(name="script", attrs={"src": expected}) is not None
