from dataclasses import dataclass, field
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record.elements.common import (
    Citation,
    Date,
    Dates,
    Identifier,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)

TGraphicOverviews = TypeVar("TGraphicOverviews", bound="GraphicOverviews")
TIdentification = TypeVar("TIdentification", bound="Identification")
TAggregations = TypeVar("TAggregations", bound="Aggregations")
TConstraints = TypeVar("TConstraints", bound="Constraints")
TExtents = TypeVar("TExtents", bound="Extents")
TPeriod = TypeVar("TPeriod", bound="TemporalPeriod")


@dataclass(kw_only=True)
class Aggregation:
    """
    Aggregation.

    Schema definition: aggregation [1]
    ISO element: gmd:MD_AggregateInformation [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L74
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_AggregateInformation.html
    """

    identifier: Identifier
    association_type: AggregationAssociationCode
    initiative_type: AggregationInitiativeCode | None = None

    def matches_filter(
        self,
        namespace: str | None = None,
        identifiers: list[str] | None = None,
        associations: list[AggregationAssociationCode] | None = None,
        initiatives: list[AggregationInitiativeCode] | None = None,
    ) -> bool:
        """
        Check if aggregation matches filter criteria.

        Intended for use in filtering functions.
        """
        if namespace is not None and self.identifier.namespace != namespace:
            return False
        if identifiers is not None and self.identifier.identifier not in identifiers:
            return False
        if associations is not None and self.association_type not in associations:
            return False
        return not (
            initiatives is not None and (self.initiative_type is None or self.initiative_type not in initiatives)
        )


