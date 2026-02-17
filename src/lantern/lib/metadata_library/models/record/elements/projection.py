from dataclasses import dataclass
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record.elements.common import Citation

TProjection = TypeVar("TProjection", bound="ReferenceSystemInfo")


@dataclass(kw_only=True)
class Code:
    """
    Reference System Info (projection) Code.

    Analogous to an Identifier which should be used but can't in v4 schema.

    Schema definition: code [1]
    ISO element: gmd:code [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1374
    [2] https://www.datypic.com/sc/niem21/e-gmd_code-1.html
    """

    value: str
    href: str | None = None


@dataclass(kw_only=True)
class ReferenceSystemInfo:
    """
    Reference System Info (projection).

    Schema definition: reference_system_info [1]
    ISO element: gmd:referenceSystemInfo [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1365
    [2] https://www.datypic.com/sc/niem21/e-gmd_referenceSystemInfo-1.html
    """

    code: Code
    version: str | None = None
    authority: Citation | None = None

    @classmethod
    def structure(cls: type[TProjection], value: dict) -> "ReferenceSystemInfo":
        """
        Parse ReferenceSystemInfo class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(ReferenceSystemInfo, lambda d, t: ReferenceSystemInfo.structure(d))`
        """
        # workaround v4 schema not allowing multiple contacts
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        if "authority" in value and "contact" in value["authority"]:
            value["authority"]["contacts"] = [value["authority"]["contact"]]
            del value["authority"]["contact"]

        converter = cattrs.Converter()
        converter.register_structure_hook(Citation, lambda d, t: Citation.structure(d))
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert ReferenceSystemInfo class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(ReferenceSystemInfo, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Citation, lambda d: d.unstructure())
        value = converter.unstructure(self)

        # workaround v4 schema not allowing multiple contacts
        # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-library/-/issues/255
        if value["authority"] and value["authority"]["contacts"]:
            value["authority"]["contact"] = value["authority"]["contacts"][0]
            del value["authority"]["contacts"]

        return value
