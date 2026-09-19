import cattrs

from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.contacts import make_bas_role, make_magic_role
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestMakeBasRole:
    """Tests fir `make_bas_role()` preset."""

    def test_bas(self):
        """Can get a generic BAS contact element."""
        expected: dict = {
            "organisation": {
                "name": "British Antarctic Survey",
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
            "online_resource": {
                "href": "https://www.bas.ac.uk",
                "title": "British Antarctic Survey public website",
                "description": "General information about the British Antarctic Survey (BAS).",
                "function": "information",
            },
            "role": {"pointOfContact"},
        }

        contact = make_bas_role(roles={ContactRoleCode.POINT_OF_CONTACT})
        converter = cattrs.Converter()
        result = clean_dict(converter.unstructure(contact))
        assert result == expected

    def test_team(self):
        """Can get a contact element for a BAS team."""
        expected: dict = {
            "organisation": {
                "name": "x, British Antarctic Survey",
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
            "email": "x",
            "online_resource": {
                "href": "x",
                "title": "x - BAS public website",
                "description": "General information about the x from the British Antarctic Survey (BAS) public website.",
                "function": "information",
            },
            "role": {"pointOfContact"},
        }

        contact = make_bas_role(
            roles={ContactRoleCode.POINT_OF_CONTACT}, team_name="x", team_email="x", team_url="x", team_url_title="x"
        )
        converter = cattrs.Converter()
        result = clean_dict(converter.unstructure(contact))
        assert result == expected


class TestMakeMagicRole:
    """Tests for `make_magic_role()` present."""

    def test_default(self):
        """Can get contact element consistent with reference value."""
        # from https://github.com/antarctica/metadata-library/blob/v0.15.1/tests/resources/configs/magic-discovery-profile/minimal_product_v1.json#L6
        expected: dict = {
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
            "role": {"pointOfContact"},
        }

        contact = make_magic_role(roles={ContactRoleCode.POINT_OF_CONTACT})
        converter = cattrs.Converter()
        result = clean_dict(converter.unstructure(contact))
        assert result == expected

    def test_roles(self):
        """Can get contact element with configured roles."""
        expected = {ContactRoleCode.AUTHOR, ContactRoleCode.EDITOR}
        result = make_magic_role(roles=expected)
        assert set(result.role) == set(expected)  # order doesn't matter