class Aggregations(list[Aggregation]):
    """
    Aggregations.

    Wrapper around a list of Aggregation items with additional methods for filtering/selecting items.

    Schema definition: aggregations [1]
    ISO element: gmd:CI_ResponsibleParty [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L65
    [2] See 'used in' section of: https://www.datypic.com/sc/niem21/e-gmd_aggregationInfo-1.html
    """

    @classmethod
    def structure(cls: type[TAggregations], value: list[dict]) -> "Aggregations":
        """
        Parse aggregations from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Aggregations, lambda d, t: Aggregations.structure(d))`

        Structures input items into a list of Aggregation items via cattrs as a new instance of this class.

        Example input: [
            {"identifier": {"identifier": "x", "href": "x", "namespace": "x"}, "association_type": "crossReference"}
        ]
        Example output: Aggregations([
            Aggregation(identifier=Identifier(identifier="x", href="x", namespace="x"), "association_type": AggregationAssociationCode.CROSS_REFERENCE)
        ])
        """
        converter = cattrs.Converter()
        return cls([converter.structure(aggregation, Aggregation) for aggregation in value])

    def unstructure(self) -> list[dict]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Aggregations, lambda d: d.unstructure())`

        Example input: Aggregations([
            Aggregation(identifier=Identifier(identifier="x", href="x", namespace="x"), "association_type": AggregationAssociationCode.CROSS_REFERENCE)
        ])
        Example output: [
            {"identifier": {"identifier": "x", "href": "x", "namespace": "x"}, "association_type": "crossReference"}
        ]
        """
        # noinspection PyUnresolvedReferences
        converter = cattrs.Converter()
        return [converter.unstructure(aggregation) for aggregation in self]

    def identifiers(self, exclude: list[str] | None = None) -> list[str]:
        """
        Get identifiers from a set of aggregations, optionally filtered to exclude a list of values.

        Exclude list can be used to filter out a Record's own identifier for example.
        """
        if exclude is None:
            exclude = []

        return list(
            {
                aggregation.identifier.identifier
                for aggregation in self
                if aggregation.identifier.identifier not in exclude
            }
        )

    def filter(
        self,
        namespace: str | None = None,
        identifiers: str | list[str] | None = None,
        associations: AggregationAssociationCode | list[AggregationAssociationCode] | None = None,
        initiatives: AggregationInitiativeCode | list[AggregationInitiativeCode] | None = None,
    ) -> "Aggregations":
        """
        Filter aggregations by namespace, identifier and/or association(s) and/or initiative(s).

        Conditions use logical AND, i.e. aggregations must match a namespace and association(s) if specified.
        Associations/initiatives use logical OR for multiple values.
        """
        identifiers = [identifiers] if isinstance(identifiers, str) else identifiers
        associations = [associations] if isinstance(associations, AggregationAssociationCode) else associations
        initiatives = [initiatives] if isinstance(initiatives, AggregationInitiativeCode) else initiatives
        return Aggregations(
            [
                aggregation
                for aggregation in self
                if aggregation.matches_filter(
                    namespace=namespace, identifiers=identifiers, associations=associations, initiatives=initiatives
                )
            ]
        )


@dataclass(kw_only=True)
class BoundingBox:
    """
    Geographic Extent Bounding Box.

    Schema definition: bounding_box [1]
    ISO element: gmd:EX_GeographicBoundingBox [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L749
    [2] https://www.datypic.com/sc/niem21/e-gmd_EX_GeographicBoundingBox.html
    """

    west_longitude: float
    east_longitude: float
    south_latitude: float
    north_latitude: float


@dataclass(kw_only=True)
class Constraint:
    """
    Constraint.

    Schema definition: constraint [1]
    ISO element: gmd:MD_LegalConstraints [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L145
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_LegalConstraints.html
    """

    type: ConstraintTypeCode
    restriction_code: ConstraintRestrictionCode | None = None
    statement: str | None = None
    href: str | None = None

    def matches_filter(
        self,
        href: str | None = None,
        types: list[ConstraintTypeCode] | None = None,
        restrictions: list[ConstraintRestrictionCode] | None = None,
    ) -> bool:
        """
        Check if constraint matches filter criteria.

        Intended for use in filtering functions.
        """
        if href is not None and self.href != href:
            return False
        if types is not None and self.type not in types:
            return False
        return not (
            restrictions is not None and (self.restriction_code is None or self.restriction_code not in restrictions)
        )


class Constraints(list[Constraint]):
    """
    Constraints.

    Wrapper around a list of Constraint items with additional methods for filtering/selecting items.

    Schema definition: constraints [1]
    ISO element: gmd:MD_LegalConstraints [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L252
    [2] See 'used in' section of: https://www.datypic.com/sc/niem21/e-gmd_MD_LegalConstraints.html
    """

    @classmethod
    def structure(cls: type[TConstraints], value: list[dict]) -> "Constraints":
        """
        Parse constraints from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Constraints, lambda d, t: Constraints.structure(d))`

        Structures input items into a list of Constraint items via cattrs as a new instance of this class.

        Example input: [{"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}]
        Example output: Constraints([Constraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, statement="x", href="x")])
        """
        converter = cattrs.Converter()
        return cls([converter.structure(constraint, Constraint) for constraint in value])

    def unstructure(self) -> list[dict]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Constraints, lambda d: d.unstructure())`

        Example input: Constraints([Constraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, statement="x", href="x")])
        Example output: [{"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}]

        """
        # noinspection PyUnresolvedReferences
        converter = cattrs.Converter()
        return [converter.unstructure(constraint) for constraint in self]

    def filter(
        self,
        href: str | None = None,
        types: ConstraintTypeCode | list[ConstraintTypeCode] | None = None,
        restrictions: ConstraintRestrictionCode | list[ConstraintRestrictionCode] | None = None,
    ) -> "Constraints":
        """
        Filter constraints by href and/or type(s) and/or restriction(s).

        Conditions use logical AND, i.e. constraints must match a href and type(s) if specified.
        Types/restrictions use logical OR for multiple values.
        """
        types = [types] if isinstance(types, ConstraintTypeCode) else types
        restrictions = [restrictions] if isinstance(restrictions, ConstraintRestrictionCode) else restrictions
        return Constraints([constraint for constraint in self if constraint.matches_filter(href, types, restrictions)])


@dataclass(kw_only=True)
class ExtentGeographic:
    """
    Geographic Extent.

    Schema definition: geographic_extent [1]
    ISO element: gmd:geographicElement [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L738
    [2] https://www.datypic.com/sc/niem21/e-gmd_geographicElement-1.html
    """

    bounding_box: BoundingBox


@dataclass(kw_only=True)
class TemporalPeriod:
    """
    Temporal Extent Period.

    Schema definition: period [1]
    ISO element: gml:TimePeriod [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1652
    [2] https://www.datypic.com/sc/niem21/e-gml32_TimePeriod.html
    """

    start: Date | None = None
    end: Date | None = None


@dataclass(kw_only=True)
class ExtentTemporal:
    """
    Temporal Extent.

    Schema definition: temporal_extent [1]
    ISO element: gmd:temporalElement [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1645
    [2] https://www.datypic.com/sc/niem21/e-gmd_temporalElement-1.html
    """

    period: TemporalPeriod | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.period is None:
            self.period = TemporalPeriod()


@dataclass(kw_only=True)
class Extent:
    """
    Extent.

    Schema definition: extent [1]
    ISO element: gmd:EX_Extent [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L579
    [2] https://www.datypic.com/sc/niem21/e-gmd_EX_Extent.html
    """

    identifier: str
    geographic: ExtentGeographic
    temporal: ExtentTemporal | None = None


class Extents(list[Extent]):
    """
    Extents.

    Wrapper around a list of Extent items with additional methods for filtering/selecting items.

    Schema definition: extents [1]
    ISO element: gmd:EX_Extent [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L608
    [2] See 'used in' section of: https://www.datypic.com/sc/niem21/e-gmd_extent-1.html
    """

    @classmethod
    def structure(cls: type[TExtents], value: list[dict]) -> "Extents":
        """
        Parse extents from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Extents, lambda d, t: Extents.structure(d))`

        Structures input items into a list of Extent items via cattrs as a new instance of this class.

        Example input: Extents([
            {"identifier": "x", "geographic": { "bounding_box": {"west_longitude": 1.0,"east_longitude": 1.0,"south_latitude": 1.0,"north_latitude": 1.0}}}
        ])
        Example output: [
            Extent(identifier="x", geographic=ExtentGeographic(bounding_box=BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)))
        ]
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Date, lambda d, t: Date.structure(d))
        converter.register_structure_hook(Dates, lambda d, t: Dates.structure(d))
        return cls([converter.structure(extent, Extent) for extent in value])

    def unstructure(self) -> list[dict]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Extents, lambda d: d.unstructure())`

        Example input: Extents([
            Extent(identifier="x", geographic=ExtentGeographic(bounding_box=BoundingBox(west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0)))
        ])
        Example output: [
            {"identifier": "x", "geographic": { "bounding_box": {"west_longitude": 1.0,"east_longitude": 1.0,"south_latitude": 1.0,"north_latitude": 1.0}}}
        ]
        """
        # noinspection PyUnresolvedReferences
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Date, lambda d: d.unstructure())
        converter.register_unstructure_hook(Dates, lambda d: d.unstructure())
        return [converter.unstructure(extent) for extent in self]

    def filter(self, identifier: str) -> "Extents":
        """
        Filter extents by identifier.

        Note: Extent identifiers are not guaranteed to be unique.
        """
        return Extents([extent for extent in self if extent.identifier == identifier])


