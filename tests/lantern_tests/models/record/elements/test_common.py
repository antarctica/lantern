from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import cattrs
import pytest

from lantern.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
    OnlineResource,
    Series,
    clean_dict,
    clean_list,
)
from lantern.models.record.enums import ContactRoleCode, DatePrecisionCode, DateTypeCode, OnlineResourceFunctionCode

MIN_CITATION = {
    "title": "x",
    "dates": Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))),
}


class TestCleanDict:
    """Test clean_dict util function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ({}, {}),
            ({"foo": None}, {}),
            ({"foo": []}, {}),
            ({"foo": {}}, {}),
            ({"foo": None, "bar": [], "baz": {}}, {}),
            ({"foo": {"bar": "x"}}, {"foo": {"bar": "x"}}),
            ({"foo": {"bar": {}}}, {}),
        ],
    )
    def test_clean_dict(self, value: dict, expected: dict):
        """Can clean a dictionary containing None values."""
        result = clean_dict(value)
        assert result == expected


class TestCleanList:
    """Test clean_list util function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ([], []),
            ([None], []),
            ([{}], []),
            ([None, [], {}], []),
            ([{"foo": None}], []),
            ([{"foo": []}], []),
            ([{"foo": {}}], []),
            ([{"foo": {"bar": "x"}}], [{"foo": {"bar": "x"}}]),
            ([{"foo": {"bar": {}}}], []),
        ],
    )
    def test_clean_list(self, value: list, expected: list):
        """Can clean a list containing None values."""
        result = clean_list(value)
        assert result == expected


class TestAddress:
    """Test Address element."""

    @pytest.mark.parametrize(
        "values",
        [
            {},
            {"delivery_point": "x", "city": "x", "administrative_area": "x", "postal_code": "x", "country": "x"},
        ],
    )
    def test_init(self, values: dict):
        """Can create an Address element from directly assigned properties."""
        expected = "x"
        address = Address(**values)

        if "delivery_point" in values:
            assert address.delivery_point == expected
        else:
            assert address.delivery_point is None

        if "city" in values:
            assert address.city == expected
        else:
            assert address.city is None

        if "administrative_area" in values:
            assert address.administrative_area == expected
        else:
            assert address.administrative_area is None

        if "postal_code" in values:
            assert address.postal_code == expected
        else:
            assert address.postal_code is None

        if "country" in values:
            assert address.country == expected
        else:
            assert address.country is None


class TestCitation:
    """Test Citation element."""

    @pytest.mark.parametrize(
        "values",
        [
            {**MIN_CITATION},
            {**MIN_CITATION, "edition": "x"},
            {**MIN_CITATION, "href": "x"},
            {**MIN_CITATION, "other_citation_details": "x"},
            {**MIN_CITATION, "identifiers": [Identifier(identifier="x", href="x", namespace="x")]},
            {
                **MIN_CITATION,
                "contacts": [Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])],
            },
            {**MIN_CITATION, "series": Series(name="x", edition="x", page="x")},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Citation element from directly assigned properties."""
        expected = "x"
        expected_date = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        citation = Citation(**values)

        assert citation.title == expected
        assert citation.dates.creation.date == expected_date

        if "edition" in values:
            assert citation.edition == expected
        else:
            assert citation.edition is None

        if "href" in values:
            assert citation.href == expected
        else:
            assert citation.href is None

        if "other_citation_details" in values:
            assert citation.other_citation_details == expected
        else:
            assert citation.other_citation_details is None

        if "identifiers" in values and isinstance(values["identifiers"], list) and len(values["identifiers"]) > 0:
            assert all(isinstance(identifier, Identifier) for identifier in citation.identifiers)
        else:
            assert citation.identifiers == []

        if "contacts" in values:
            assert all(isinstance(contact, Contact) for contact in citation.contacts)
        else:
            assert citation.contacts == []

        if "series" in values:
            assert citation.series.name == values["series"].name if values["series"].name is not None else None
            assert citation.series.edition == values["series"].edition if values["series"].edition is not None else None
            assert citation.series.page == values["series"].page if values["series"].page is not None else None
        else:
            assert citation.series.name is None
            assert citation.series.edition is None
            assert citation.series.page is None

    def test_structure_cattrs(self):
        """Can use Cattrs to create a Citation instance from plain types."""
        expected_date = date(2014, 6, 30)
        value = {
            "title": {"value": "x", "href": "x"},
            "dates": {"creation": expected_date.isoformat()},
        }
        expected = Citation(title="x", dates=Dates(creation=Date(date=expected_date)), href="x")

        converter = cattrs.Converter()
        converter.register_structure_hook(Dates, lambda d, t: Dates.structure(d))
        converter.register_structure_hook(Citation, lambda d, t: Citation.structure(d))
        result = converter.structure(value, Citation)

        assert result == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))),
                {
                    "title": {"value": "x"},
                    "dates": {"creation": "2014-06-30"},
                },
            ),
            (
                Citation(title="x", dates=Dates(creation=Date(date=date(2014, 6, 30))), href="x"),
                {
                    "title": {"value": "x", "href": "x"},
                    "dates": {"creation": "2014-06-30"},
                },
            ),
        ],
    )
    def test_unstructure_cattrs(self, value: Citation, expected: dict):
        """Can use Cattrs to convert a Citation instance into plain types."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(Citation, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected


class TestContactIdentity:
    """Test ContactIdentity element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"name": "x"},
            {"name": "x", "href": "x", "title": "x"},
        ],
    )
    def test_init(self, values: dict):
        """Can create a ContactIdentity element from directly assigned properties."""
        expected = "x"
        identity = ContactIdentity(**values)

        assert identity.name == expected

        if "href" in values:
            assert identity.href == expected
        else:
            assert identity.href is None

        if "title" in values:
            assert identity.title == expected
        else:
            assert identity.title is None


class TestContact:
    """Test Contact element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"organisation": ContactIdentity(name="x"), "role": [ContactRoleCode.POINT_OF_CONTACT]},
            {"individual": ContactIdentity(name="x"), "role": [ContactRoleCode.POINT_OF_CONTACT]},
            {
                "organisation": ContactIdentity(name="x"),
                "phone": "x",
                "address": Address(),
                "email": "x",
                "online_resource": OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD),
                "role": [ContactRoleCode.POINT_OF_CONTACT],
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a Contact element from directly assigned properties."""
        expected = "x"
        expected_identity = ContactIdentity(name="x")
        expected_address = Address()
        expected_online = OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
        contact = Contact(**values)

        if "organisation" in values:
            assert contact.organisation == expected_identity
        else:
            assert contact.organisation is None

        if "individual" in values:
            assert contact.individual == expected_identity
        else:
            assert contact.individual is None

        if "phone" in values:
            assert contact.phone == expected
        else:
            assert contact.phone is None

        if "address" in values:
            assert contact.address == expected_address
        else:
            assert contact.address is None

        if "email" in values:
            assert contact.email == expected
        else:
            assert contact.email is None

        if "online_resource" in values:
            assert contact.online_resource == expected_online
        else:
            assert contact.online_resource is None

    def test_invalid_identity(self):
        """Can't create a Contact if neither individual nor organisation is provided."""
        with pytest.raises(ValueError, match="At least one of individual or organisation is required"):
            Contact(role=[])

    def test_invalid_roles(self):
        """Can't create a Contact without a role."""
        with pytest.raises(ValueError, match="At least one role is required"):
            Contact(individual=ContactIdentity(name="x"), role=[])

    def test_unique_roles(self):
        """Contact.role property does not contain duplicate values."""
        contact = Contact(
            organisation=ContactIdentity(name="x"), role=[ContactRoleCode.PUBLISHER, ContactRoleCode.PUBLISHER]
        )
        assert contact.role == [ContactRoleCode.PUBLISHER]

    @pytest.mark.parametrize(
        ("first", "second", "expected"),
        [
            (
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.PUBLISHER]),
                True,
            ),
            (
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                Contact(organisation=ContactIdentity(name="y"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                False,
            ),
        ],
    )
    def test_eq_no_roles(self, first: Contact, second: Contact, expected: bool):
        """Can compare two Contacts ignoring different roles."""
        assert first.eq_no_roles(second) == expected

    @pytest.mark.parametrize(
        ("first", "second", "expected"),
        [
            (
                Contact(
                    organisation=ContactIdentity(name="x"),
                    role=[ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER],
                ),
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.PUBLISHER]),
                True,
            ),
            (
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
                False,
            ),
            (
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                Contact(organisation=ContactIdentity(name="y"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                False,
            ),
            (
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT]),
                True,
            ),
        ],
    )
    def test_eq_contains_roles(self, first: Contact, second: Contact, expected: bool):
        """Can compare two Contacts checking if roles overlap."""
        assert first.eq_contains_roles(second) == expected


class TestContacts:
    """Test Contacts container."""

    def test_init(self):
        """Can create a Contacts container from directly assigned properties."""
        expected = Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])
        contacts = Contacts([expected])

        assert len(contacts) == 1
        assert contacts[0] == expected

    test_filer_roles_poc = Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])
    test_filer_roles_author = Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR])
    test_filer_roles_poc_publisher = Contact(
        organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER]
    )

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                ContactRoleCode.POINT_OF_CONTACT,
                [test_filer_roles_poc, test_filer_roles_poc_publisher],
            ),
            (
                [ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.AUTHOR],
                [test_filer_roles_poc, test_filer_roles_author, test_filer_roles_poc_publisher],
            ),
            ([], []),
        ],
    )
    def test_filter_roles(self, value: ContactRoleCode | list[ContactRoleCode], expected: list[Contact]):
        """Can filter contacts by one or more roles."""
        contacts = Contacts(
            [self.test_filer_roles_poc, self.test_filer_roles_author, self.test_filer_roles_poc_publisher]
        )

        result = contacts.filter(value)
        assert result == expected

    def test_structure(self):
        """Can create a Contacts container by converting a list of plain types."""
        expected = Contacts([Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])])
        result = Contacts.structure([{"organisation": {"name": "x"}, "role": ["pointOfContact"]}])

        assert type(result) is type(expected)
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create a Contacts instance from plain types."""
        value = [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}]
        expected = Contacts([Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])])

        converter = cattrs.Converter()
        converter.register_structure_hook(Contacts, lambda d, t: Contacts.structure(d))
        result = converter.structure(value, Contacts)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a Contacts instance into plain types."""
        value = Contacts([Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])])
        expected = [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Contacts, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


class TestDate:
    """Test Date element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"date": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)},
            {"date": datetime(2014, 6, 30, tzinfo=UTC).date(), "precision": DatePrecisionCode.YEAR},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Date element from directly assigned properties."""
        date_ = Date(**values)

        assert date_.date == values["date"]
        if "precision" in values:
            assert date_.precision == values["precision"]
        else:
            assert date_.precision is None

    def test_no_timezone(self):
        """Invalid timezone triggers error."""
        with pytest.raises(ValueError, match=r"Invalid timezone: \[None\]. It must be UTC."):
            Date(date=datetime.now())  # noqa: DTZ005

    def test_invalid_timezone(self):
        """Invalid timezone triggers error."""
        with pytest.raises(ValueError, match=r"Invalid timezone: \[America/Lima\]. It must be UTC."):
            Date(date=datetime.now(tz=ZoneInfo("America/Lima")))

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                {"date": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)},
                "2014-06-30T14:30:45+00:00",
            ),
            (
                {"date": datetime(2014, 6, 30, 14, 30, tzinfo=UTC)},
                "2014-06-30T14:30:00+00:00",
            ),
            (
                {"date": datetime(2014, 6, 30, 14, tzinfo=UTC)},
                "2014-06-30T14:00:00+00:00",
            ),
            (
                {"date": datetime(2014, 6, 30, tzinfo=UTC).date()},
                "2014-06-30",
            ),
            (
                {"date": datetime(2014, 6, 30, tzinfo=UTC).date(), "precision": DatePrecisionCode.MONTH},
                "2014-06",
            ),
            (
                {"date": datetime(2014, 6, 30, tzinfo=UTC).date(), "precision": DatePrecisionCode.YEAR},
                "2014",
            ),
        ],
    )
    def test_isoformat(self, values: dict, expected: str):
        """Can format a date with relevant precision."""
        date_ = Date(**values)

        assert date_.isoformat == expected
        if "precision" in values:
            assert date_.precision == values["precision"]
        else:
            assert date_.precision is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                "2014-06-30T14:30:45+00:00",
                (datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC), None),
            ),
            ("2014-06-30T14:30:00+00:00", (datetime(2014, 6, 30, 14, 30, tzinfo=UTC), None)),
            ("2014-06-30T14:00:00+00:00", (datetime(2014, 6, 30, 14, tzinfo=UTC), None)),
            ("2014-06-30", (datetime(2014, 6, 30, tzinfo=UTC).date(), None)),
            (
                "2014-06",
                (datetime(2014, 6, 1, tzinfo=UTC).date(), DatePrecisionCode.MONTH),
            ),
            (
                "2014",
                (datetime(2014, 1, 1, tzinfo=UTC).date(), DatePrecisionCode.YEAR),
            ),
        ],
    )
    def test_structure(self, value: str, expected: tuple[datetime | date, DatePrecisionCode | None]):
        """Can create a Date element by parsing a date string."""
        date_, precision = expected
        result = Date.structure(value)

        assert result.date == date_
        assert result.precision == precision

    def test_unstructure(self):
        """Can convert a Date element to plain types."""
        value = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        expected = "2014-06-30T14:30:45+00:00"
        result = value.unstructure()

        assert result == expected


class TestDates:
    """Test Dates container element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"creation": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)},
            {"publication": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)},
            {
                "creation": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "publication": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "revision": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "adopted": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "deprecated": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "distribution": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "expiry": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "in_force": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "last_revision": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "last_update": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "next_update": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "released": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "superseded": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "unavailable": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "validity_begins": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
                "validity_expires": datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC),
            },
        ],
    )
    def test_init(self, values: dict):  # noqa: C901
        """Can create a Dates container from directly assigned properties."""
        expected_date = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        dates = Dates(**values)

        if "creation" in values:
            assert dates.creation == expected_date
        else:
            assert dates.creation is None
        if "publication" in values:
            assert dates.publication == expected_date
        else:
            assert dates.publication is None
        if "revision" in values:
            assert dates.revision == expected_date
        else:
            assert dates.revision is None
        if "adopted" in values:
            assert dates.adopted == expected_date
        else:
            assert dates.adopted is None
        if "deprecated" in values:
            assert dates.deprecated == expected_date
        else:
            assert dates.deprecated is None
        if "distribution" in values:
            assert dates.distribution == expected_date
        else:
            assert dates.distribution is None
        if "expiry" in values:
            assert dates.expiry == expected_date
        else:
            assert dates.expiry is None
        if "in_force" in values:
            assert dates.in_force == expected_date
        else:
            assert dates.in_force is None
        if "last_revision" in values:
            assert dates.last_revision == expected_date
        else:
            assert dates.last_revision is None
        if "last_update" in values:
            assert dates.last_update == expected_date
        else:
            assert dates.last_update is None
        if "next_update" in values:
            assert dates.next_update == expected_date
        else:
            assert dates.next_update is None
        if "released" in values:
            assert dates.released == expected_date
        else:
            assert dates.released is None
        if "superseded" in values:
            assert dates.superseded == expected_date
        else:
            assert dates.superseded is None
        if "unavailable" in values:
            assert dates.unavailable == expected_date
        else:
            assert dates.unavailable is None
        if "validity_begins" in values:
            assert dates.validity_begins == expected_date
        else:
            assert dates.validity_begins is None
        if "validity_expires" in values:
            assert dates.validity_expires == expected_date
        else:
            assert dates.validity_expires is None

    def test_invalid_empty(self):
        """Can't create a Dates container without any dates."""
        with pytest.raises(ValueError, match="At least one date is required"):
            Dates()

    @pytest.mark.parametrize(
        "value",
        [Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)), None],
    )
    def test_get_item(self, value: Date | None):
        """Can get a date by key."""
        dates = Dates(
            creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)),
            publication=value,
        )

        assert dates["publication"] == dates.publication
        assert dates["publication"] == value

    def test_as_dict_enum(self):
        """Can convert a Dates container to a dictionary with enum values."""
        creation = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        dates = Dates(creation=creation)
        expected = {DateTypeCode.CREATION: creation}

        result = dates.as_dict_enum()
        assert result == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                {"lastUpdate": "2014"},
                Dates(last_update=Date(date=date(2014, 1, 1), precision=DatePrecisionCode.YEAR)),
            ),
            (
                {
                    "creation": "2014-06-01T12:30:45+00:00",
                    "publication": "2014-06-02T12:30:45+00:00",
                    "revision": "2014-06-03T12:30:45+00:00",
                    "adopted": "2014-06-04T12:30:45+00:00",
                    "deprecated": "2014-06-05T12:30:45+00:00",
                    "distribution": "2014-06-06T12:30:45+00:00",
                    "expiry": "2014-06-07T12:30:45+00:00",
                    "inForce": "2014-06-08T12:30:45+00:00",
                    "lastRevision": "2014-06-09T12:30:45+00:00",
                    "lastUpdate": "2014-06-10T12:30:45+00:00",
                    "nextUpdate": "2014-06-11T12:30:45+00:00",
                    "released": "2014-06-12T12:30:45+00:00",
                    "superseded": "2014-06-13T12:30:45+00:00",
                    "unavailable": "2014-06-14T12:30:45+00:00",
                    "validityBegins": "2014-06-15T12:30:45+00:00",
                    "validityExpires": "2014-06-16T12:30:45+00:00",
                },
                Dates(
                    creation=Date(date=datetime(2014, 6, 1, 12, 30, second=45, tzinfo=UTC)),
                    publication=Date(date=datetime(2014, 6, 2, 12, 30, second=45, tzinfo=UTC)),
                    revision=Date(date=datetime(2014, 6, 3, 12, 30, second=45, tzinfo=UTC)),
                    adopted=Date(date=datetime(2014, 6, 4, 12, 30, second=45, tzinfo=UTC)),
                    deprecated=Date(date=datetime(2014, 6, 5, 12, 30, second=45, tzinfo=UTC)),
                    distribution=Date(date=datetime(2014, 6, 6, 12, 30, second=45, tzinfo=UTC)),
                    expiry=Date(date=datetime(2014, 6, 7, 12, 30, second=45, tzinfo=UTC)),
                    in_force=Date(date=datetime(2014, 6, 8, 12, 30, second=45, tzinfo=UTC)),
                    last_revision=Date(date=datetime(2014, 6, 9, 12, 30, second=45, tzinfo=UTC)),
                    last_update=Date(date=datetime(2014, 6, 10, 12, 30, second=45, tzinfo=UTC)),
                    next_update=Date(date=datetime(2014, 6, 11, 12, 30, second=45, tzinfo=UTC)),
                    released=Date(date=datetime(2014, 6, 12, 12, 30, second=45, tzinfo=UTC)),
                    superseded=Date(date=datetime(2014, 6, 13, 12, 30, second=45, tzinfo=UTC)),
                    unavailable=Date(date=datetime(2014, 6, 14, 12, 30, second=45, tzinfo=UTC)),
                    validity_begins=Date(date=datetime(2014, 6, 15, 12, 30, second=45, tzinfo=UTC)),
                    validity_expires=Date(date=datetime(2014, 6, 16, 12, 30, second=45, tzinfo=UTC)),
                ),
            ),
        ],
    )
    def test_structure(self, value: dict, expected: Dates):
        """Can create a Dates container by converting a dict of plain types."""
        result = Dates.structure(value)

        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create a Dates instance from plain types."""
        value = {"lastUpdate": "2014"}
        expected = Dates(last_update=Date(date=date(2014, 1, 1), precision=DatePrecisionCode.YEAR))

        converter = cattrs.Converter()
        converter.register_structure_hook(Dates, lambda d, t: Dates.structure(d))
        result = converter.structure(value, Dates)

        assert result == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                Dates(
                    last_update=Date(
                        date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC), precision=DatePrecisionCode.YEAR
                    )
                ),
                {"lastUpdate": "2014"},
            ),
            (
                Dates(
                    creation=Date(date=datetime(2014, 6, 1, 12, 30, second=45, tzinfo=UTC)),
                    publication=Date(date=datetime(2014, 6, 2, 12, 30, second=45, tzinfo=UTC)),
                    revision=Date(date=datetime(2014, 6, 3, 12, 30, second=45, tzinfo=UTC)),
                    adopted=Date(date=datetime(2014, 6, 4, 12, 30, second=45, tzinfo=UTC)),
                    deprecated=Date(date=datetime(2014, 6, 5, 12, 30, second=45, tzinfo=UTC)),
                    distribution=Date(date=datetime(2014, 6, 6, 12, 30, second=45, tzinfo=UTC)),
                    expiry=Date(date=datetime(2014, 6, 7, 12, 30, second=45, tzinfo=UTC)),
                    in_force=Date(date=datetime(2014, 6, 8, 12, 30, second=45, tzinfo=UTC)),
                    last_revision=Date(date=datetime(2014, 6, 9, 12, 30, second=45, tzinfo=UTC)),
                    last_update=Date(date=datetime(2014, 6, 10, 12, 30, second=45, tzinfo=UTC)),
                    next_update=Date(date=datetime(2014, 6, 11, 12, 30, second=45, tzinfo=UTC)),
                    released=Date(date=datetime(2014, 6, 12, 12, 30, second=45, tzinfo=UTC)),
                    superseded=Date(date=datetime(2014, 6, 13, 12, 30, second=45, tzinfo=UTC)),
                    unavailable=Date(date=datetime(2014, 6, 14, 12, 30, second=45, tzinfo=UTC)),
                    validity_begins=Date(date=datetime(2014, 6, 15, 12, 30, second=45, tzinfo=UTC)),
                    validity_expires=Date(date=datetime(2014, 6, 16, 12, 30, second=45, tzinfo=UTC)),
                ),
                {
                    "creation": "2014-06-01T12:30:45+00:00",
                    "publication": "2014-06-02T12:30:45+00:00",
                    "revision": "2014-06-03T12:30:45+00:00",
                    "adopted": "2014-06-04T12:30:45+00:00",
                    "deprecated": "2014-06-05T12:30:45+00:00",
                    "distribution": "2014-06-06T12:30:45+00:00",
                    "expiry": "2014-06-07T12:30:45+00:00",
                    "inForce": "2014-06-08T12:30:45+00:00",
                    "lastRevision": "2014-06-09T12:30:45+00:00",
                    "lastUpdate": "2014-06-10T12:30:45+00:00",
                    "nextUpdate": "2014-06-11T12:30:45+00:00",
                    "released": "2014-06-12T12:30:45+00:00",
                    "superseded": "2014-06-13T12:30:45+00:00",
                    "unavailable": "2014-06-14T12:30:45+00:00",
                    "validityBegins": "2014-06-15T12:30:45+00:00",
                    "validityExpires": "2014-06-16T12:30:45+00:00",
                },
            ),
        ],
    )
    def test_unstructure(self, value: Dates, expected: dict):
        """Can convert a Dates container to plain types."""
        result = value.unstructure()

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a Dates instance into plain types."""
        value = Dates(last_update=Date(date=date(2014, 1, 1), precision=DatePrecisionCode.YEAR))
        expected = {"lastUpdate": "2014"}

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Dates, lambda d: d.unstructure())
        result = converter.unstructure(value)

        assert result == expected


class TestIdentifier:
    """Test Identifier element."""

    @pytest.mark.parametrize(
        "values", [{"identifier": "x", "namespace": "x"}, {"identifier": "x", "href": "x", "namespace": "x"}]
    )
    def test_init(self, values: dict):
        """Can create an Identifier element from directly assigned properties."""
        expected = "x"
        identifier = Identifier(**values)

        assert identifier.identifier == expected
        assert identifier.namespace == expected

        if "href" in values:
            assert identifier.href == expected
        else:
            assert identifier.href is None


class TestIdentifiers:
    """Test Identifiers container."""

    def test_init(self):
        """Can create an Identifiers container from directly assigned properties."""
        expected = Identifier(identifier="x", href="x", namespace="x")
        identifiers = Identifiers([expected])

        assert len(identifiers) == 1
        assert identifiers[0] == expected

    def test_filter_namespace(self):
        """Can filter identifiers by a namespace."""
        identifier = Identifier(identifier="x", href="x", namespace="a")
        identifiers = Identifiers([identifier, Identifier(identifier="x", href="x", namespace="b")])
        expected = Identifiers([identifier])

        result = identifiers.filter(identifier.namespace)
        assert result == expected

    def test_structure(self):
        """Can create an Identifiers container by converting a list of plain types."""
        expected = Identifiers([Identifier(identifier="x", href="x", namespace="x")])
        result = Identifiers.structure([{"identifier": "x", "href": "x", "namespace": "x"}])
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create an Identifiers instance from plain types."""
        value = [{"identifier": "x", "href": "x", "namespace": "x"}]
        expected = Identifiers([Identifier(identifier="x", href="x", namespace="x")])

        converter = cattrs.Converter()
        converter.register_structure_hook(Identifiers, lambda d, t: Identifiers.structure(d))
        result = converter.structure(value, Identifiers)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert an Identifiers instance into plain types."""
        value = Identifiers([Identifier(identifier="x", href="x", namespace="x")])
        expected = [{"identifier": "x", "href": "x", "namespace": "x"}]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Identifiers, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected


