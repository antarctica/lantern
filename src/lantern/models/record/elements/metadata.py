from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import TypeVar

import cattrs

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Contacts

TMetadata = TypeVar("TMetadata", bound="Metadata")


@dataclass(kw_only=True)
class MetadataStandard:
    """
    Metadata Standard.

    Meta grouping of top-level elements related to metadata standard used in record itself rather than the resource.

    Schema definition: metadata_standard [1]
    ISO element: gmd:metadataStandardName / gmd:metadataStandardVersion [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1180
    [2] https://www.datypic.com/sc/niem21/e-gmd_metadataStandardName-1.html,
        https://www.datypic.com/sc/niem21/e-gmd_metadataStandardVersion-1.html
    """

    name: str = "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data"
    version: str = "ISO 19115-2:2009(E)"


@dataclass(kw_only=True)
class Metadata:
    """
    Metadata.

    Meta grouping of top-level elements related to metadata record itself rather than the resource.

    Schema definition: metadata [1]
    ISO element: N/A [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1150
    [2] -
    """

    character_set: str = "utf8"
    language: str = "eng"
    contacts: Contacts = field(default_factory=Contacts)
    date_stamp: date = field(default_factory=lambda: datetime.now(tz=UTC).date())
    metadata_standard: MetadataStandard = field(default_factory=MetadataStandard)

    def __post_init__(self) -> None:
        """Process defaults."""
        if len(self.contacts) < 1:
            msg = "At least one contact is required"
            raise ValueError(msg) from None

        if self.date_stamp is None:
            self.date_stamp = datetime.now(tz=UTC).date()

    @classmethod
    def structure(cls: type[TMetadata], value: dict) -> "Metadata":
        """
        Parse Metadata class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(Metadata, lambda d, t: Metadata.structure(d))`
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(Contacts, lambda d, t: Contacts.structure(d))
        converter.register_structure_hook(date, lambda d, t: date.fromisoformat(d))
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert Metadata class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(Metadata, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Contacts, lambda d: d.unstructure())
        converter.register_unstructure_hook(date, lambda d: d.isoformat())
        return converter.unstructure(self)
