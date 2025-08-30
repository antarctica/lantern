from dataclasses import dataclass
from datetime import date

import pytest

from lantern.lib.metadata_library.models.record.elements.common import Contact as RecordContact
from lantern.lib.metadata_library.models.record.elements.common import (
    ContactIdentity,
    Date,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    BoundingBox,
    ExtentGeographic,
    ExtentTemporal,
    TemporalPeriod,
)
from lantern.lib.metadata_library.models.record.elements.identification import Extent as RecordExtent
from lantern.lib.metadata_library.models.record.enums import (
    ContactRoleCode,
)
from lantern.models.item.base.elements import (
    Contact,
    Contacts,
    Extent,
    Extents,
    Link,
    unpack,
)


@dataclass
class UnpackDataClass:
    """Resource for TestUnpack."""

    x: str


class UnpackRegularClass:
    """Resource for TestUnpack."""

    pass


class TestUnpack:
    """Test dataclass unpack util function."""

    def test_unpack(self):
        """Can unpack a dataclass."""
        expected = {"x": "x"}
        d = UnpackDataClass(x="x")

        result = unpack(d)
        assert result == expected

    @pytest.mark.cov()
    def test_error_type(self):
        """Cannot unpack something that isn't a dataclass."""
        c = UnpackRegularClass()

        with pytest.raises(TypeError, match="Value must be a dataclass."):
            unpack(c)


class TestContact:
    """Test Item Contact."""

    def test_init(self):
        """Creates a Contact."""
        rec_contact = RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})
        item_contact = Contact(rec_contact)
        assert isinstance(item_contact, Contact)

    @pytest.mark.parametrize("value", ["x", None])
    def test_ror(self, value: str | None):
        """Can get ROR."""
        rec_contact = RecordContact(
            organisation=ContactIdentity(name="x", title="ror", href=value), role={ContactRoleCode.POINT_OF_CONTACT}
        )
        item_contact = Contact(rec_contact)
        assert item_contact.ror == value

    @pytest.mark.parametrize("value", ["x", None])
    def test_orcid(self, value: str | None):
        """Can get ORCID."""
        rec_contact = RecordContact(
            individual=ContactIdentity(name="x", title="orcid", href=value), role={ContactRoleCode.POINT_OF_CONTACT}
        )
        item_contact = Contact(rec_contact)
        assert item_contact.orcid == value


class TestContacts:
    """Test Item Contacts."""

    def test_init(self):
        """Creates a Contacts container."""
        role = ContactRoleCode.POINT_OF_CONTACT
        rec_contact = RecordContact(organisation=ContactIdentity(name="x"), role={role})
        item_contact = Contact(rec_contact)

        item_contacts = Contacts([item_contact])
        assert isinstance(item_contacts, Contacts)
        assert item_contacts[0] == item_contact
        # verify methods from parent class are accessible
        assert len(item_contacts.filter(roles=role)) > 0


class TestExtent:
    """Test Item Extent."""

    date_ = Date(date=date(2014, 6, 30))

    def test_init(self):
        """Creates an Extent."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        item_extent = Extent(rec_extent)
        assert isinstance(item_extent, Extent)

    def test_bounding_box(self):
        """Can get bounding box."""
        coordinate = 1.0
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(
                    west_longitude=coordinate,
                    east_longitude=coordinate,
                    south_latitude=coordinate,
                    north_latitude=coordinate,
                )
            ),
        )
        item_extent = Extent(rec_extent)
        assert item_extent.bounding_box == [coordinate, coordinate, coordinate, coordinate]

    @pytest.mark.parametrize("value", [date_, None])
    def test_start(self, value: Date | None):
        """Can get start of temporal extent."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        if value is not None:
            rec_extent.temporal = ExtentTemporal(period=TemporalPeriod(start=value))

        item_extent = Extent(rec_extent)
        assert item_extent.start == value

    @pytest.mark.parametrize("value", [date_, None])
    def test_end(self, value: Date | None):
        """Can get start of temporal extent."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        if value is not None:
            rec_extent.temporal = ExtentTemporal(period=TemporalPeriod(end=value))

        item_extent = Extent(rec_extent)
        assert item_extent.end == value


class TestExtents:
    """Test Item Extents."""

    def test_init(self):
        """Creates an Extents container."""
        identifier = "bounding"
        rec_extent = RecordExtent(
            identifier=identifier,
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        item_extent = Extent(rec_extent)

        item_extents = Extents([item_extent])
        assert isinstance(item_extents, Extents)
        assert item_extents[0] == item_extent
        # verify methods from parent class are accessible
        assert len(item_extents.filter(identifier=identifier)) > 0


class TestLink:
    """Test HTML anchor representation."""

    @pytest.mark.parametrize(
        ("href", "external", "expected_href", "expected_external"), [("x", True, "x", True), (None, None, None, False)]
    )
    def test_init(self, href: str | None, external: bool | None, expected_href: str | None, expected_external: bool):
        """Creates a Link."""
        link = Link(value="x", href=href, external=external)
        assert link.href == expected_href
        assert link.external == expected_external
