from dataclasses import dataclass, field
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record.elements.common import Citation

TDataQuality = TypeVar("TDataQuality", bound="DataQuality")
TDomainConsistencies = TypeVar("TDomainConsistencies", bound="DomainConsistencies")


@dataclass(kw_only=True)
class Lineage:
    """
    Lineage.

    Schema definition: lineage [1]
    ISO element: gmd:LI_Lineage [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1083
    [2] https://www.datypic.com/sc/niem21/e-gmd_LI_Lineage.html
    """

    statement: str


@dataclass(kw_only=True)
class DomainConsistency:
    """
    Domain Consistency.

    Schema definition: domain_consistency_measure [1]
    ISO element: gmd:DQ_DomainConsistency [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L536
    [2] https://www.datypic.com/sc/niem21/e-gmd_DQ_DomainConsistency.html
    """

    specification: Citation
    explanation: str
    result: bool


class DomainConsistencies(list[DomainConsistency]):
    """
    DomainConsistencies.

    Wrapper around a list of DomainConsistency items with additional methods for filtering/managing items.

    Schema definition: identifiers [1]
    ISO element: gmd:report [2] (represents a single data quality element, multiple reports are allowed)

    [1] https://github.com/antarctica/metadata-library/blob/v0.16.0/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L562
    [2] https://www.datypic.com/sc/niem21/e-gmd_report-1.html
    """

    @classmethod
    def structure(cls: type[TDomainConsistencies], value: list[dict]) -> "DomainConsistencies":
        """
        Parse domain consistency elements from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(DomainConsistencies, lambda d, t: DomainConsistencies.structure(d))`

        Structures input items into a list of DomainConsistency items via cattrs as a new instance of this class.

        Example input: [{"specification": {"title": {"value": "x"}, "dates": {"creation": '2014-06-30'}}, "explanation": "x", "result": True}]
        Example output: DomainConsistencies([DomainConsistency(specification=Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))), explanation="x", result=True)])
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Citation, lambda d, t: Citation.structure(d))
        return cls([converter.structure(domain, DomainConsistency) for domain in value])

    def unstructure(self) -> list[dict]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(DomainConsistencies, lambda d: d.unstructure())`

        Example input: DomainConsistencies([DomainConsistency(specification=Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))), explanation="x", result=True)])
        Example output: [{"specification": {"title": {"value": "x"}, "dates": {"creation": '2014-06-30'}}, "explanation": "x", "result": True}]
        """
        # noinspection PyUnresolvedReferences
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Citation, lambda d: d.unstructure())
        return [converter.unstructure(identifier) for identifier in self]

    def filter(self, href: str) -> "DomainConsistencies":
        """Filter domain consistency elements by specification href."""
        return DomainConsistencies([domain for domain in self if domain.specification.href == href])

    def ensure(self, domain: DomainConsistency) -> None:
        """Add domain consistency elements without creating duplicates."""
        if domain in self:
            # skip exact match
            return

        self.append(domain)


@dataclass(kw_only=True)
class DataQuality:
    """
    Data Quality.

    This element is not yet represented in the v4 JSON Schema but will in future versions. The top-level Record object
    workaround this limitation by moving elements from the Identification element to this one.

    Schema definition: N/A [1]
    ISO element: gmd:DQ_DataQuality [2]

    [1] -
    [2] https://www.datypic.com/sc/niem21/e-gmd_DQ_DataQuality.html
    """

    lineage: Lineage | None = None
    domain_consistency: DomainConsistencies = field(default_factory=DomainConsistencies)

    @classmethod
    def structure(cls: type[TDataQuality], value: dict) -> "DataQuality":
        """
        Parse DataQuality class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(DataQuality, lambda d, t: DataQuality.structure(d))`
        """
        # workaround v4 schema not allowing multiple contacts
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        for i, dc in enumerate(value.get("domain_consistency", [])):
            if "contact" not in dc["specification"]:
                continue
            dc["specification"]["contacts"] = [dc["specification"]["contact"]]
            del dc["specification"]["contact"]
            value["domain_consistency"][i] = dc

        converter = cattrs.Converter()
        converter.register_structure_hook(DomainConsistencies, lambda d, t: DomainConsistencies.structure(d))
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert DataQuality class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(DomainConsistencies, lambda d: d.unstructure())
        value = converter.unstructure(self)

        # workaround v4 schema not allowing multiple contacts
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        for i, dc in enumerate(value.get("domain_consistency", [])):
            if not dc["specification"]["contacts"]:
                continue
            dc["specification"]["contact"] = dc["specification"]["contacts"][0]
            del dc["specification"]["contacts"]
            value["domain_consistency"][i] = dc

        return value
