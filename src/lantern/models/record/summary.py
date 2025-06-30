from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import TypeVar

import cattrs

from lantern.models.record import Record
from lantern.models.record.elements.common import Date
from lantern.models.record.elements.identification import (
    Aggregations,
    Constraints,
    GraphicOverviews,
)
from lantern.models.record.enums import HierarchyLevelCode

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

    @classmethod
    def structure(cls: type[TRecordSummary], value: dict) -> "RecordSummary":
        """
        Create a RecordSummary instance from plain types.

        Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(RecordSummary, lambda d, t: RecordSummary.structure(d))`
        """
        value_ = deepcopy(value)

        converter = cattrs.Converter()
        converter.register_structure_hook(date, lambda d, t: date.fromisoformat(d))
        converter.register_structure_hook(Date, lambda d, t: Date.structure(d))
        converter.register_structure_hook(Aggregations, lambda d, t: Aggregations.structure(d))
        converter.register_structure_hook(Constraints, lambda d, t: Constraints.structure(d))
        converter.register_structure_hook(GraphicOverviews, lambda d, t: GraphicOverviews.structure(d))
        return converter.structure(value_, cls)

    @classmethod
    def subset_config(cls: type[TRecordSummary], value: dict) -> dict:
        """Create a RecordSummary config from a Record config."""
        return {
            "file_identifier": value.get("file_identifier"),
            "hierarchy_level": value["hierarchy_level"],
            "date_stamp": value["metadata"]["date_stamp"],
            "title": value["identification"]["title"]["value"],
            "purpose": value["identification"].get("purpose", None),
            "edition": value["identification"].get("edition", None),
            "creation": value["identification"]["dates"]["creation"],
            "revision": value["identification"]["dates"].get("revision", None),
            "publication": value["identification"]["dates"].get("publication", None),
            "graphic_overviews": value["identification"].get("graphic_overviews", []),
            "constraints": value["identification"].get("constraints", []),
            "aggregations": value["identification"].get("aggregations", []),
        }

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
