from datetime import UTC, date, datetime

import cattrs
import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, DomainConsistency, Lineage
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestDomainConsistency:
    """Test DomainConsistency element."""

    def test_init(self):
        """Can create a DomainConsistency element from directly assigned properties."""
        expected = "x"
        values = {
            "specification": Citation(
                title="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)))
            ),
            "explanation": expected,
            "result": True,
        }
        domain_consistency = DomainConsistency(**values)

        assert domain_consistency.specification.title == "x"
        assert domain_consistency.explanation == expected
        assert domain_consistency.result is True


class TestLineage:
    """Test Lineage element."""

    def test_init(self):
        """Can create a Lineage element from directly assigned properties."""
        expected = "x"
        values = {"statement": expected}
        lineage = Lineage(**values)

        assert lineage.statement == expected


class TestDataQuality:
    """Test DataQuality element."""

    @pytest.mark.parametrize(
        "values",
        [
            {},
            {"lineage": Lineage(statement="x")},
            {
                "domain_consistency": [
                    DomainConsistency(
                        specification=Citation(
                            title="x",
                            dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
                        ),
                        explanation="x",
                        result=True,
                    )
                ],
            },
            {
                "lineage": Lineage(statement="x"),
                "domain_consistency": [
                    DomainConsistency(
                        specification=Citation(
                            title="x",
                            dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
                        ),
                        explanation="x",
                        result=True,
                    )
                ],
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a DataQuality element from directly assigned properties."""
        expected = "x"
        data_quality = DataQuality(**values)

        if "lineage" in values:
            assert data_quality.lineage.statement == expected
        else:
            assert data_quality.lineage is None

        if "domain_consistency" in values:
            assert data_quality.domain_consistency == values["domain_consistency"]
        else:
            assert data_quality.domain_consistency == []

    def test_structure_cattrs(self):
        """Can use Cattrs to create a DataQuality instance from plain types."""
        expected_date = date(2014, 6, 30)
        value = {
            "lineage": {"statement": "x"},
            "domain_consistency": [
                {
                    "specification": {
                        "title": {"value": "x"},
                        "dates": {"creation": expected_date.isoformat()},
                        "contact": {"organisation": {"name": "x"}, "role": [ContactRoleCode.PUBLISHER.value]},
                    },
                    "explanation": "x",
                    "result": True,
                }
            ],
        }
        expected = DataQuality(
            lineage=Lineage(statement="x"),
            domain_consistency=[
                DomainConsistency(
                    specification=Citation(
                        title="x",
                        dates=Dates(creation=Date(date=expected_date)),
                        contacts=Contacts(
                            [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.PUBLISHER})]
                        ),
                    ),
                    explanation="x",
                    result=True,
                )
            ],
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(DataQuality, lambda d, t: DataQuality.structure(d))
        result = converter.structure(value, DataQuality)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a DataQuality instance into plain types."""
        expected_date = date(2014, 6, 30)
        value = DataQuality(
            lineage=Lineage(statement="x"),
            domain_consistency=[
                DomainConsistency(
                    specification=Citation(
                        title="x",
                        dates=Dates(creation=Date(date=expected_date)),
                        contacts=Contacts(
                            [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.PUBLISHER})]
                        ),
                    ),
                    explanation="x",
                    result=True,
                )
            ],
        )
        expected = {
            "lineage": {"statement": "x"},
            "domain_consistency": [
                {
                    "specification": {
                        "title": {"value": "x"},
                        "dates": {"creation": expected_date.isoformat()},
                        "contact": {"organisation": {"name": "x"}, "role": [ContactRoleCode.PUBLISHER.value]},
                    },
                    "explanation": "x",
                    "result": True,
                }
            ],
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected
