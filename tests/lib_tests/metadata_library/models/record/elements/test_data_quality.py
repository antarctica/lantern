from copy import deepcopy
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
from lantern.lib.metadata_library.models.record.elements.data_quality import (
    DataQuality,
    DomainConsistencies,
    DomainConsistency,
    Lineage,
)
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict, clean_list


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


class TestDomainConsistencies:
    """Test DomainConsistency's container."""

    def test_init(self):
        """Can create an DomainConsistencies container from directly assigned properties."""
        expected = DomainConsistency(
            specification=Citation(
                title="x",
                dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
            ),
            explanation="x",
            result=True,
        )
        domains = DomainConsistencies([expected])

        assert len(domains) == 1
        assert domains[0] == expected

    def test_filter_href(self):
        """Can filter domain consistency elements by a specification href."""
        domain_a = DomainConsistency(
            specification=Citation(
                title="x",
                href="a",
                dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
            ),
            explanation="x",
            result=True,
        )
        domain_b = deepcopy(domain_a)
        domain_b.specification.href = "b"
        domains = DomainConsistencies([domain_a, domain_b])
        expected = DomainConsistencies([domain_a])

        result = domains.filter(domain_a.specification.href)
        assert result == expected

    test_ensure_domain = DomainConsistency(
        specification=Citation(
            title="x",
            dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
        ),
        explanation="x",
        result=True,
    )

    @pytest.mark.parametrize(
        ("before", "after"),
        [
            (DomainConsistencies([]), DomainConsistencies([test_ensure_domain])),
            (DomainConsistencies([test_ensure_domain]), DomainConsistencies([test_ensure_domain])),
        ],
    )
    def test_ensure(self, before: DomainConsistencies, after: DomainConsistencies):
        """Can append a domain consistency element as needed."""
        value = self.test_ensure_domain

        before.ensure(value)
        assert before == after

    def test_structure(self):
        """Can create an DomainConsistencies container by converting a list of plain types."""
        expected = DomainConsistencies(
            [
                DomainConsistency(
                    specification=Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))),
                    explanation="x",
                    result=True,
                )
            ]
        )
        result = DomainConsistencies.structure(
            [
                {
                    "specification": {"title": {"value": "x"}, "dates": {"creation": "2014-06-30"}},
                    "explanation": "x",
                    "result": True,
                }
            ]
        )
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Identifiers instance from plain types."""
        value = [
            {
                "specification": {"title": {"value": "x"}, "dates": {"creation": "2014-06-30"}},
                "explanation": "x",
                "result": True,
            }
        ]
        expected = DomainConsistencies(
            [
                DomainConsistency(
                    specification=Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))),
                    explanation="x",
                    result=True,
                )
            ]
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(DomainConsistencies, lambda d, t: DomainConsistencies.structure(d))
        result = converter.structure(value, DomainConsistencies)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert an Identifiers instance into plain types."""
        value = DomainConsistencies(
            [
                DomainConsistency(
                    specification=Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))),
                    explanation="x",
                    result=True,
                )
            ]
        )
        expected = [
            {
                "specification": {"title": {"value": "x"}, "dates": {"creation": "2014-06-30"}},
                "explanation": "x",
                "result": True,
            }
        ]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(DomainConsistencies, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


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
            assert data_quality.domain_consistency == DomainConsistencies(values["domain_consistency"])
        else:
            assert data_quality.domain_consistency == DomainConsistencies([])

    @pytest.mark.parametrize("has_spec_contact", [False, True])
    def test_structure_cattrs(self, has_spec_contact: bool):
        """Can use Cattrs to create a DataQuality instance from plain types."""
        expected_date = date(2014, 6, 30)
        value: dict = {
            "lineage": {"statement": "x"},
            "domain_consistency": [
                {
                    "specification": {"title": {"value": "x"}, "dates": {"creation": expected_date.isoformat()}},
                    "explanation": "x",
                    "result": True,
                }
            ],
        }
        if has_spec_contact:
            value["domain_consistency"][0]["specification"]["contact"] = {
                "organisation": {"name": "x"},
                "role": [ContactRoleCode.PUBLISHER.value],
            }
        expected = DataQuality(
            lineage=Lineage(statement="x"),
            domain_consistency=DomainConsistencies(
                [
                    DomainConsistency(
                        specification=Citation(title="x", dates=Dates(creation=Date(date=expected_date))),
                        explanation="x",
                        result=True,
                    )
                ]
            ),
        )
        if has_spec_contact:
            expected.domain_consistency[0].specification.contacts = Contacts(
                [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.PUBLISHER})]
            )

        converter = cattrs.Converter()
        converter.register_structure_hook(DataQuality, lambda d, t: DataQuality.structure(d))
        result = converter.structure(value, DataQuality)

        assert result == expected

    @pytest.mark.parametrize("has_spec_contact", [False, True])
    def test_unstructure_cattrs(self, has_spec_contact: bool):
        """Can use Cattrs to convert a DataQuality instance into plain types."""
        expected_date = date(2014, 6, 30)
        value = DataQuality(
            lineage=Lineage(statement="x"),
            domain_consistency=DomainConsistencies(
                [
                    DomainConsistency(
                        specification=Citation(title="x", dates=Dates(creation=Date(date=expected_date))),
                        explanation="x",
                        result=True,
                    )
                ]
            ),
        )
        if has_spec_contact:
            value.domain_consistency[0].specification.contacts = Contacts(
                [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.PUBLISHER})]
            )
        expected: dict = {
            "lineage": {"statement": "x"},
            "domain_consistency": [
                {
                    "specification": {"title": {"value": "x"}, "dates": {"creation": expected_date.isoformat()}},
                    "explanation": "x",
                    "result": True,
                }
            ],
        }
        if has_spec_contact:
            expected["domain_consistency"][0]["specification"]["contact"] = {
                "organisation": {"name": "x"},
                "role": [ContactRoleCode.PUBLISHER.value],
            }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected
