from datetime import UTC, date, datetime

import cattrs
import pytest

from lantern.models.record.elements.common import Date, Dates, Identifier, clean_dict, clean_list
from lantern.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    BoundingBox,
    Constraint,
    Constraints,
    Extent,
    ExtentGeographic,
    Extents,
    ExtentTemporal,
    GraphicOverview,
    GraphicOverviews,
    Identification,
    Maintenance,
    TemporalPeriod,
)
from lantern.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)

MIN_IDENTIFICATION = {
    "title": "x",
    "abstract": "x",
    "dates": Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
}


class TestAggregation:
    """Test Aggregation element."""

    @pytest.mark.parametrize(
        "values",
        [
            {
                "identifier": Identifier(identifier="x", href="x", namespace="x"),
                "association_type": AggregationAssociationCode.CROSS_REFERENCE,
            },
            {
                "identifier": Identifier(identifier="x", href="x", namespace="x"),
                "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                "initiative_type": AggregationInitiativeCode.CAMPAIGN,
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create an Aggregation element from directly assigned properties."""
        aggregation = Aggregation(**values)

        assert aggregation.identifier == values["identifier"]
        assert aggregation.association_type == values["association_type"]

        if "initiative_type" in values:
            assert aggregation.initiative_type == values["initiative_type"]
        else:
            assert aggregation.initiative_type is None

    @pytest.mark.parametrize(
        ("values", "conditions", "expected"),
        [
            # namespace
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"namespace": "x"},
                True,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"namespace": "y"},
                False,
            ),
            # association_type
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"associations": [AggregationAssociationCode.CROSS_REFERENCE]},
                True,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"associations": [AggregationAssociationCode.SERIES]},
                False,
            ),
            # initiative_type
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {"initiatives": [AggregationInitiativeCode.CAMPAIGN]},
                True,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {"initiatives": [AggregationInitiativeCode.TASK]},
                False,
            ),
            # namespace + association
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"namespace": "x", "associations": [AggregationAssociationCode.CROSS_REFERENCE]},
                True,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"namespace": "y", "associations": [AggregationAssociationCode.CROSS_REFERENCE]},
                False,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                },
                {"namespace": "x", "associations": [AggregationAssociationCode.SERIES]},
                False,
            ),
            # namespace + initiative
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {"namespace": "x", "initiatives": [AggregationInitiativeCode.CAMPAIGN]},
                True,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {"namespace": "y", "initiatives": [AggregationInitiativeCode.CAMPAIGN]},
                False,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {"namespace": "y", "initiatives": [AggregationInitiativeCode.TASK]},
                False,
            ),
            # association + initiative
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {
                    "associations": [AggregationAssociationCode.CROSS_REFERENCE],
                    "initiatives": [AggregationInitiativeCode.CAMPAIGN],
                },
                True,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {
                    "associations": [AggregationAssociationCode.SERIES],
                    "initiatives": [AggregationInitiativeCode.CAMPAIGN],
                },
                False,
            ),
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {
                    "associations": [AggregationAssociationCode.CROSS_REFERENCE],
                    "initiatives": [AggregationInitiativeCode.TASK],
                },
                False,
            ),
            # namespace + association + initiative
            (
                {
                    "identifier": Identifier(identifier="x", href="x", namespace="x"),
                    "association_type": AggregationAssociationCode.CROSS_REFERENCE,
                    "initiative_type": AggregationInitiativeCode.CAMPAIGN,
                },
                {
                    "namespace": "x",
                    "associations": [AggregationAssociationCode.CROSS_REFERENCE],
                    "initiatives": [AggregationInitiativeCode.CAMPAIGN],
                },
                True,
            ),
        ],
    )
    def test_filter(self, values: dict, conditions: dict, expected: bool):
        """Can determine whether Aggregation matches filtering conditions."""
        aggregation = Aggregation(**values)
        result = aggregation.matches_filter(**conditions)
        assert result == expected


class TestAggregations:
    """Test Aggregations container."""

    def test_init(self):
        """Can create an Aggregations container from directly assigned properties."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.CROSS_REFERENCE,
        )

        result = Aggregations([expected])

        assert len(result) == 1
        assert result[0] == expected

    test_filter_a = Aggregation(
        identifier=Identifier(identifier="x", href="x", namespace="x"),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
    )
    test_filter_b = Aggregation(
        identifier=Identifier(identifier="x", href="x", namespace="x"),
        association_type=AggregationAssociationCode.SERIES,
    )
    test_filter_c = Aggregation(
        identifier=Identifier(identifier="x", href="x", namespace="x"),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
        initiative_type=AggregationInitiativeCode.CAMPAIGN,
    )
    test_filter_d = Aggregation(
        identifier=Identifier(identifier="x", href="x", namespace="y"),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
        initiative_type=AggregationInitiativeCode.CAMPAIGN,
    )

    @pytest.mark.parametrize(
        ("conditions", "expected"),
        [
            (
                {"namespace": "x", "associations": AggregationAssociationCode.CROSS_REFERENCE},
                [test_filter_a, test_filter_c],
            ),
            (
                {"namespace": "x", "initiatives": AggregationInitiativeCode.CAMPAIGN},
                [test_filter_c],
            ),
            (
                {"initiatives": AggregationInitiativeCode.CAMPAIGN},
                [test_filter_c, test_filter_d],
            ),
            (
                {"associations": [AggregationAssociationCode.CROSS_REFERENCE, AggregationAssociationCode.SERIES]},
                [test_filter_a, test_filter_b, test_filter_c, test_filter_d],
            ),
        ],
    )
    def test_filter(self, conditions: dict, expected: list[Aggregation]):
        """Can filter aggregations by namespace and/or association type and/or initiative type."""
        aggregations = Aggregations([self.test_filter_a, self.test_filter_b, self.test_filter_c, self.test_filter_d])

        result = aggregations.filter(**conditions)

        assert len(result) == len(expected)
        assert result == expected

    def test_structure(self):
        """Can create an Aggregations element by converting a list of plain types."""
        expected = Aggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace="x"),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                )
            ]
        )
        result = Aggregations.structure(
            [{"identifier": {"identifier": "x", "href": "x", "namespace": "x"}, "association_type": "crossReference"}]
        )
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Aggregations instance from plain types."""
        value = [
            {"identifier": {"identifier": "x", "href": "x", "namespace": "x"}, "association_type": "crossReference"}
        ]
        expected = Aggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace="x"),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                )
            ]
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Aggregations, lambda d, t: Aggregations.structure(d))
        result = converter.structure(value, Aggregations)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert an Aggregations instance into plain types."""
        value = Aggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace="x"),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                )
            ]
        )
        expected = [
            {"identifier": {"identifier": "x", "href": "x", "namespace": "x"}, "association_type": "crossReference"}
        ]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Aggregations, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


class TestBoundingBox:
    """Test BoundingBox element."""

    def test_init(self):
        """Can create a BoundingBox element from directly assigned properties."""
        values = {
            "west_longitude": 1.0,
            "east_longitude": 2.0,
            "south_latitude": 3.0,
            "north_latitude": 4.0,
        }
        bbox = BoundingBox(**values)

        assert bbox.west_longitude == values["west_longitude"]
        assert bbox.east_longitude == values["east_longitude"]
        assert bbox.south_latitude == values["south_latitude"]
        assert bbox.north_latitude == values["north_latitude"]


class TestConstraint:
    """Test Constraint element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"type": ConstraintTypeCode.ACCESS},
            {
                "type": ConstraintTypeCode.USAGE,
                "restriction_code": ConstraintRestrictionCode.UNRESTRICTED,
                "statement": "x",
                "href": "x",
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a Constraint element from directly assigned properties."""
        constraint = Constraint(**values)

        assert constraint.type == values["type"]

        if "restriction_code" in values:
            assert constraint.restriction_code == values["restriction_code"]
        else:
            assert constraint.restriction_code is None

        if "statement" in values:
            assert constraint.statement == values["statement"]
        else:
            assert constraint.statement is None

        if "href" in values:
            assert constraint.href == values["href"]
        else:
            assert constraint.href is None

    @pytest.mark.parametrize(
        ("values", "conditions", "expected"),
        [
            # href
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"href": "x"},
                True,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"href": "y"},
                False,
            ),
            # type
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"types": [ConstraintTypeCode.USAGE]},
                True,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"types": [ConstraintTypeCode.ACCESS]},
                False,
            ),
            # restriction
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {"restrictions": [ConstraintRestrictionCode.RESTRICTED]},
                True,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {"restrictions": [ConstraintRestrictionCode.UNRESTRICTED]},
                False,
            ),
            # href + type
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"href": "x", "types": [ConstraintTypeCode.USAGE]},
                True,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"href": "y", "types": [ConstraintTypeCode.USAGE]},
                False,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                },
                {"href": "x", "types": [ConstraintTypeCode.ACCESS]},
                False,
            ),
            # href + restriction
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {"href": "x", "restrictions": [ConstraintRestrictionCode.RESTRICTED]},
                True,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {"href": "y", "restrictions": [ConstraintRestrictionCode.RESTRICTED]},
                False,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {"href": "x", "restrictions": [ConstraintRestrictionCode.UNRESTRICTED]},
                False,
            ),
            # type + restriction
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {
                    "types": [ConstraintTypeCode.USAGE],
                    "restrictions": [ConstraintRestrictionCode.RESTRICTED],
                },
                True,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {
                    "types": [ConstraintTypeCode.ACCESS],
                    "restrictions": [ConstraintRestrictionCode.RESTRICTED],
                },
                False,
            ),
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {
                    "types": [ConstraintTypeCode.USAGE],
                    "restrictions": [ConstraintRestrictionCode.UNRESTRICTED],
                },
                False,
            ),
            # href + type + restriction
            (
                {
                    "href": "x",
                    "type": ConstraintTypeCode.USAGE,
                    "restriction_code": ConstraintRestrictionCode.RESTRICTED,
                },
                {
                    "href": "x",
                    "types": [ConstraintTypeCode.USAGE],
                    "restrictions": [ConstraintRestrictionCode.RESTRICTED],
                },
                True,
            ),
        ],
    )
    def test_filter(self, values: dict, conditions: dict, expected: bool):
        """Can determine whether Constraint matches filtering conditions."""
        constraint = Constraint(**values)
        result = constraint.matches_filter(**conditions)
        assert result == expected


class TestConstraints:
    """Test Constraints container."""

    def test_init(self):
        """Can create a Constraints container from directly assigned properties."""
        expected = Constraint(type=ConstraintTypeCode.ACCESS)

        result = Constraints([expected])

        assert len(result) == 1
        assert result[0] == expected

    test_filter_a = Constraint(
        href="x",
        type=ConstraintTypeCode.USAGE,
    )
    test_filter_b = Constraint(
        href="x",
        type=ConstraintTypeCode.ACCESS,
    )
    test_filter_c = Constraint(
        href="x",
        type=ConstraintTypeCode.USAGE,
        restriction_code=ConstraintRestrictionCode.RESTRICTED,
    )
    test_filter_d = Constraint(
        href="y",
        type=ConstraintTypeCode.USAGE,
        restriction_code=ConstraintRestrictionCode.RESTRICTED,
    )

    @pytest.mark.parametrize(
        ("conditions", "expected"),
        [
            (
                {"href": "x", "types": ConstraintTypeCode.USAGE},
                [test_filter_a, test_filter_c],
            ),
            (
                {"href": "x", "restrictions": ConstraintRestrictionCode.RESTRICTED},
                [test_filter_c],
            ),
            (
                {"restrictions": ConstraintRestrictionCode.RESTRICTED},
                [test_filter_c, test_filter_d],
            ),
            (
                {"types": [ConstraintTypeCode.USAGE, ConstraintTypeCode.ACCESS]},
                [test_filter_a, test_filter_b, test_filter_c, test_filter_d],
            ),
        ],
    )
    def test_filter(self, conditions: dict, expected: list[Aggregation]):
        """Can filter constraints by href and/or type and/or restriction code."""
        constraints = Constraints([self.test_filter_a, self.test_filter_b, self.test_filter_c, self.test_filter_d])

        result = constraints.filter(**conditions)

        assert len(result) == len(expected)
        assert result == expected

    def test_structure(self):
        """Can create a Constraints element by converting a list of plain types."""
        expected = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    statement="x",
                    href="x",
                )
            ]
        )

        result = Constraints.structure(
            [{"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}]
        )
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create a Constraints instance from plain types."""
        value = [{"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}]
        expected = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    statement="x",
                    href="x",
                )
            ]
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Constraints, lambda d, t: Constraints.structure(d))
        result = converter.structure(value, Constraints)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a Constraints instance into plain types."""
        value = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    statement="x",
                    href="x",
                )
            ]
        )
        expected = [{"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Constraints, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


class TestExtentGeographic:
    """Test ExtentGeographic element."""

    def test_init(self):
        """Can create an ExtentGeographic element from directly assigned properties."""
        values = {
            "bounding_box": BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)
        }
        geographic = ExtentGeographic(**values)

        assert geographic.bounding_box == values["bounding_box"]


class TestExtentTemporal:
    """Test ExtentTemporal element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"period": TemporalPeriod(start=Date(date=date(2014, 6, 30)), end=Date(date=date(2014, 6, 30)))},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create an ExtentGeographic element from directly assigned properties."""
        temporal = ExtentTemporal(**values)

        if "period" in values:
            assert temporal.period == values["period"]
        else:
            assert temporal.period == TemporalPeriod()


class TestExtent:
    """Test Extent element."""

    @pytest.mark.parametrize(
        "values",
        [
            {
                "identifier": "x",
                "geographic": ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                    )
                ),
            },
            {
                "identifier": "x",
                "geographic": ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                    )
                ),
                "temporal": ExtentTemporal(
                    period=TemporalPeriod(start=Date(date=date(2014, 6, 30)), end=Date(date=date(2014, 6, 30)))
                ),
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create an Extent element from directly assigned properties."""
        extent = Extent(**values)

        assert extent.identifier == values["identifier"]
        assert extent.geographic == values["geographic"]

        if "temporal" in values:
            assert extent.temporal == values["temporal"]
        else:
            assert extent.temporal is None


class TestExtents:
    """Test Extents container."""

    def test_init(self):
        """Can create an Extents container from directly assigned properties."""
        expected = Extent(
            identifier="x",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)
            ),
        )

        extents = Extents([expected])

        assert len(extents) == 1
        assert extents[0] == expected

    def test_filter_identifier(self):
        """Can filter extents by an identifier."""
        extent = Extent(
            identifier="x",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)
            ),
        )
        other = Extent(
            identifier="y",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)
            ),
        )
        extents = Extents([extent, other])
        expected = Extents([extent])

        result = extents.filter(extent.identifier)
        assert result == expected

    def test_structure(self):
        """Can create an Extents container by converting a list of plain types."""
        expected_date = date(2014, 6, 30)
        expected = Extents(
            [
                Extent(
                    identifier="x",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                    temporal=ExtentTemporal(
                        period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                    ),
                )
            ]
        )
        result = Extents.structure(
            [
                {
                    "identifier": "x",
                    "geographic": {
                        "bounding_box": {
                            "west_longitude": 1.0,
                            "east_longitude": 1.0,
                            "south_latitude": 1.0,
                            "north_latitude": 1.0,
                        }
                    },
                    "temporal": {
                        "period": {
                            "start": expected_date.isoformat(),
                            "end": expected_date.isoformat(),
                        }
                    },
                }
            ]
        )
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Extents instance from plain types."""
        expected_date = date(2014, 6, 30)
        value = [
            {
                "identifier": "x",
                "geographic": {
                    "bounding_box": {
                        "west_longitude": 1.0,
                        "east_longitude": 1.0,
                        "south_latitude": 1.0,
                        "north_latitude": 1.0,
                    }
                },
                "temporal": {
                    "period": {
                        "start": expected_date.isoformat(),
                        "end": expected_date.isoformat(),
                    }
                },
            }
        ]
        expected = Extents(
            [
                Extent(
                    identifier="x",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                    temporal=ExtentTemporal(
                        period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                    ),
                )
            ]
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Extents, lambda d, t: Extents.structure(d))
        result = converter.structure(value, Extents)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert an Extents instance into plain types."""
        expected_date = date(2014, 6, 30)
        value = Extents(
            [
                Extent(
                    identifier="x",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                    temporal=ExtentTemporal(
                        period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                    ),
                )
            ]
        )
        expected = [
            {
                "identifier": "x",
                "geographic": {
                    "bounding_box": {
                        "west_longitude": 1.0,
                        "east_longitude": 1.0,
                        "south_latitude": 1.0,
                        "north_latitude": 1.0,
                    }
                },
                "temporal": {
                    "period": {
                        "start": expected_date.isoformat(),
                        "end": expected_date.isoformat(),
                    }
                },
            }
        ]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Extents, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


class TestGraphicOverview:
    """Test GraphicOverview element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"identifier": "x", "href": "x", "mime_type": "x"},
            {"identifier": "x", "href": "x", "mime_type": "x", "description": "x"},
        ],
    )
    def test_init(self, values: dict):
        """Can create a GraphicOverview element from directly assigned properties."""
        expected = "x"
        graphic_overview = GraphicOverview(**values)

        assert graphic_overview.identifier == expected
        assert graphic_overview.href == expected
        assert graphic_overview.mime_type == expected
        if "description" in values:
            assert graphic_overview.description == expected


class TestGraphicOverviews:
    """Test GraphicOverviews container."""

    def test_init(self):
        """Can create a GraphicOverviews container from directly assigned properties."""
        expected = GraphicOverview(identifier="x", href="x", mime_type="x")

        extents = GraphicOverviews([expected])

        assert len(extents) == 1
        assert extents[0] == expected

    def test_filter_identifier(self):
        """Can filter overviews by an identifier."""
        overview = GraphicOverview(identifier="x", href="x", mime_type="x")
        other = GraphicOverview(identifier="y", href="x", mime_type="x")
        overviews = GraphicOverviews([overview, other])
        expected = GraphicOverviews([overview])

        result = overviews.filter(overview.identifier)
        assert result == expected

    def test_structure(self):
        """Can create a GraphicOverviews container by converting a list of plain types."""
        expected = GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")])
        result = GraphicOverviews.structure([{"identifier": "x", "href": "x", "mime_type": "x"}])
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create a GraphicOverviews instance from plain types."""
        value = [{"identifier": "x", "href": "x", "mime_type": "x"}]
        expected = GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")])

        converter = cattrs.Converter()
        converter.register_structure_hook(GraphicOverviews, lambda d, t: GraphicOverviews.structure(d))
        result = converter.structure(value, GraphicOverviews)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a GraphicOverviews instance into plain types."""
        value = GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")])
        expected = [{"identifier": "x", "href": "x", "mime_type": "x"}]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(GraphicOverviews, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


class TestMaintenance:
    """Test Maintenance element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"maintenance_frequency": MaintenanceFrequencyCode.AS_NEEDED, "progress": ProgressCode.ON_GOING},
            {"maintenance_frequency": MaintenanceFrequencyCode.AS_NEEDED},
            {"progress": ProgressCode.ON_GOING},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Maintenance element from directly assigned properties."""
        maintenance = Maintenance(**values)

        if "maintenance_frequency" in values:
            assert maintenance.maintenance_frequency == values["maintenance_frequency"]
        else:
            assert maintenance.maintenance_frequency is None

        if "progress" in values:
            assert maintenance.progress == values["progress"]
        else:
            assert maintenance.progress is None


class TestTemporalPeriod:
    """Test TemporalPeriod element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"start": Date(date=date(2014, 6, 30)), "end": Date(date=date(2014, 6, 30))},
            {"start": Date(date=date(2014, 6, 30))},
            {"end": Date(date=date(2014, 6, 30))},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create a TemporalPeriod element from directly assigned properties."""
        period = TemporalPeriod(**values)

        if "start" in values:
            assert period.start == values["start"]
        else:
            assert period.start is None

        if "end" in values:
            assert period.end == values["end"]
        else:
            assert period.end is None


class TestIdentification:
    """Test Identification element."""

    @pytest.mark.parametrize(
        "values",
        [
            {**MIN_IDENTIFICATION},
            {**MIN_IDENTIFICATION, "purpose": "x"},
            {
                **MIN_IDENTIFICATION,
                "graphic_overviews": [GraphicOverview(identifier="x", href="x", mime_type="x")],
            },
            {
                **MIN_IDENTIFICATION,
                "constraints": [Constraint(type=ConstraintTypeCode.ACCESS)],
            },
            {
                **MIN_IDENTIFICATION,
                "aggregations": [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    )
                ],
            },
            {
                **MIN_IDENTIFICATION,
                "maintenance": Maintenance(maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED),
            },
            {
                **MIN_IDENTIFICATION,
                "extents": [
                    Extent(
                        identifier="x",
                        geographic=ExtentGeographic(
                            bounding_box=BoundingBox(
                                west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                            )
                        ),
                    )
                ],
            },
            {**MIN_IDENTIFICATION, "supplemental_information": "x"},
            {**MIN_IDENTIFICATION, "spatial_resolution": 1},
        ],
    )
    def test_init(self, values: dict):
        """
        Can create an Identification element from directly assigned properties.

        Properties from parent citation class are not re-tested here, except to verify inheritance.
        """
        expected_character = "utf8"
        expected_language = "eng"
        identification = Identification(**values)

        assert identification.title == values["title"]  # inheritance test
        assert identification.abstract == values["abstract"]
        assert identification.character_set == expected_character
        assert identification.language == expected_language

        if "purpose" in values:
            assert identification.purpose == values["purpose"]

        if (
            "graphic_overviews" in values
            and isinstance(values["graphic_overviews"], list)
            and len(values["graphic_overviews"]) > 0
        ):
            assert all(isinstance(graphic, GraphicOverview) for graphic in identification.graphic_overviews)
        else:
            assert identification.graphic_overviews == []

        if "constraints" in values and isinstance(values["constraints"], list) and len(values["constraints"]) > 0:
            assert all(isinstance(constraint, Constraint) for constraint in identification.constraints)
        else:
            assert identification.constraints == []

        if "aggregations" in values and isinstance(values["aggregations"], list) and len(values["aggregations"]) > 0:
            assert all(isinstance(aggregation, Aggregation) for aggregation in identification.aggregations)
        else:
            assert identification.aggregations == []

        if "maintenance" in values:
            assert identification.maintenance == values["maintenance"]
        else:
            assert identification.maintenance == Maintenance()

        if "extents" in values and isinstance(values["extents"], list) and len(values["extents"]) > 0:
            assert all(isinstance(extent, Extent) for extent in identification.extents)
        else:
            assert identification.extents == []

        if "supplemental_information" in values:
            assert identification.supplemental_information == values["supplemental_information"]
        else:
            assert identification.supplemental_information is None

        if "spatial_resolution" in values:
            assert identification.spatial_resolution == values["spatial_resolution"]
        else:
            assert identification.spatial_resolution is None

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Identification instance from plain types."""
        expected_date = date(2014, 6, 30)
        expected_enums = {
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        value = {
            "title": {"value": "x"},
            "dates": {"creation": expected_date.isoformat()},
            "abstract": "x",
            "constraints": [
                {
                    "type": expected_enums["constraint_type"].value,
                    "restriction_code": expected_enums["constraint_code"].value,
                }
            ],
            "extents": [
                {
                    "identifier": "x",
                    "geographic": {
                        "bounding_box": {
                            "west_longitude": 1.0,
                            "east_longitude": 1.0,
                            "south_latitude": 1.0,
                            "north_latitude": 1.0,
                        }
                    },
                    "temporal": {
                        "period": {
                            "start": expected_date.isoformat(),
                            "end": expected_date.isoformat(),
                        }
                    },
                }
            ],
        }
        expected = Identification(
            title="x",
            dates=Dates(creation=Date(date=expected_date)),
            abstract="x",
            constraints=Constraints(
                [
                    Constraint(
                        type=expected_enums["constraint_type"], restriction_code=expected_enums["constraint_code"]
                    ),
                ]
            ),
            extents=Extents(
                [
                    Extent(
                        identifier="x",
                        geographic=ExtentGeographic(
                            bounding_box=BoundingBox(
                                west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                            )
                        ),
                        temporal=ExtentTemporal(
                            period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                        ),
                    )
                ]
            ),
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Identification, lambda d, t: Identification.structure(d))
        result = converter.structure(value, Identification)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert an Identification instance into plain types."""
        expected_date = date(2014, 6, 30)
        expected_enums = {
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        value = Identification(
            title="x",
            dates=Dates(creation=Date(date=expected_date)),
            abstract="x",
            constraints=Constraints(
                [
                    Constraint(
                        type=expected_enums["constraint_type"], restriction_code=expected_enums["constraint_code"]
                    ),
                ]
            ),
            extents=Extents(
                [
                    Extent(
                        identifier="x",
                        geographic=ExtentGeographic(
                            bounding_box=BoundingBox(
                                west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                            )
                        ),
                        temporal=ExtentTemporal(
                            period=TemporalPeriod(start=Date(date=expected_date), end=Date(date=expected_date))
                        ),
                    )
                ]
            ),
        )
        expected = {
            "title": {"value": "x"},
            "dates": {"creation": expected_date.isoformat()},
            "abstract": "x",
            "constraints": [
                {
                    "type": expected_enums["constraint_type"].value,
                    "restriction_code": expected_enums["constraint_code"].value,
                }
            ],
            "character_set": "utf8",
            "language": "eng",
            "extents": [
                {
                    "identifier": "x",
                    "geographic": {
                        "bounding_box": {
                            "west_longitude": 1.0,
                            "east_longitude": 1.0,
                            "south_latitude": 1.0,
                            "north_latitude": 1.0,
                        }
                    },
                    "temporal": {
                        "period": {
                            "start": expected_date.isoformat(),
                            "end": expected_date.isoformat(),
                        }
                    },
                }
            ],
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Identification, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected
