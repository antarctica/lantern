from dataclasses import dataclass
from typing import TypeVar

import cattrs

from lantern.lib.metadata_library.models.record.elements.common import Contact, OnlineResource
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode

TDistributions = TypeVar("TDistributions", bound="Distributions")


@dataclass(kw_only=True)
class Format:
    """
    Format.

    Schema definition: format [1]
    ISO element: gmd:MD_Format [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L625
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_Format.html
    """

    format: str
    href: str | None = None


@dataclass(kw_only=True)
class Size:
    """
    Size.

    Schema definition: size [1]
    ISO element: gmd:transferSize [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1776
    [2] https://www.datypic.com/sc/niem21/e-gmd_transferSize-1.html
    """

    unit: str
    magnitude: float


@dataclass(kw_only=True)
class TransferOption:
    """
    Transfer Option.

    Schema definition: transfer_option [1]
    ISO element: gmd:MD_DigitalTransferOptions [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1767
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_DigitalTransferOptions.html
    """

    size: Size | None = None
    online_resource: OnlineResource


@dataclass(kw_only=True)
class Distribution:
    """
    Distribution.

    Schema definition: distribution [1]
    ISO element: gmd:MD_Distribution [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L515
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_Distribution.html
    """

    format: Format | None = None
    distributor: Contact
    transfer_option: TransferOption

    def __post_init__(self) -> None:
        """Process defaults."""
        if ContactRoleCode.DISTRIBUTOR not in self.distributor.role:
            msg = "Distributor contact must include the 'distributor' role."
            raise ValueError(msg) from None

    def unstructure(self) -> dict:
        """
        Convert Metadata class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Distribution, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Contact, lambda d: d.unstructure())
        return converter.unstructure(self)


class Distributions(list[Distribution]):
    """
    Distribution options.

    Wrapper around a list of Distribution items with additional methods for managing items.

    Schema definition: distribution [1]
    ISO element: gmd:MD_Distribution [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.16.0/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L486
    [2] https://www.datypic.com/sc/niem21/e-gmd_MD_Distribution.html
    """

    @classmethod
    def structure(cls: type[TDistributions], value: list[dict]) -> "Distributions":
        """
        Parse contacts from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Distributions, lambda d, t: Distributions.structure(d))`

        Structures input items into a list of Distribution option items via cattrs as a new instance of this class.

        Example input: [{"distributor": {"organisation": {"name": "x"}, "role": ["distributor"]}, "transfer_option": {"online_resource": {"href": "x", "function": "download"}}}]
        Example output: Distributions([Distribution(distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}), transfer_option=TransferOption(online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)))])
        """
        converter = cattrs.Converter()
        return cls([converter.structure(distribution, Distribution) for distribution in value])

    def unstructure(self) -> list[dict]:
        """
        Convert to plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Distributions, lambda d: d.unstructure())`

        Example input: Distributions([Distribution(distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}), transfer_option=TransferOption(online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)))])
        Example output: [{"distributor": {"organisation": {"name": "x"}, "role": ["distributor"]}, "transfer_option": {"online_resource": {"href": "x", "function": "download"}}}]
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Distribution, lambda d: d.unstructure())
        return [converter.unstructure(distribution) for distribution in self]

    def ensure(self, distribution: Distribution) -> None:
        """Add distribution option without creating duplicates."""
        if distribution in self:
            # skip exact match
            return

        self.append(distribution)
