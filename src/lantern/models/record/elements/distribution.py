from dataclasses import dataclass

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Contact, OnlineResource
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import ContactRoleCode


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
