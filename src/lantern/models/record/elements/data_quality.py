from dataclasses import dataclass
from typing import TypeVar

import cattrs

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Citation

TDataQuality = TypeVar("TDataQuality", bound="DataQuality")


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
    domain_consistency: list[DomainConsistency] | None = None

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.domain_consistency is None:
            self.domain_consistency = []

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
            dc["specification"]["contacts"] = [dc["specification"]["contact"]]
            del dc["specification"]["contact"]
            value["domain_consistency"][i] = dc

        converter = cattrs.Converter()
        converter.register_structure_hook(Citation, lambda d, t: Citation.structure(d))
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert DataQuality class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Citation, lambda d: d.unstructure())
        value = converter.unstructure(self)

        # workaround v4 schema not allowing multiple contacts
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        for i, dc in enumerate(value.get("domain_consistency", [])):
            dc["specification"]["contact"] = dc["specification"]["contacts"][0]
            del dc["specification"]["contacts"]
            value["domain_consistency"][i] = dc

        return value
