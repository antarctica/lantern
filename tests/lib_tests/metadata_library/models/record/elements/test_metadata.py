from datetime import UTC, date, datetime

import cattrs
import pytest

from lantern.lib.metadata_library.models.record.elements.common import Contact, ContactIdentity, Contacts
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata, MetadataStandard
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestMetadata:
    """Test Metadata element."""

    @pytest.mark.parametrize(
        ("values", "expected_date"),
        [
            (
                {
                    "contacts": [
                        Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})
                    ]
                },
                datetime.now(tz=UTC).date(),
            ),
            (
                {
                    "contacts": [
                        Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})
                    ],
                    "date_stamp": None,
                },
                datetime.now(tz=UTC).date(),
            ),
            (
                {
                    "contacts": [
                        Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})
                    ],
                    "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date(),
                },
                datetime(2014, 6, 30, tzinfo=UTC).date(),
            ),
        ],
    )
    def test_init(self, values: dict, expected_date: datetime):
        """Can create a Metadata element from directly assigned properties."""
        expected_character = "utf8"
        expected_language = "eng"
        metadata = Metadata(**values)

        assert metadata.character_set == expected_character
        assert metadata.language == expected_language
        assert len(metadata.contacts) > 0
        assert metadata.date_stamp is not None
        assert metadata.date_stamp == expected_date
        assert isinstance(metadata.metadata_standard, MetadataStandard)

    def test_invalid_contacts(self):
        """Can't create a Metadata element without any contacts."""
        with pytest.raises(ValueError, match=r"At least one contact is required"):
            Metadata(contacts=Contacts([]))

    def test_structure_cattrs(self):
        """Can use Cattrs to create a Metadata instance from plain types."""
        expected_date = date(2014, 6, 30)
        expected_enum = ContactRoleCode.POINT_OF_CONTACT
        value = {
            "contacts": [{"organisation": {"name": "x"}, "role": [expected_enum.value]}],
            "date_stamp": expected_date.isoformat(),
        }
        expected = Metadata(
            contacts=Contacts([Contact(organisation=ContactIdentity(name="x"), role={expected_enum})]),
            date_stamp=expected_date,
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Metadata, lambda d, t: Metadata.structure(d))
        result = converter.structure(value, Metadata)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a Metadata instance into plain types."""
        expected_date = date(2014, 6, 30)
        expected_enum = ContactRoleCode.POINT_OF_CONTACT
        value = Metadata(
            contacts=Contacts([Contact(organisation=ContactIdentity(name="x"), role={expected_enum})]),
            date_stamp=expected_date,
        )
        expected = {
            "contacts": [{"organisation": {"name": "x"}, "role": [expected_enum.value]}],
            "date_stamp": expected_date.isoformat(),
            "character_set": "utf8",
            "language": "eng",
            "metadata_standard": {
                "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                "version": "ISO 19115-2:2009(E)",
            },
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Metadata, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected


class TestMetadataStandard:
    """Test MetadataStandard element."""

    def test_init(self):
        """Can create a MetadataStandard element."""
        expected_name: str = (
            "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data"
        )
        expected_version: str = "ISO 19115-2:2009(E)"
        standard = MetadataStandard()

        assert standard.name == expected_name
        assert standard.version == expected_version
