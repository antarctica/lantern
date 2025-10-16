import pytest

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import AggregationAssociationCode, AggregationInitiativeCode
from lantern.lib.metadata_library.models.record.presets.aggregations import (
    make_bas_cat,
    make_bas_cat_collection_member,
    make_bas_cat_cross_ref,
    make_in_bas_cat_collection,
)


class TestMakeBasCat:
    """Tests for `make_bas_cat()` present."""

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                {"item_id": "x", "association": AggregationAssociationCode.LARGER_WORK_CITATION, "initiative": None},
                Aggregation(
                    identifier=Identifier(
                        identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk"
                    ),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                ),
            ),
            (
                {
                    "item_id": "x",
                    "association": AggregationAssociationCode.LARGER_WORK_CITATION,
                    "initiative": AggregationInitiativeCode.CAMPAIGN,
                },
                Aggregation(
                    identifier=Identifier(
                        identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk"
                    ),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                    initiative_type=AggregationInitiativeCode.CAMPAIGN,
                ),
            ),
        ],
    )
    def test_default(self, values: dict, expected: str):
        """Can make an aggregation for an item."""
        result = make_bas_cat(**values)
        assert result == expected


class TestMakeInBasCatCollection:
    """Test `make_in_bas_cat_collection()` preset."""

    def test_default(self):
        """Can make an aggregation for a collection."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        result = make_in_bas_cat_collection("x")

        assert result == expected


class TestMakeBasCatCollectionMember:
    """Test `make_bas_cat_collection_member()` preset."""

    def test_default(self):
        """Can make an aggregation for an item in a collection."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk"),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        result = make_bas_cat_collection_member("x")

        assert result == expected


class TestMakeBasCatCrossRef:
    """Test `make_bas_cat_cross_ref()` preset."""

    def test_default(self):
        """Can make an aggregation for an item related to another."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk"),
            association_type=AggregationAssociationCode.CROSS_REFERENCE,
        )
        result = make_bas_cat_cross_ref("x")

        assert result == expected
