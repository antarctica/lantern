from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.elements.common import Date, clean_dict
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregations,
    Constraints,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode

TRecordSummary = TypeVar("TRecordSummary", bound="RecordSummary")


@dataclass(kw_only=True)
class RecordSummary:
    """
    Summary of a resource within the BAS Data Catalogue / Metadata ecosystem.

    RecordSummaries are a low-level view of key aspects of a resource, using the ISO 19115 information model. They are
    intended to be used where full records are unnecessary or would be impractical - such as describing/listing large
    numbers of resources, or for resources related to a selected resource.

    RecordSummaries can be created independently but are intended to be derived from a Record instance using `loads()`.
    This class does not support loading/dumping record configurations encoded in JSON or XML.
    """

    file_identifier: str | None = None
    hierarchy_level: HierarchyLevelCode
    date_stamp: date
    title: str
    purpose: str | None = None
    edition: str | None = None
    creation: Date
    revision: Date | None = None
    publication: Date | None = None
    graphic_overviews: GraphicOverviews | None = None
    constraints: Constraints | None = None
    aggregations: Aggregations | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.graphic_overviews is None:
            self.graphic_overviews = GraphicOverviews()
        if self.constraints is None:
            self.constraints = Constraints()
        if self.aggregations is None:
            self.aggregations = Aggregations()

    @staticmethod
    def _converter_up() -> cattrs.Converter:
        """
        Cattrs converter for structuring data.

        Standalone method for easier subclassing.
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(date, lambda d, t: date.fromisoformat(d))
        converter.register_structure_hook(Date, lambda d, t: Date.structure(d))
        converter.register_structure_hook(Aggregations, lambda d, t: Aggregations.structure(d))
        converter.register_structure_hook(Constraints, lambda d, t: Constraints.structure(d))
        converter.register_structure_hook(GraphicOverviews, lambda d, t: GraphicOverviews.structure(d))
        return converter

    @classmethod
    def structure(cls: type[TRecordSummary], value: dict) -> "RecordSummary":
        """
        Create a RecordSummary instance from plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(RecordSummary, lambda d, t: RecordSummary.structure(d))`
        """
        value_ = deepcopy(value)
        converter = cls._converter_up()
        return converter.structure(value_, cls)

    @staticmethod
    def _converter_down() -> cattrs.Converter:
        """
        Cattrs converter for unstructuring data.

        Standalone method for easier subclassing.
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(date, lambda d: d.isoformat())
        converter.register_unstructure_hook(Date, lambda d: d.unstructure())
        converter.register_unstructure_hook(Aggregations, lambda d: d.unstructure())
        converter.register_unstructure_hook(Constraints, lambda d: d.unstructure())
        converter.register_unstructure_hook(GraphicOverviews, lambda d: d.unstructure())
        return converter

    def unstructure(self) -> dict:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(RecordSummary, lambda d: d.unstructure())`
        """
        converter = self._converter_down()
        return clean_dict(converter.unstructure(self))

    def dumps(self) -> dict:
        """Create a JSON safe dict."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(RecordSummary, lambda d: d.unstructure())
        return converter.unstructure(self)

    @classmethod
    def _loads_json_dict(cls: type[TRecordSummary], value: dict) -> "RecordSummary":
        """Create a RecordSummary from a config dict loaded from JSON."""
        converter = cattrs.Converter()
        converter.register_structure_hook(RecordSummary, lambda d, t: RecordSummary.structure(d))
        return converter.structure(value, cls)

    @classmethod
    def _loads_record(cls: type[TRecordSummary], record: Record) -> "RecordSummary":
        """Create a RecordSummary from a Record."""
        return cls(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            date_stamp=record.metadata.date_stamp,
            title=record.identification.title,
            purpose=record.identification.purpose,
            edition=record.identification.edition,
            creation=record.identification.dates.creation,
            revision=record.identification.dates.revision,
            publication=record.identification.dates.publication,
            graphic_overviews=record.identification.graphic_overviews,
            constraints=record.identification.constraints,
            aggregations=record.identification.aggregations,
        )

    @classmethod
    def loads(cls: type[TRecordSummary], value: Record | dict) -> "RecordSummary":
        """Create a RecordSummary from a Record."""
        if isinstance(value, Record):
            return cls._loads_record(value)
        return cls._loads_json_dict(value)

    @property
    def revision_creation(self) -> Date:
        """Revision date, or creation if not defined."""
        return self.revision if self.revision else self.creation
