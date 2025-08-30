import json

from bs4 import BeautifulSoup

from lantern.models.item.catalogue import ItemCatalogue


class TestItemTemplate:
    """Test base catalogue item template."""

    def test_html_head(self, fx_item_catalogue_model_min: ItemCatalogue):
        """
        Can set common page elements in site layout.

        Integration test between item template and site layout.
        """
        expected = fx_item_catalogue_model_min.page_metadata
        html = BeautifulSoup(fx_item_catalogue_model_min.render(), parser="html.parser", features="lxml")

        assert html.head.title.string == expected.html_title

        for key, val in expected.html_open_graph.items():
            assert html.head.find(name="meta", property=key)["content"] == val

        schema_org_item = json.loads(expected.html_schema_org)
        schema_org_page = json.loads(html.head.find(name="script", type="application/ld+json").string)
        assert schema_org_item == schema_org_page
