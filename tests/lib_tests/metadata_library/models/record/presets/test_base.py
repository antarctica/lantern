from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, date, datetime

import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.elements.identification import Identification
from lantern.lib.metadata_library.models.record.enums import (
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.base import RecordMagicDiscoveryV1

EXPECTED_POC = Contact(
    organisation=ContactIdentity(
        name="Mapping and Geographic Information Centre, British Antarctic Survey",
        href="https://ror.org/01rhff309",
        title="ror",
    ),
    phone="+44 (0)1223 221400",
    email="magic@bas.ac.uk",
    address=Address(
        delivery_point="British Antarctic Survey, High Cross, Madingley Road",
        city="Cambridge",
        administrative_area="Cambridgeshire",
        postal_code="CB3 0ET",
        country="United Kingdom",
    ),
    online_resource=OnlineResource(
        href="https://www.bas.ac.uk/teams/magic",
        title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
        description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.POINT_OF_CONTACT},
)

EXPECTED_PUBLISHER = deepcopy(EXPECTED_POC)
EXPECTED_PUBLISHER.role = {ContactRoleCode.PUBLISHER}
EXPECTED_PROFILE = DomainConsistency(
    specification=Citation(
        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
        dates=Dates(publication=Date(date=date(2024, 11, 1))),
        edition="1",
        contacts=Contacts([EXPECTED_PUBLISHER]),
    ),
    explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
    result=True,
)


class TestRecordMagicDiscoveryV1:
    """Test record with magic discovery v1 profile."""

    def test_init(self):
        """Can create a minimal Record element from directly assigned properties."""
        date_stamp = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.DATASET
        value = "x"
        record = RecordMagicDiscoveryV1(
            file_identifier="x",
            hierarchy_level=hierarchy_level,
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_stamp))),
        )

        assert isinstance(record, RecordMagicDiscoveryV1)

    def test_loads(self, fx_record_config_minimal_magic_preset: dict):
        """Can create a minimal Record from a JSON serialised dict."""
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)
        assert isinstance(record, RecordMagicDiscoveryV1)

    def test_metadata_contact(self, fx_record_config_minimal_magic_preset: dict):
        """Includes MAGIC as metadata point of contact."""
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)
        assert record.metadata.contacts == [EXPECTED_POC]

    def test_metadata_datestamp(self):
        """Metadata date stamp can be specified."""
        date_stamp = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.DATASET
        value = "x"
        record = RecordMagicDiscoveryV1(
            file_identifier="x",
            hierarchy_level=hierarchy_level,
            date_stamp=date_stamp,
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_stamp))),
        )

        assert record.metadata.contacts == [EXPECTED_POC]

    def test_catalogue_identifier(self, fx_record_config_minimal_magic_preset: dict):
        """Includes a catalogue identifier."""
        expected = Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)

        assert expected in record.identification.identifiers

    def test_catalogue_identifier_existing(self, fx_record_config_minimal_magic_preset: dict):
        """Does not include a duplicate catalogue identifier if already in record."""
        expected = Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")
        # noinspection PyTypeChecker
        fx_record_config_minimal_magic_preset["identification"]["identifiers"] = [asdict(expected)]
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)

        matches = [i for i in record.identification.identifiers if i == expected]
        assert len(matches) == 1

    def test_poc(self, fx_record_config_minimal_magic_preset: dict):
        """Includes MAGIC as a point of contact."""
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)
        assert record.identification.contacts == [EXPECTED_POC]

    @pytest.mark.parametrize(
        "contacts",
        [
            # exact match
            [
                {
                    "address": {
                        "administrative_area": "Cambridgeshire",
                        "city": "Cambridge",
                        "country": "United Kingdom",
                        "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                        "postal_code": "CB3 0ET",
                    },
                    "email": "magic@bas.ac.uk",
                    "online_resource": {
                        "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                        "function": "information",
                        "href": "https://www.bas.ac.uk/teams/magic",
                        "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                    },
                    "organisation": {
                        "href": "https://ror.org/01rhff309",
                        "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                        "title": "ror",
                    },
                    "phone": "+44 (0)1223 221400",
                    "role": ["pointOfContact"],
                },
            ],
            # overlapping roles
            [
                {
                    "address": {
                        "administrative_area": "Cambridgeshire",
                        "city": "Cambridge",
                        "country": "United Kingdom",
                        "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                        "postal_code": "CB3 0ET",
                    },
                    "email": "magic@bas.ac.uk",
                    "online_resource": {
                        "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                        "function": "information",
                        "href": "https://www.bas.ac.uk/teams/magic",
                        "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                    },
                    "organisation": {
                        "href": "https://ror.org/01rhff309",
                        "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                        "title": "ror",
                    },
                    "phone": "+44 (0)1223 221400",
                    "role": ["pointOfContact", "publisher"],
                },
            ],
            # non-overlapping roles
            [
                {
                    "address": {
                        "administrative_area": "Cambridgeshire",
                        "city": "Cambridge",
                        "country": "United Kingdom",
                        "delivery_point": "British Antarctic Survey, High Cross, Madingley Road",
                        "postal_code": "CB3 0ET",
                    },
                    "email": "magic@bas.ac.uk",
                    "online_resource": {
                        "description": "General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
                        "function": "information",
                        "href": "https://www.bas.ac.uk/teams/magic",
                        "title": "Mapping and Geographic Information Centre (MAGIC) - BAS public website",
                    },
                    "organisation": {
                        "href": "https://ror.org/01rhff309",
                        "name": "Mapping and Geographic Information Centre, British Antarctic Survey",
                        "title": "ror",
                    },
                    "phone": "+44 (0)1223 221400",
                    "role": ["publisher"],
                },
            ],
            # non-match
            [
                {
                    "organisation": {
                        "name": "x",
                    },
                    "role": ["pointOfContact"],
                },
            ],
        ],
    )
    def test_poc_existing(self, fx_record_config_minimal_magic_preset: dict, contacts: list[dict]):
        """Includes MAGIC as a point of contact."""
        fx_record_config_minimal_magic_preset["identification"]["contacts"] = contacts
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)

        # noinspection PyUnresolvedReferences
        matches = [
            contact
            for contact in record.identification.contacts
            if contact.organisation.name == "Mapping and Geographic Information Centre, British Antarctic Survey"
        ]
        assert len(matches) == 1
        # noinspection PyUnresolvedReferences
        assert ContactRoleCode.POINT_OF_CONTACT in list(matches[0].role)

    def test_profile(self, fx_record_config_minimal_magic_preset: dict):
        """Includes domain consistency element for profile."""
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)
        assert EXPECTED_PROFILE in record.data_quality.domain_consistency

    def test_catalogue_profile_existing(self, fx_record_config_minimal_magic_preset: dict):
        """Does not include a duplicate profile if already in record."""
        profile = {
            "specification": {
                "title": {
                    "value": "British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                    "href": "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
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
        fx_record_config_minimal_magic_preset["identification"]["domain_consistency"] = [profile]
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)

        matches = [p for p in record.data_quality.domain_consistency if p == EXPECTED_PROFILE]
        assert len(matches) == 1

    def test_lineage_statement(self, fx_record_config_minimal_magic_preset: dict):
        """Can set a lineage statement."""
        expected = "x"
        fx_record_config_minimal_magic_preset["identification"]["lineage"] = {"statement": expected}
        record = RecordMagicDiscoveryV1.loads(fx_record_config_minimal_magic_preset)

        assert record.data_quality.lineage.statement == expected

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "dataset",
                    "metadata": {
                        "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
                        "date_stamp": "2014-06-30",
                    },
                    "identification": {
                        "title": {"value": "x"},
                        "dates": {"creation": "2014-06-30"},
                        "abstract": "x",
                    },
                },
                "British Antarctic Survey (?year). _x_ (Version ?version) [Dataset]. British Antarctic Survey Mapping and Geographic Information Centre. [https://data.bas.ac.uk/items/x](https://data.bas.ac.uk/items/x).",
            ),
            (
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "dataset",
                    "metadata": {
                        "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
                        "date_stamp": "2014-06-30",
                    },
                    "identification": {
                        "title": {"value": "x"},
                        "dates": {"creation": "2014-06-30", "publication": "2014-06-30"},
                        "edition": "x",
                        "abstract": "x",
                    },
                },
                "British Antarctic Survey (2014). _x_ (Version x) [Dataset]. British Antarctic Survey Mapping and Geographic Information Centre. [https://data.bas.ac.uk/items/x](https://data.bas.ac.uk/items/x).",
            ),
        ],
    )
    def test_set_citation(self, values: dict, expected: str):
        """Can set citation from record."""
        record = RecordMagicDiscoveryV1.loads(values)
        record.set_citation()

        assert record.identification.other_citation_details == expected
