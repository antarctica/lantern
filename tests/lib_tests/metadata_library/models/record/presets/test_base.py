from dataclasses import asdict
from datetime import UTC, date, datetime

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import set_admin as set_admin_dict

from lantern.lib.metadata_library.models.record.elements.common import (
    Citation,
    Constraint,
    Constraints,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Maintenance,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import (
    DataQuality,
    DomainConsistencies,
    DomainConsistency,
    Lineage,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    BoundingBox,
    Extent,
    ExtentGeographic,
    Extents,
    Identification,
)
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.base import RecordMagic, RecordMagicOpen
from lantern.lib.metadata_library.models.record.presets.contacts import UKRI_RIGHTS_HOLDER, make_magic_role
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict

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
        """Can create a minimal Record from directly assigned properties."""
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        value = "x"
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_))),
        )

        assert isinstance(record, RecordMagic)

    def test_no_file_identifier(self):
        """Cannot create a Record without a file identifier."""
        with pytest.raises(TypeError, match=r"Records require a file_identifier."):
            _ = RecordMagic(
                hierarchy_level=HierarchyLevelCode.PRODUCT,
                identification=Identification(
                    title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
                ),
            )

    @pytest.mark.cov()
    def test_no_file_identifier_set_cat_identifier(self):
        """Cannot set catalogue identifier in a Record without a file identifier."""
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
            ),
        )
        record.file_identifier = None

        with pytest.raises(TypeError):
            record._set_cat_identifier()

    def test_loads(self, fx_lib_record_config_min_magic: dict):
        """Can create a minimal Record from a JSON serialised dict."""
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert isinstance(record, RecordMagic)

    def test_metadata_constraints(self, fx_lib_record_config_min_magic: dict):
        """Can include default metadata constraints."""
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        results = record.metadata.constraints.filter(
            types=ConstraintTypeCode.ACCESS, restrictions=ConstraintRestrictionCode.UNRESTRICTED
        )
        assert len(results) == 1

    @pytest.mark.parametrize("has_frequency", [False, True])
    @pytest.mark.parametrize("has_progress", [False, True])
    def test_metadata_maintenance(self, has_frequency: bool, has_progress: bool):
        """
        Can include default metadata maintenace using a non-standard parameter.

        To avoid needing to specify a minimal Metadata element.
        """
        default_frequency = MaintenanceFrequencyCode.AS_NEEDED
        active_frequency = MaintenanceFrequencyCode.NOT_PLANNED
        default_progress = ProgressCode.COMPLETED
        active_progress = ProgressCode.ON_GOING

        maintenance = Maintenance(
            maintenance_frequency=default_frequency if not has_frequency else active_frequency,
            progress=default_progress if not has_progress else active_progress,
        )
        exp_frequency = active_frequency if has_frequency else default_frequency
        exp_progress = active_progress if has_progress else default_progress

        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            meta_maintenance=maintenance if has_frequency or has_progress else None,
            identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=date_))),
        )
        assert record.metadata.maintenance.maintenance_frequency == exp_frequency
        assert record.metadata.maintenance.progress == exp_progress

    def test_metadata_contact(self, fx_lib_record_config_min_magic: dict):
        """Can include MAGIC as metadata point of contact."""
        expected = make_magic_role({ContactRoleCode.POINT_OF_CONTACT})
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert record.metadata.contacts == [expected]

    def test_metadata_date_stamp(self):
        """
        Can specify a metadata date stamp using a non-standard parameter.

        To avoid needing to specify a minimal Metadata element.
        """
        expected = datetime(2014, 6, 30, tzinfo=UTC).date()
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.PRODUCT
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=hierarchy_level,
            meta_date_stamp=expected,
            identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=date_))),
        )

        assert record.metadata.date_stamp == expected

    @pytest.mark.parametrize("has_meta", [False, True])
    def test_metadata(self, fx_lib_record_config_min_magic: dict, has_meta: bool):
        """
        Can include metadata element overriding some class defaults.

        Date stamp and maintenance info. Contacts, constraints, etc. are hard-coded.
        """
        expected = "2020-04-20" if has_meta else "2014-06-30"
        if has_meta:
            fx_lib_record_config_min_magic["metadata"]["date_stamp"] = expected

        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert record.metadata.date_stamp.isoformat() == expected

    def test_catalogue_identifier(self, fx_lib_record_config_min_magic: dict):
        """Can include an identifier using the catalogue namespace."""
        expected = Identifier(
            identifier="x", href="https://lantern.data.bas.ac.uk/items/x", namespace="lantern.data.bas.ac.uk"
        )
        record = RecordMagic.loads(fx_lib_record_config_min_magic)

        assert expected in record.identification.identifiers

    def test_catalogue_identifier_existing(self, fx_lib_record_config_min_magic: dict):
        """Can include a catalogue identifier without creating duplicates where already in the record."""
        expected = Identifier(
            identifier="x", href="https://lantern.data.bas.ac.uk/items/x", namespace="lantern.data.bas.ac.uk"
        )
        fx_lib_record_config_min_magic["identification"]["identifiers"] = [asdict(expected)]
        record = RecordMagic.loads(fx_lib_record_config_min_magic)

        matches = [i for i in record.identification.identifiers if i == expected]
        assert len(matches) == 1

    def test_contact(self, fx_lib_record_config_min_magic: dict):
        """Can include MAGIC as a point of contact and publisher."""
        expected = make_magic_role({ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER})
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert expected in record.identification.contacts

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
        dq = clean_dict(
            DataQuality(domain_consistency=DomainConsistencies([profile_class])).unstructure()["domain_consistency"][0]
        )
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
                    "hierarchy_level": "product",
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
                "British Antarctic Survey (?year). _x_ (Version ?version) [Product]. British Antarctic Survey Mapping and Geographic Information Centre. [https://data.bas.ac.uk/items/x](https://data.bas.ac.uk/items/x).",
            ),
            (
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "product",
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
                "British Antarctic Survey (2014). _x_ (Version x) [Product]. British Antarctic Survey Mapping and Geographic Information Centre. [https://data.bas.ac.uk/items/x](https://data.bas.ac.uk/items/x).",
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
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=date_stamp)), other_citation_details=expected
            ),
        )
        assert record.identification.other_citation_details == expected

        # via loading from dict
        fx_lib_record_config_min_magic["identification"]["other_citation_details"] = expected
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert record.identification.other_citation_details == expected

    @pytest.mark.parametrize("has_frequency", [False, True])
    @pytest.mark.parametrize("has_progress", [False, True])
    def test_maintenance(self, fx_lib_record_config_min_magic: dict, has_frequency: bool, has_progress: bool):
        """Can include default resource maintenace."""
        default_frequency = MaintenanceFrequencyCode.AS_NEEDED
        active_frequency = MaintenanceFrequencyCode.NOT_PLANNED
        default_progress = ProgressCode.COMPLETED
        active_progress = ProgressCode.ON_GOING

        maintenance = Maintenance(
            maintenance_frequency=default_frequency if not has_frequency else active_frequency,
            progress=default_progress if not has_progress else active_progress,
        )
        fx_lib_record_config_min_magic["identification"]["maintenance"] = {
            "maintenance_frequency": default_frequency if not has_frequency else active_frequency,
            "progress": default_progress if not has_progress else active_progress,
        }
        exp_frequency = active_frequency if has_frequency else default_frequency
        exp_progress = active_progress if has_progress else default_progress

        # via direct properties
        date_stamp = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x",
                abstract="x",
                dates=Dates(creation=Date(date=date_stamp)),
                maintenance=maintenance if has_frequency or has_progress else None,
            ),
        )
        assert record.identification.maintenance.maintenance_frequency == exp_frequency
        assert record.identification.maintenance.progress == exp_progress

        # via loading from dict
        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert record.identification.maintenance.maintenance_frequency == exp_frequency
        assert record.identification.maintenance.progress == exp_progress

    def test_admin(self, fx_admin_meta_keys: AdministrationKeys, fx_admin_meta_element: AdministrationMetadata):
        """
        Can create a minimal Record element with administration metadata from directly assigned properties.

        Ensure the MAGIC Administration profile is included.
        """
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=date_))),
            admin_keys=fx_admin_meta_keys,
            admin_meta=fx_admin_meta_element,
        )

        assert isinstance(record, RecordMagic)
        result = get_admin(keys=fx_admin_meta_keys, record=record)
        assert isinstance(result, AdministrationMetadata)
        assert EXPECTED_PROFILE_ADMINISTRATION in record.data_quality.domain_consistency

    @pytest.mark.cov()
    def test_admin_loads(self, fx_admin_meta_keys: AdministrationKeys, fx_lib_record_config_min_magic: dict):
        """Can create a minimal Record with administration metadata from a JSON serialised dict."""
        set_admin_dict(
            keys=fx_admin_meta_keys,
            config=fx_lib_record_config_min_magic,
            admin_meta=AdministrationMetadata(id=fx_lib_record_config_min_magic["file_identifier"]),
        )

        record = RecordMagic.loads(fx_lib_record_config_min_magic)
        assert isinstance(record, RecordMagic)
        result = get_admin(keys=fx_admin_meta_keys, record=record)
        assert isinstance(result, AdministrationMetadata)

    @pytest.mark.cov()
    def test_valid(self):
        """Can create a minimal Record, valid against catalogue requirements and profiles."""
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagic(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x",
                abstract="x",
                dates=Dates(creation=Date(date=date_)),
                edition="x",
                constraints=Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
                        ),
                        Constraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE),
                    ]
                ),
                extents=Extents(
                    [
                        Extent(
                            identifier="bounding",
                            geographic=ExtentGeographic(
                                bounding_box=BoundingBox(
                                    west_longitude=0, east_longitude=0, south_latitude=0, north_latitude=0
                                )
                            ),
                        )
                    ]
                ),
            ),
            data_quality=DataQuality(lineage=Lineage(statement="x")),
        )

        assert isinstance(record, RecordMagic)
        record.validate()


