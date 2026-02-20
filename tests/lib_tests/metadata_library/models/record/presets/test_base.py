from dataclasses import asdict
from datetime import UTC, date, datetime

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata

from lantern.lib.metadata_library.models.record.elements.common import (
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, DomainConsistency
from lantern.lib.metadata_library.models.record.elements.identification import Identification
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.lib.metadata_library.models.record.presets.base import RecordMagic
from lantern.lib.metadata_library.models.record.presets.contacts import UKRI_RIGHTS_HOLDER, make_magic_role
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict

EXPECTED_POC = make_magic_role({ContactRoleCode.POINT_OF_CONTACT})
EXPECTED_PUBLISHER = make_magic_role({ContactRoleCode.PUBLISHER})

# Conformance presets are deliberately not used here to ensure these presets are actually correct.
EXPECTED_PROFILE_DISCOVERY = DomainConsistency(
    specification=Citation(
        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/",
        dates=Dates(publication=Date(date=date(2025, 11, 24))),
        edition="2",
        contacts=Contacts([EXPECTED_PUBLISHER]),
    ),
    explanation="Resource within scope of the British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
    result=True,
)
EXPECTED_PROFILE_ADMINISTRATION = DomainConsistency(
    specification=Citation(
        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Administration Metadata Profile",
        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-administration/v1/",
        dates=Dates(publication=Date(date=date(2025, 10, 22))),
        edition="1",
        contacts=Contacts([EXPECTED_PUBLISHER]),
    ),
    explanation="Resource within scope of the British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Administration Metadata Profile.",
    result=True,
)


class TestRecordMagic:
    """Test record with magic profiles and defaults."""

    def test_init(self):
        """Can create a minimal Record element from directly assigned properties."""
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.DATASET
        value = "x"
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=hierarchy_level,
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_))),
        )

        assert isinstance(record, RecordMagic)

    def test_no_file_identifier(self):
        """Cannot create a Record without a file identifier."""
        with pytest.raises(ValueError, match=r"Records require a file_identifier."):
            _ = RecordMagic(
                hierarchy_level=HierarchyLevelCode.PRODUCT,
                identification=Identification(
                    title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
                ),
            )

    def test_loads(self, fx_lib_record_config_min_magic: dict):
        """Can create a minimal Record from a JSON serialised dict."""
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert isinstance(record, RecordMagic)

    def test_metadata_contact(self, fx_lib_record_config_min_magic: dict):
        """Can include MAGIC as metadata point of contact."""
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert record.metadata.contacts == [EXPECTED_POC]

    def test_metadata_datestamp(self):
        """Can specify a metadata date stamp."""
        expected = datetime(2014, 6, 30, tzinfo=UTC).date()
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.DATASET
        value = "x"
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=hierarchy_level,
            date_stamp=expected,
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_))),
        )

        assert record.metadata.date_stamp == expected

    def test_catalogue_identifier(self, fx_lib_record_config_min_magic: dict):
        """Can include an identifier using the catalogue namespace."""
        expected = Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")
        record = RecordMagic.loads(fx_lib_record_config_min_magic)

        assert expected in record.identification.identifiers

    def test_catalogue_identifier_existing(self, fx_lib_record_config_min_magic: dict):
        """Can include a catalogue identifier without creating duplicates where already in the record."""
        expected = Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")
        # noinspection PyTypeChecker
        fx_lib_record_config_min_magic["identification"]["identifiers"] = [asdict(expected)]
        record = RecordMagic.loads(fx_lib_record_config_min_magic)

        matches = [i for i in record.identification.identifiers if i == expected]
        assert len(matches) == 1

    def test_poc(self, fx_lib_record_config_min_magic: dict):
        """Can include MAGIC as a point of contact."""
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert EXPECTED_POC in record.identification.contacts

    def test_rights_holder(self, fx_lib_record_config_min_magic: dict):
        """Can include UKRI as a default copyright holder contact."""
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert UKRI_RIGHTS_HOLDER in record.identification.contacts

    @pytest.mark.parametrize(
        "contacts",
        [
            # exact match
            Contacts([make_magic_role({ContactRoleCode.POINT_OF_CONTACT})]),
            # overlapping roles
            Contacts([make_magic_role({ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER})]),
            # non-overlapping roles
            Contacts([make_magic_role({ContactRoleCode.PUBLISHER})]),
            # non-match
            Contacts([Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})]),
        ],
    )
    def test_poc_existing(self, fx_lib_record_config_min_magic: dict, contacts: Contacts):
        """Can include MAGIC as a contact without creating duplicates where already in the record."""
        fx_lib_record_config_min_magic["identification"]["contacts"] = contacts.unstructure()
        record = RecordMagic.loads(fx_lib_record_config_min_magic)

        # noinspection PyUnresolvedReferences
        matches = [
            contact
            for contact in record.identification.contacts
            if contact.organisation.name == "Mapping and Geographic Information Centre, British Antarctic Survey"
        ]
        assert len(matches) == 1
        # noinspection PyUnresolvedReferences
        assert ContactRoleCode.POINT_OF_CONTACT in list(matches[0].role)

    def test_profile(self, fx_lib_record_config_min_magic: dict):
        """
        Can include domain consistency element for discovery profile.

        Ensure the MAGIC Administration profile is not included (as admin metadata is not included).
        """
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert EXPECTED_PROFILE_DISCOVERY in record.data_quality.domain_consistency
        assert EXPECTED_PROFILE_ADMINISTRATION not in record.data_quality.domain_consistency

    @pytest.mark.parametrize("profile_class", [EXPECTED_PROFILE_DISCOVERY, EXPECTED_PROFILE_ADMINISTRATION])
    def test_catalogue_profile_existing(self, fx_lib_record_config_min_magic: dict, profile_class: DomainConsistency):
        """Can include profiles without creating duplicates where they are already in record."""
        dq = clean_dict(DataQuality(domain_consistency=[profile_class]).unstructure()["domain_consistency"][0])
        fx_lib_record_config_min_magic["identification"]["domain_consistency"] = [dq]
        record = RecordMagic.loads(fx_lib_record_config_min_magic)

        matches = [p for p in record.data_quality.domain_consistency if p == profile_class]
        assert len(matches) == 1

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
    def test_set_default_citation(self, values: dict, expected: str):
        """
        Can get default citation based on record.

        Additional unit tests for `make_magic_citation()` are performed elsewhere.
        """
        record = RecordMagic.loads(values)

        assert record.identification.other_citation_details == expected

    @pytest.mark.cov()
    def test_set_citation_override(self, fx_lib_record_config_min_magic: dict):
        """Can get non-default citation if a value is set in the record."""
        expected = "x"

        # via direct properties
        date_stamp = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.DATASET,
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=date_stamp)), other_citation_details=expected
            ),
        )
        assert record.identification.other_citation_details == expected

        # via loading from dict
        fx_lib_record_config_min_magic["identification"]["other_citation_details"] = expected
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert record.identification.other_citation_details == expected

    def test_admin_meta(self, fx_admin_meta_keys: AdministrationKeys, fx_admin_meta_element: AdministrationMetadata):
        """
        Can create a minimal Record element with administration metadata from directly assigned properties.

        Ensure the MAGIC Administration profile is included.
        """
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.DATASET,
            identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=date_))),
            admin_keys=fx_admin_meta_keys,
            admin_meta=fx_admin_meta_element,
        )

        assert isinstance(record, RecordMagic)
        result = get_admin(keys=fx_admin_meta_keys, record=record)
        assert isinstance(result, AdministrationMetadata)
        assert EXPECTED_PROFILE_ADMINISTRATION in record.data_quality.domain_consistency
