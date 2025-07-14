from datetime import date

import pytest
from bs4 import BeautifulSoup

from lantern.lib.metadata_library.models.record.elements.common import Date, Identifier
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    Constraint,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.models.item.catalogue import ItemCatalogue, Tab
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from tests.conftest import _item_catalogue_min


class TestMacrosItem:
    """Test item template macros."""

    def test_header(self, fx_item_catalogue_min: ItemCatalogue):
        """Can get item header with expected values from item."""
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")
        expected = fx_item_catalogue_min.page_header

        assert html.select_one("#item-header-type i")["class"] == expected.subtitle[1].split(" ")
        assert html.select_one("#item-header-type").text.strip() == expected.subtitle[0]
        assert html.select_one("#item-header-title").text.strip() == expected.title

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="x", namespace="y"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                ]
            ),
        ],
    )
    def test_collections(self, fx_item_catalogue_min: ItemCatalogue, value: Aggregations):
        """Can get item collections with expected values from item."""
        fx_item_catalogue_min._record.identification.aggregations = value
        expected = fx_item_catalogue_min.summary.collections
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if len(expected) > 0:
            assert html.select_one("#summary-collections") is not None
        else:
            assert html.select_one("#summary-collections") is None

        for collection in expected:
            assert html.select_one(f"a[href='{collection.href}']") is not None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.PAPER_MAP,
                    )
                ]
            ),
        ],
    )
    def test_physical_parent(self, fx_item_catalogue_min_physical_map: ItemCataloguePhysicalMap, value: Aggregations):
        """Can get item physical map parent with expected value from item."""
        fx_item_catalogue_min_physical_map._record.identification.aggregations = value
        expected = fx_item_catalogue_min_physical_map.summary.physical_parent
        html = BeautifulSoup(fx_item_catalogue_min_physical_map.render(), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one(f"#summary-physical-parent a[href='{expected.href}']") is not None
        else:
            assert html.select_one("#summary-physical-parent") is None

    @pytest.mark.parametrize("value", [None, "x"])
    def test_edition(self, fx_item_catalogue_min: ItemCatalogue, value: str | None):
        """Can get item edition with expected value from item."""
        fx_item_catalogue_min._record.identification.edition = value
        expected = fx_item_catalogue_min.summary.edition
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected is None:
            assert html.select_one("#summary-edition") is None
        else:
            assert html.select_one("#summary-edition").text.strip() == expected

    @pytest.mark.parametrize("value", [None, (Date(date=date(2023, month=10, day=31)))])
    def test_published(self, fx_item_catalogue_min: ItemCatalogue, value: Date | None):
        """Can get item publication with expected value from item."""
        fx_item_catalogue_min._record.identification.dates.publication = value
        expected = fx_item_catalogue_min.summary.published
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected is None:
            assert html.select_one("#summary-published") is None
        else:
            assert html.select_one("#summary-published").text.strip() == expected.value
            assert html.select_one("#summary-published")["datetime"] == expected.datetime

    @pytest.mark.parametrize(
        "value",
        [
            Constraint(
                type=ConstraintTypeCode.ACCESS,
                restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                statement="Open Access",
            ),
            Constraint(
                type=ConstraintTypeCode.ACCESS,
                restriction_code=ConstraintRestrictionCode.RESTRICTED,
                statement="Closed Access",
            ),
        ],
    )
    def test_access(self, fx_item_catalogue_min: ItemCatalogue, value: Constraint):
        """Can get item access with expected value from item."""
        fx_item_catalogue_min._record.identification.constraints.append(value)
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if value.restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
            assert html.select_one("#summary-access") is None
        else:
            assert html.select_one("#summary-access").text.strip() == "Restricted"

    @pytest.mark.parametrize("value", [None, "x"])
    def test_citation(self, fx_item_catalogue_min: ItemCatalogue, value: str | None):
        """Can get item citation with expected value from item."""
        fx_item_catalogue_min._record.identification.other_citation_details = value
        expected = fx_item_catalogue_min.summary.citation
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")

        if expected is None:
            assert html.select_one("#summary-citation") is None
        else:
            assert expected in str(html.select_one("#summary-citation"))

    _published = Date(date=date(2023, month=10, day=31))

    def test_abstract(self, fx_item_catalogue_min: ItemCatalogue):
        """Can get item abstract with expected value from item."""
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")
        expected = fx_item_catalogue_min.summary.abstract
        assert expected in str(html.select_one("#summary-abstract"))

    @pytest.mark.parametrize(
        "value",
        [
            GraphicOverviews([]),
            GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")]),
            GraphicOverviews(
                [
                    GraphicOverview(identifier="x", href="x", mime_type="x"),
                    GraphicOverview(identifier="y", href="y", mime_type="y"),
                ]
            ),
        ],
    )
    def test_graphics(self, fx_item_catalogue_min: ItemCatalogue, value: GraphicOverviews):
        """Can get item graphics with expected values from item."""
        fx_item_catalogue_min._record.identification.graphic_overviews = value
        expected = fx_item_catalogue_min.graphics
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")

        assert html.select_one("#item-graphics") is not None

        if len(expected) > 0:
            graphic = expected[0]
            graphic_html = html.select_one(f"#graphics-{graphic.identifier}")
            assert graphic_html is not None
            assert graphic_html["src"] == graphic.href

        # Disabled until we can display multiple graphics sensibly.
        # for graphic in expected:
        #     graphic_html = html.select_one(f"#graphics-{graphic.identifier}")  # noqa: ERA001
        #     assert graphic_html is not None  # noqa: ERA001
        #     assert graphic_html["src"] == graphic.href  # noqa: ERA001

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="a", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                        initiative_type=AggregationInitiativeCode.PAPER_MAP,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="b", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                        initiative_type=AggregationInitiativeCode.PAPER_MAP,
                    ),
                ]
            ),
        ],
    )
    def test_sides(self, fx_item_catalogue_min_physical_map: ItemCataloguePhysicalMap, value: Aggregations):
        """
        Can get item sides with expected values from physical map item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_catalogue_min_physical_map._record.identification.aggregations = value
        expected: list | None = fx_item_catalogue_min_physical_map.sides
        html = BeautifulSoup(fx_item_catalogue_min_physical_map.render(), parser="html.parser", features="lxml")

        sides = html.select_one("#item-sides")
        assert sides is not None if expected else sides is None
        if sides is None:
            return

        for item in expected:
            # find an article element containing a link matching side[1].href
            side = next(
                (article for article in sides.find_all("article") if article.find("a", href=item[1].href)), None
            )
            assert side is not None
            assert item[0] in str(side)

    @pytest.mark.parametrize("tab", _item_catalogue_min().tabs)
    def test_tabs_nav(self, fx_item_catalogue_min: ItemCatalogue, tab: Tab):
        """Can get enabled tabs based on item."""
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")
        tab_input = html.select_one(f"#tab-{tab.anchor}")
        tab_label = html.select_one(f"label[for=tab-{tab.anchor}]")
        tab_content = html.select_one(f"#tab-content-{tab.anchor}")

        if tab.enabled:
            assert tab_input is not None
            assert tab_content is not None
            assert tab_label.select_one("i")["class"] == tab.icon.split(" ")
            assert tab_label.text.strip() == tab.title
        else:
            assert tab_input is None
            assert tab_label is None
            assert tab_content is None

    def test_tab_nav_default(self, fx_item_catalogue_min: ItemCatalogue):
        """
        Can get default tab based on item.

        Tab switching is not tested here as it's dynamic, see e2e tests.
        """
        html = BeautifulSoup(fx_item_catalogue_min.render(), parser="html.parser", features="lxml")
        expected = fx_item_catalogue_min.default_tab_anchor

        tab_input = html.select_one(f"#tab-{expected}")["checked"]
        assert tab_input is not None