@dataclass(kw_only=True)
class GraphicOverview:
    """
    Graphic Overview.

    Schema definition: graphic_overview [1]
    ISO element: gmd:MD_BrowseGraphic [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L690
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_BrowseGraphic.html
    """

    identifier: str
    href: str
    description: str | None = None
    mime_type: str


class GraphicOverviews(list[GraphicOverview]):
    """
    Graphic Overviews.

    Wrapper around a list of GraphicOverview items with additional methods for filtering/selecting items.

    Schema definition: graphic_overviews [1]
    ISO element: gmd:MD_BrowseGraphic [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L685
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_BrowseGraphic.html
    """

    @classmethod
    def structure(cls: type[TGraphicOverviews], value: list[dict]) -> "GraphicOverviews":
        """
        Parse graphic overviews from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(GraphicOverviews, lambda d, t: GraphicOverviews.structure(d))`

        Structures input items into a list of GraphicOverview items via cattrs as a new instance of this class.

        Example input: [{"identifier": "x", "href": "x", "mime_type": "x"}]
        Example output: GraphicOverviews([GraphicOverview(identifier="x", description="x", href="x", mime_type="x")])
        """
        converter = cattrs.Converter()
        return cls([converter.structure(overview, GraphicOverview) for overview in value])

    def unstructure(self) -> list[dict]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(GraphicOverviews, lambda d: d.unstructure())`

        Example input: GraphicOverviews([GraphicOverview(identifier="x", description="x", href="x", mime_type="x")])
        Example output: [{"identifier": "x", "href": "x", "mime_type": "x"}]

        """
        # noinspection PyUnresolvedReferences
        converter = cattrs.Converter()
        return [converter.unstructure(overview) for overview in self]

    def filter(self, identifier: str) -> "GraphicOverviews":
        """
        Filter graphic overviews by identifier.

        Note: GraphicOverview identifiers are not guaranteed to be unique.
        """
        return GraphicOverviews([overview for overview in self if overview.identifier == identifier])


@dataclass(kw_only=True)
class Maintenance:
    """
    Maintenance.

    Schema definition: maintenance [1]
    ISO element: gmd:MD_MaintenanceInformation [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1116
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_MaintenanceInformation.html
    """

    maintenance_frequency: MaintenanceFrequencyCode | None = None
    progress: ProgressCode | None = None


@dataclass(kw_only=True)
class Identification(Citation):
    """
    Identification.

    Wrapper around citation.

    Schema definition: identification [1]
    ISO element: gmd:MD_DataIdentification [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L861
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_DataIdentification.html
    """

    abstract: str
    purpose: str | None = None
    maintenance: Maintenance = field(default_factory=Maintenance)
    graphic_overviews: GraphicOverviews = field(default_factory=GraphicOverviews)
    constraints: Constraints = field(default_factory=Constraints)
    aggregations: Aggregations = field(default_factory=Aggregations)
    character_set: str = "utf8"
    language: str = "eng"
    extents: Extents = field(default_factory=Extents)
    spatial_resolution: int | None = None
    supplemental_information: str | None = None

    @staticmethod
    def _reorder_elements(value: dict) -> dict:
        """
        Reorder keys in unstructured dict to follow conventional element order.

        As this class extends Citation, the order of elements in an unstructured dict doesn't follow the JSON schema.
        This doesn't affect validation but does make it harder to compare against records made prior to this class.
        """
        order = [
            "title",
            "abstract",
            "purpose",
            # credit (not yet implemented)
            # status (not yet implemented)
            "dates",
            "edition",
            "series",
            "other_citation_details",
            "identifiers",
            "contacts",
            "maintenance",
            "graphic_overviews",
            # resource_formats (not yet implemented)
            # keywords (not yet implemented)
            "constraints",
            "aggregations",
            "supplemental_information",
            # spatial representation type (not yet implemented)
            "spatial_resolution",
            "character_set",
            "language",
            # topics (not yet implemented)
            "extents",
        ]

        # redefine value based on order for keys defined in value
        return {key: value[key] for key in order if key in value}

    @classmethod
    def structure(cls: type[TIdentification], value: dict) -> "Identification":
        """
        Parse Identification class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Identification, lambda d, t: Identification.structure(d))`

        Steps:

        1. Unwrap title (i.e. `{'title': {'value': 'x'}, 'abstract': 'x'}` -> `{'title': 'x', 'abstract': 'x'}`)
        2. Convert the input dict to a new instance of this class via cattrs
        """
        converter = Citation._converter()
        converter.register_structure_hook(Aggregations, lambda d, t: Aggregations.structure(d))
        converter.register_structure_hook(Constraints, lambda d, t: Constraints.structure(d))
        converter.register_structure_hook(Extents, lambda d, t: Extents.structure(d))
        converter.register_structure_hook(GraphicOverviews, lambda d, t: GraphicOverviews.structure(d))

        title = value.pop("title")["value"]
        value["title"] = title
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert Identification class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Identification, lambda d: d.unstructure())`

        Steps:

        1. Convert the class instance into plain types via cattrs
        2. Wrap title (i.e. `{'title': 'x', 'abstract': 'x'}` -> {'title': {'value': 'x'}, 'abstract': 'x'})
        """
        converter = super()._converter()
        converter.register_unstructure_hook(Aggregations, lambda d: d.unstructure())
        converter.register_unstructure_hook(Constraints, lambda d: d.unstructure())
        converter.register_unstructure_hook(Extents, lambda d: d.unstructure())
        converter.register_unstructure_hook(GraphicOverviews, lambda d: d.unstructure())

        value = converter.unstructure(self)

        title = value.pop("title")
        value["title"] = {"value": title}

        return self._reorder_elements(value)