class TestOnlineResource:
    """Test OnlineResource element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"href": "x", "function": OnlineResourceFunctionCode.DOWNLOAD},
            {
                "href": "x",
                "function": OnlineResourceFunctionCode.DOWNLOAD,
                "title": "x",
                "description": "x",
                "protocol": "x",
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create an OnlineResource element from directly assigned properties."""
        expected_str = "x"
        expected_enum = OnlineResourceFunctionCode.DOWNLOAD
        online_resource = OnlineResource(**values)

        assert online_resource.href == expected_str
        assert online_resource.function == expected_enum

        if "title" in values:
            assert online_resource.title == expected_str
        else:
            assert online_resource.title is None

        if "description" in values:
            assert online_resource.description == expected_str
        else:
            assert online_resource.description is None

        if "protocol" in values:
            assert online_resource.protocol == expected_str
        else:
            assert online_resource.protocol is None


class TestSeries:
    """Test descriptive Series element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"name": "x", "edition": "x"},
            {"name": "x"},
            {"edition": "x"},
            {},
        ],
    )
    def test_init(self, values: dict):
        """Can create a Series element from directly assigned properties."""
        series = Series(**values)

        if "name" in values:
            assert series.name == values["name"]
        else:
            assert series.name is None

        if "edition" in values:
            assert series.edition == values["edition"]
        else:
            assert series.edition is None