class TestRecordMagicOpen:
    """Test unrestricted record with magic profiles and defaults."""

    @staticmethod
    def _assert_defaults(keys: AdministrationKeys, record: RecordMagicOpen) -> None:
        assert isinstance(record, RecordMagicOpen)

        # access constraints
        metadata_access = record.metadata.constraints.filter(
            types=ConstraintTypeCode.ACCESS, restrictions=ConstraintRestrictionCode.UNRESTRICTED
        )
        assert len(metadata_access) == 1
        resource_access = record.metadata.constraints.filter(
            types=ConstraintTypeCode.ACCESS, restrictions=ConstraintRestrictionCode.UNRESTRICTED
        )

        # usage constraints
        assert len(resource_access) == 1
        metadata_licence = record.metadata.constraints.filter(
            types=ConstraintTypeCode.USAGE, restrictions=ConstraintRestrictionCode.LICENSE
        )[0]
        assert metadata_licence.href == "https://creativecommons.org/licenses/by-nd/4.0/"
        resource_licence = record.identification.constraints.filter(
            types=ConstraintTypeCode.USAGE, restrictions=ConstraintRestrictionCode.LICENSE
        )[0]
        assert resource_licence.href == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

        # admin metadata permissions
        admin_meta = get_admin(keys=keys, record=record)
        assert isinstance(admin_meta, AdministrationMetadata)
        metadata_permission = admin_meta.metadata_permissions[0]
        assert metadata_permission.directory == "*"
        assert metadata_permission.group == "*"
        resource_permission = admin_meta.resource_permissions[0]
        assert resource_permission.directory == "*"
        assert resource_permission.group == "*"

    def test_init(self, fx_admin_meta_keys: AdministrationKeys):
        """Can create a minimal unrestricted Record element from directly assigned properties."""
        record = RecordMagicOpen(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
            ),
            admin_keys=fx_admin_meta_keys,
        )

        self._assert_defaults(keys=fx_admin_meta_keys, record=record)

    def test_init_no_keys(self, fx_admin_meta_keys: AdministrationKeys):
        """Cannot create an unrestricted Record without admin metadata keys."""
        with pytest.raises(TypeError, match=r"Open records require administration metadata keys."):
            _ = RecordMagicOpen(
                file_identifier="x",
                hierarchy_level=HierarchyLevelCode.PRODUCT,
                identification=Identification(
                    title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
                ),
            )

    @pytest.mark.cov()
    def test_no_file_identifier_set_open_access(self, fx_admin_meta_keys: AdministrationKeys):
        """Cannot set catalogue identifier in a Record without a file identifier."""
        record = RecordMagicOpen(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
            ),
            admin_keys=fx_admin_meta_keys,
        )
        record.file_identifier = None

        with pytest.raises(TypeError):
            record._set_open_access(admin_keys=fx_admin_meta_keys, record=record)

    def test_loads(self, fx_admin_meta_keys: AdministrationKeys, fx_lib_record_config_min_magic: dict):
        """Can create a minimal unrestricted Record from a JSON serialised dict."""
        record = RecordMagicOpen.loads(value=fx_lib_record_config_min_magic, admin_keys=fx_admin_meta_keys)
        self._assert_defaults(keys=fx_admin_meta_keys, record=record)

    def test_existing_admin(
        self, fx_admin_meta_keys: AdministrationKeys, fx_admin_meta_element: AdministrationMetadata
    ):
        """Can create a minimal unrestricted Record element from directly assigned properties."""
        expected = ["https://gitlab.example.com/group/project/-/issues/1"]
        fx_admin_meta_element.gitlab_issues = expected
        record = RecordMagicOpen(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
            ),
            admin_keys=fx_admin_meta_keys,
            admin_meta=fx_admin_meta_element,
        )

        assert isinstance(record, RecordMagicOpen)
        admin_meta = get_admin(keys=fx_admin_meta_keys, record=record)
        assert isinstance(admin_meta, AdministrationMetadata)
        assert admin_meta.gitlab_issues == expected
        metadata_permission = admin_meta.metadata_permissions[0]
        assert metadata_permission.directory == "*"
        assert metadata_permission.group == "*"

    @pytest.mark.cov()
    def test_valid(self, fx_admin_meta_keys: AdministrationKeys):
        """Can create a minimal Record, valid against catalogue requirements and profiles."""
        date_ = datetime(2014, 6, 30, tzinfo=UTC).date()
        record = RecordMagicOpen(
            file_identifier="x",
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            identification=Identification(
                title="x",
                abstract="x",
                dates=Dates(creation=Date(date=date_)),
                edition="x",
                extents=Extents(
                    [
                        Extent(
                            identifier="bounding",
                            geographic=ExtentGeographic(
                                bounding_box=BoundingBox(
                                    west_longitude=0, east_longitude=0, south_latitude=0, north_latitude=0
                                )
                            ),
                        )
                    ]
                ),
            ),
            data_quality=DataQuality(lineage=Lineage(statement="x")),
            admin_keys=fx_admin_meta_keys,
        )

        assert isinstance(record, RecordMagic)
        record.validate()
