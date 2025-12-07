import cattrs

from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_DISCOVERY_V1
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict


class TestMagicProfileV1:
    """Test `MAGIC_PROFILE_V1` preset constant."""

    def test_magic_profile_v1(self):
        """Can get domain consistency element consistent with reference value."""
        # from https://github.com/antarctica/metadata-library/blob/v0.16.0/tests/resources/configs/magic-discovery-profile/minimal_product_v1_alt.json#L114
        expected = {
            "specification": {
                "title": {
                    "value": "British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                    "href": "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v1/",
                },
                "dates": {"publication": "2024-11-01"},
                "edition": "1",
                "contact": {
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
                    "role": ["publisher"],
                },
            },
            "explanation": "Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
            "result": True,
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(DataQuality, lambda d: d.unstructure())
        container = DataQuality(domain_consistency=[MAGIC_DISCOVERY_V1])
        result = clean_dict(converter.unstructure(container))["domain_consistency"][0]

        assert result == expected
