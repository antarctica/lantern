from dataclasses import dataclass, is_dataclass
from typing import Any, SupportsIndex, cast, overload

from lantern.lib.metadata_library.models.record.elements.common import Contact as RecordContact
from lantern.lib.metadata_library.models.record.elements.common import Contacts as RecordContacts
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.identification import Extent as RecordExtent
from lantern.lib.metadata_library.models.record.elements.identification import Extents as RecordExtents
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode


class Contact(RecordContact):
    """
    Item Contact.

    Wrapper around Record Contact adding convenience properties.
    """

    def __init__(self, contact: RecordContact) -> None:
        """Initialise from an underlying Record Contact."""
        props = unpack(contact)
        super().__init__(**props)

    @property
    def orcid(self) -> str | None:
        """ORCID."""
        if (
            self.individual is not None
            and self.individual.title is not None
            and self.individual.href is not None
            and self.individual.title == "orcid"
        ):
            return self.individual.href
        return None

    @property
    def ror(self) -> str | None:
        """ROR."""
        if (
            self.organisation is not None
            and self.organisation.title is not None
            and self.organisation.href is not None
            and self.organisation.title == "ror"
        ):
            return self.organisation.href
        return None


class Contacts(RecordContacts):
    """
    Contacts.

    Wrapper around Record Contacts to reflect correct type.
    """

    @overload
    def __getitem__(self, index: SupportsIndex) -> Contact: ...  # pragma: no branch

    @overload
    def __getitem__(self, index: slice) -> "Contacts": ...  # pragma: no branch

    def __getitem__(self, index: SupportsIndex | slice) -> "Contact | Contacts":
        """Get items as overloaded type."""
        result = super().__getitem__(index)
        return cast(Contacts, result) if isinstance(index, slice) else cast(Contact, result)

    def filter(self, roles: ContactRoleCode | list[ContactRoleCode]) -> "Contacts":
        """Get items as overloaded type."""
        return cast(Contacts, super().filter(roles))


class Extent(RecordExtent):
    """
    Item Extent.

    Wrapper around Record Extent adding convenience properties.
    """

    def __init__(self, extent: RecordExtent) -> None:
        """Initialise from an underlying Record Extent."""
        super().__init__(**unpack(extent))

    @property
    def bounding_box(self) -> list[float]:
        """Bounding box [west, south, east, north] [min_x, min_y, max_x, max_y]."""
        bbox = self.geographic.bounding_box
        return [bbox.west_longitude, bbox.south_latitude, bbox.east_longitude, bbox.north_latitude]

    @property
    def start(self) -> Date | None:
        """Temporal period start."""
        if self.temporal is None:
            return None
        return self.temporal.period.start if self.temporal.period else None

    @property
    def end(self) -> Date | None:
        """Temporal period end."""
        if self.temporal is None:
            return None
        return self.temporal.period.end if self.temporal.period else None


class Extents(RecordExtents):
    """
    Extents.

    Wrapper around Record Extents to reflect correct type.
    """

    @overload
    def __getitem__(self, index: SupportsIndex) -> Extent: ...  # pragma: no branch

    @overload
    def __getitem__(self, index: slice) -> "Extents": ...  # pragma: no branch

    def __getitem__(self, index: SupportsIndex | slice) -> "Extent | Extents":
        """Get items as overloaded type."""
        result = super().__getitem__(index)
        return cast(Extents, result) if isinstance(index, slice) else cast(Extent, result)

    def filter(self, identifier: str) -> "Extents":
        """Get items as overloaded type."""
        return cast(Extents, super().filter(identifier))


@dataclass
class Link:
    """
    HTML anchor.

    The href attribute is optional to account for situations where a dynamic action will be performed instead of a
    normal link. For example some distribution options do not have a single direct download link and will show
    additional information instead.
    """

    value: str
    href: str | None = None
    external: bool = False

    def __post_init__(self) -> None:
        """Process defaults."""
        if self.external is None:
            self.external = False


def unpack(value: Any) -> dict[str, Any]:  # noqa: ANN401
    """Unpack a dataclass into a dictionary non-recursively."""
    if not is_dataclass(value):
        msg = "Value must be a dataclass."
        raise TypeError(msg)

    return {key: getattr(value, key) for key in value.__dataclass_fields__}
