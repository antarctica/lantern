from datetime import date

import pytest

from lantern.models.record import HierarchyLevelCode
from lantern.models.record.elements.common import Date, Identifier
from lantern.models.record.presets.citation import make_magic_citation


class TestMakeMagicCitation:
    """Tests for `make_magic_citation()` present."""

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                {
                    "title": "x",
                    "hierarchy_level": HierarchyLevelCode.DATASET,
                    "edition": None,
                    "publication_date": None,
                    "identifiers": None,
                },
                "British Antarctic Survey (?year). _x_ (Version ?version) [Dataset]. British Antarctic Survey Mapping and Geographic Information Centre. [?](?).",
            ),
            (
                {
                    "title": "x",
                    "hierarchy_level": HierarchyLevelCode.DATASET,
                    "edition": "x",
                    "publication_date": Date(date=date(2014, 6, 30)),
                    "identifiers": [
                        Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")
                    ],
                },
                "British Antarctic Survey (2014). _x_ (Version x) [Dataset]. British Antarctic Survey Mapping and Geographic Information Centre. [https://data.bas.ac.uk/items/x](https://data.bas.ac.uk/items/x).",
            ),
        ],
    )
    def test_default(self, values: dict, expected: str):
        """Can generate a MAGIC citation."""
        result = make_magic_citation(**values)
        assert result == expected
