import cattrs

from lantern.lib.metadata_library.models.record import clean_dict
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role


class TestMakeMagicRole:
    """Tests for `make_magic_role()` present."""

    def test_default(self):
        """Can get contact element consistent with reference value."""
        # from https://github.com/antarctica/metadata-library/blob/v0.15.1/tests/resources/configs/magic-discovery-profile/minimal_product_v1.json#L6
        expected = {
            "organisation": {
                "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                "href": "https://ror.org/01rhff309",
                "title": "ror",
            },
            "phone": "+44 (0)1223 221400",
            "address": {
                "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                "city": "Cambridge",
                "administrative_area": "Cambridgeshire",
                "postal_code": "CB3 0ET",
                "country": "United Kingdom",
            },
            "email": "magic@bas.ac.uk",
            "online_resource": {
                "href": "https://www.bas.ac.uk/teams/magic",
                "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                "function": "information",
            },
            "role": ["pointOfContact"],
        }

        contact = make_magic_role(roles=[ContactRoleCode.POINT_OF_CONTACT])
        converter = cattrs.Converter()
        result = clean_dict(converter.unstructure(contact))

        assert result == expected

    def test_roles(self):
        """Can get contact element with configured roles."""
        expected = [ContactRoleCode.AUTHOR, ContactRoleCode.EDITOR]
        result = make_magic_role(roles=expected)
        assert set(result.role) == set(expected)  # order doesn't matter
