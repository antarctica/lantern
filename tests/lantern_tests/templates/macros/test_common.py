"""
Test specific common template macros.

By their nature common macros are used across multiple templates and so captured in numerous other tests.
Some macros with conditional logic for example are tested here specifically to verify their behaviour.
"""

from copy import deepcopy
from datetime import date

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.elements.common import Constraint, Constraints, Date, Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, set_admin
from lantern.models.item.catalogue.elements import ItemCatalogueSummary
from lantern.models.record.revision import RecordRevision
from tests.conftest import _admin_meta_keys, _revision_config_min


class TestPageHeader:
    """Test page header common macro."""

    @staticmethod
    def _render(config: dict) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = """{% import '_macros/common.html.j2' as com %}{{ com.page_header(**config) }}"""
        return jinja.from_string(template).render(config=config)

    def test_main(self):
        """Can render a minimal page header with main content only."""
        expected = "x"
        html = BeautifulSoup(self._render({"main": expected}), parser="html.parser", features="lxml")
        assert html.select_one("h1").text.strip() == expected

    @pytest.mark.parametrize(("sub", "sub_i"), [("x", None), ("x", "x")])
    def test_subheader(self, sub: str, sub_i: str | None):
        """Can render a page header with optional subheader with and without icon."""
        html = BeautifulSoup(self._render({"sub": sub, "sub_i": sub_i}), parser="html.parser", features="lxml")

        assert html.select_one("small").text.strip() == sub
        if sub_i is not None:
            assert html.select_one("small i")["class"] == sub_i.split(" ")

    def test_id(self):
        """Can render a page header with optional id selectors for each component."""
        html = BeautifulSoup(
            self._render({"id_wrapper": "x", "id_sub": "y", "id_main": "z", "sub": "..."}),
            parser="html.parser",
            features="lxml",
        )

        assert html.select_one("#x") is not None
        assert html.select_one("#y") is not None
        assert html.select_one("#z") is not None


class TestItemSummary:
    """Test item summary common macro."""

    record = RecordRevision.loads(_revision_config_min())
    record.file_identifier = "x"
    record.hierarchy_level = HierarchyLevelCode.PRODUCT
    record.identification.title = "y"
    record.identification.purpose = "z"

    summary_base = ItemCatalogueSummary(record=record, admin_meta_keys=_admin_meta_keys())

    @staticmethod
    def _render(item: ItemCatalogueSummary) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = """{% import '_macros/common.html.j2' as com %}{{ com.item_summary(item) }}"""
        return jinja.from_string(template).render(item=item)

    def test_anchor(self):
        """Can get title and href with expected values from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        assert summary.title_html in str(html.select_one("a"))
        assert html.select_one("a")["href"] == summary.href

    def test_summary(self):
        """Can get summary description with expected value from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        assert summary.summary_html in str(html.select_one("article"))

    def test_graphic(self):
        """Can get graphic with expected value from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        assert html.select_one("img")["src"] == summary.href_graphic[0]

    def test_type(self):
        """Can get item type with expected value from summary."""
        summary = self.summary_base
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        # span containing item type can only be matched by text. Can't match directly because span contains <i> tag
        assert any(summary.fragments.item_type in span.text for span in html.find_all(name="span"))
        assert html.select_one("i")["class"] == summary.fragments.item_type_icon.split(" ")

    @pytest.mark.parametrize("edition", [None, "x"])
    def test_edition(self, edition: str | None):
        """Can get optional edition with expected value from summary."""
        record = deepcopy(self.summary_base._record)
        record.identification.edition = edition
        summary = ItemCatalogueSummary(record=record, admin_meta_keys=self.summary_base._admin_keys)
        expected = summary.fragments.edition
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        if expected:
            # noinspection PyTypeChecker
            assert html.find(name="span", string=expected) is not None

    @pytest.mark.parametrize("published", [None, Date(date=date(2023, 10, 31))])
    def test_published(self, published: Date | None):
        """Can get optional publication date with expected value from summary."""
        record = deepcopy(self.summary_base._record)
        record.identification.dates.publication = published
        summary = ItemCatalogueSummary(record=record, admin_meta_keys=self.summary_base._admin_keys)
        expected = summary.fragments.published
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("time").text.strip() == expected.value
            assert html.select_one("time")["datetime"] == expected.datetime

    @pytest.mark.parametrize("value", [0, 1, 2])
    def test_items(self, value: int | None):
        """Can get optional child item count with expected value from summary."""
        agg = Aggregation(
            identifier=Identifier(identifier="x", namespace="x"),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
        )
        record = deepcopy(self.summary_base._record)
        record.identification.aggregations.extend([agg for _ in range(value)])
        summary = ItemCatalogueSummary(record=record, admin_meta_keys=self.summary_base._admin_keys)
        expected = summary.fragments.children
        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")

        if expected:
            # noinspection PyTypeChecker
            assert html.find(name="span", string=expected) is not None
        else:
            # noinspection PyTypeChecker
            assert html.find(name="span", string="0 items") is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                    statement="Open Access",
                ),
                False,
            ),
            (
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.RESTRICTED,
                    statement="Closed Access",
                ),
                True,
            ),
        ],
    )
    def test_access(self, fx_admin_meta_keys: AdministrationKeys, value: Constraint, expected: bool):
        """
        Can get access type with expected value from summary.

        Only shown if restricted.
        """
        record = deepcopy(self.summary_base._record)
        record.identification.constraints = Constraints([value])
        if value.restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
            admin_meta = Administration(id=record.file_identifier, access_permissions=[OPEN_ACCESS])
            set_admin(keys=fx_admin_meta_keys, record=record, admin_meta=admin_meta)
        summary = ItemCatalogueSummary(record=record, admin_meta_keys=self.summary_base._admin_keys)

        html = BeautifulSoup(self._render(summary), parser="html.parser", features="lxml")
        result = html.find(lambda tag: tag.name == "span" and "Restricted" in tag.get_text())
        if expected:
            assert result is not None
        else:
            assert result is None


class TestDefinitionListItem:
    """Test DL item common macro."""

    @staticmethod
    def _render(config: dict, value: str) -> str:
        _loader = PackageLoader("lantern", "resources/templates")
        jinja = Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
        template = (
            """{% import '_macros/common.html.j2' as com %}{% call com.dl_item(**config) %}{{ value }}{% endcall %}"""
        )
        return jinja.from_string(template).render(config=config, value=value)

    def test_main(self):
        """Can render a minimal DL item with minimal properties only."""
        config = {"title": "x", "id": "x"}
        value = "x"
        html = BeautifulSoup(
            self._render(config={"title": config["title"], "id": config["id"]}, value=value),
            parser="html.parser",
            features="lxml",
        )
        assert html.select_one("dt").text.strip() == config["title"]
        assert html.select_one("dd", id=config["id"]) is not None

    def test_dd_class(self):
        """Can render a DL item classes on the DD element."""
        dd_class = "x"
        html = BeautifulSoup(
            self._render(config={"title": "x", "id": "x", "dd_class": dd_class}, value="x"),
            parser="html.parser",
            features="lxml",
        )
        assert html.select_one(f"dd.{dd_class}") is not None
