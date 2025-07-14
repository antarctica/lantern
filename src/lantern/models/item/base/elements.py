from dataclasses import dataclass, is_dataclass
from typing import Any, cast

from lantern.lib.metadata_library.models.record.elements.common import Contact as RecordContact
from lantern.lib.metadata_library.models.record.elements.common import Contacts as RecordContacts
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.elements.identification import Extent as RecordExtent
from lantern.lib.metadata_library.models.record.elements.identification import Extents as RecordExtents


class Contact(RecordContact):
    """
    Item Contact.

    Wrapper around Record Contact adding convenience properties.
    """

    def __init__(self, contact: RecordContact) -> None:
        """Initialise from an underlying Record Contact."""
        # noinspection PyTypeChecker
        props = unpack(contact)
        props.pop("_role")
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

    def __getitem__(self, index: int) -> Contact:
        """Override type."""
        return cast(Contact, super().__getitem__(index))


class Extent(RecordExtent):
    """
    Item Extent.

    Wrapper around Record Extent adding convenience properties.
    """

    def __init__(self, extent: RecordExtent) -> None:
        """Initialise from an underlying Record Extent."""
        # noinspection PyTypeChecker
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

    def __getitem__(self, index: int) -> Extent:
        """Override type."""
        return cast(Extent, super().__getitem__(index))


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
