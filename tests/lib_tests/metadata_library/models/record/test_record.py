import json
import logging
from copy import deepcopy
from datetime import UTC, date, datetime

import pytest
from bas_metadata_library.standards.iso_19115_2 import MetadataRecord
from bas_metadata_library.standards.iso_19115_common.utils import _encode_date_properties
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from pytest_mock import MockerFixture

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Citation,
    Constraint,
    Constraints,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    Identifiers,
    Maintenance,
    OnlineResource,
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
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.conformance import (
    MAGIC_ADMINISTRATION_V1,
    MAGIC_DISCOVERY_V1,
    MAGIC_DISCOVERY_V2,
)
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError, RecordSchema
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin, set_admin
from lantern.lib.metadata_library.models.record.utils.kv import set_kv


class TestRecordSchema:
    """Test RecordSchema enumeration helper methods."""

    def test_map_schema(self):
        """Can get an enum member for a supported schema."""
        href = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"
        assert RecordSchema.map_href(href) == RecordSchema.ISO_2_V4

    def test_map_schema_unknown(self):
        """Cannot get an enum member for an unknown or unsupported schema."""
        with pytest.raises(KeyError):
            RecordSchema.map_href("unknown")

    @pytest.mark.parametrize(
        ("schema", "schema_id"),
        [
            (
                RecordSchema.ISO_2_V4,
                "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
            ),
            (
                RecordSchema.MAGIC_DISCO_V1,
                "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/magic-discovery-v1.json",
            ),
            (
                RecordSchema.MAGIC_DISCO_V2,
                "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/magic-discovery-v2.json",
            ),
        ],
    )
    def test_get_schema_contents(self, schema: RecordSchema, schema_id: str):
        """Can get the contents of a supported schema."""
        result = RecordSchema.get_schema_contents(schema)
        assert isinstance(result, dict)
        assert result["$id"] == schema_id


class TestRecord:
    """Test root Record element."""

    magic_discovery_v1_valid = Record(
        file_identifier="x",
        hierarchy_level=HierarchyLevelCode.PRODUCT,
        metadata=Metadata(
            contacts=Contacts(
                [
                    Contact(
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
                ]
            ),
            constraints=Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.ACCESS,
                        restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                        statement="Open Access (Anonymous)",
                    ),
                    Constraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                        href="https://creativecommons.org/licenses/by-nd/4.0/",
                        statement="This information is licensed under the Creative Commons Attribution-NoDerivatives 4.0 International Licence (CC BY-ND 4.0). To view this licence, visit https://creativecommons.org/licenses/by-nd/4.0/",
                    ),
                ]
            ),
            date_stamp=datetime(2014, 6, 30, tzinfo=UTC).date(),
        ),
        identification=Identification(
            title="x",
            edition="x",
            identifiers=Identifiers(
                [Identifier(identifier="x", href="https://data.bas.ac.uk/items/x", namespace="data.bas.ac.uk")]
            ),
            abstract="x",
            dates=Dates(
                creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()),
                released=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()),
            ),
            contacts=Contacts(
                [
                    Contact(
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
                ]
            ),
            maintenance=Maintenance(
                maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED,
                progress=ProgressCode.COMPLETED,
            ),
            constraints=Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.ACCESS,
                        restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                        statement="Open Access (Anonymous)",
                    ),
                    Constraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                        href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                        statement="This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
                    ),
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
        data_quality=DataQuality(
            lineage=Lineage(statement="x"),
            domain_consistency=DomainConsistencies(
                [
                    DomainConsistency(
                        specification=Citation(
                            title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                            href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
                            dates=Dates(publication=Date(date=date(2024, 11, 1))),
                            edition="1",
                            contacts=Contacts(
                                [
                                    Contact(
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
                                        role={ContactRoleCode.PUBLISHER},
                                    )
                                ]
                            ),
                        ),
                        explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
                        result=True,
                    )
                ]
            ),
        ),
    )

    magic_administration_v1_valid = Record(
        file_identifier="x",
        hierarchy_level=HierarchyLevelCode.DATASET,
        metadata=Metadata(
            contacts=Contacts(
                [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})]
            ),
            date_stamp=datetime(2014, 6, 30, tzinfo=UTC).date(),
        ),
        identification=Identification(
            title="x",
            abstract="x",
            dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())),
            supplemental_information="...",
        ),
        data_quality=DataQuality(
            domain_consistency=DomainConsistencies([MAGIC_ADMINISTRATION_V1]),
        ),
    )

    def test_init(self):
        """Can create a minimal Record element from directly assigned properties."""
        value = "x"
        expected_schema = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"
        date_stamp = datetime(2014, 6, 30, tzinfo=UTC).date()
        hierarchy_level = HierarchyLevelCode.PRODUCT

        record = Record(
            hierarchy_level=hierarchy_level,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name=value), role={ContactRoleCode.POINT_OF_CONTACT})]
                ),
                date_stamp=date_stamp,
            ),
            identification=Identification(title=value, abstract=value, dates=Dates(creation=Date(date=date_stamp))),
        )

        assert record._schema == expected_schema
        assert record.hierarchy_level == hierarchy_level
        assert record.metadata.contacts[0].organisation.name == value
        assert record.metadata.date_stamp == date_stamp
        assert record.identification.abstract == value
        assert isinstance(record.distribution, list)
        assert len(record.distribution) == 0

    def test_sha1(self, fx_lib_record_model_min_iso: Record):
        """Can calculate a SHA1 hash of the record config."""
        assert fx_lib_record_model_min_iso.sha1 == "12e1d01105a5c77e3315e493acf5eb590129ffca"

    @pytest.mark.cov()
    @pytest.mark.parametrize("maintenance", [False, True])
    def test_normalise_static_config_values(self, fx_lib_record_config_min_iso: dict, maintenance: bool):
        """Can normalise record."""
        if maintenance:
            fx_lib_record_config_min_iso["metadata"]["maintenance"] = {"progress": ProgressCode.ON_GOING.value}

        result = Record._normalise_static_config_values(fx_lib_record_config_min_iso)
        assert "maintenance" not in result["metadata"]

    @pytest.mark.parametrize("value", [{}, {"invalid": "x"}, {"hierarchy_level": HierarchyLevelCode.DIMENSION_GROUP}])
    def test_config_supported(self, fx_lib_record_config_min_iso: dict, value: dict):
        """Can determine if a record config is supported or not."""
        if value:
            fx_lib_record_config_min_iso = {**fx_lib_record_config_min_iso, **value}
        expected = not bool(value)

        result = Record._config_supported(fx_lib_record_config_min_iso)
        assert result == expected

    @pytest.mark.cov()
    def test_config_supported_log(self, caplog: pytest.LogCaptureFixture, fx_lib_record_config_min_iso: dict):
        """Can log unsupported record config contents if set."""
        fx_lib_record_config_min_iso["invalid"] = "x"
        logger = logging.getLogger("test")
        logger.setLevel(logging.DEBUG)

        Record._config_supported(config=fx_lib_record_config_min_iso, logger=logger)

        assert "Diff: Item root['invalid'] (\"x\") added to dictionary." in caplog.text

    @pytest.mark.parametrize("check_supported", [False, True])
    def test_loads(self, check_supported: bool):
        """
        Can create a Record from a JSON serialised dict.

        This is not intended as an exhaustive/comprehensive test of all properties, rather it tests any properties
        that require special processing, such as non-standard nesting or enumerations.
        """
        expected_str = "x"
        expected_date = date(2014, 6, 30)
        expected_enums = {
            "hierarchy_level": HierarchyLevelCode.PRODUCT,
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        config = {
            "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
            "hierarchy_level": expected_enums["hierarchy_level"].value,
            "metadata": {
                "contacts": [{"organisation": {"name": expected_str}, "role": [expected_enums["contact_role"].value]}],
                "date_stamp": expected_date.isoformat(),
            },
            "identification": {
                "title": {"value": expected_str},
                "dates": {"creation": expected_date.isoformat()},
                "abstract": expected_str,
                "constraints": [
                    {
                        "type": expected_enums["constraint_type"].value,
                        "restriction_code": expected_enums["constraint_code"].value,
                    }
                ],
                "lineage": {"statement": expected_str},
            },
        }

        record = Record.loads(config, check_supported=check_supported)

        assert record._schema is not None
        assert record._schema == config["$schema"]
        assert record.identification.title == expected_str  # specially nested property
        assert record.data_quality.lineage.statement == expected_str  # moved property
        assert record.hierarchy_level == expected_enums["hierarchy_level"]  # enum property
        assert next(iter(record.metadata.contacts[0].role)) == expected_enums["contact_role"]  # enum property
        assert record.metadata.date_stamp == expected_date  # date property
        assert record.identification.dates.creation.date == expected_date  # date property
        assert record.identification.constraints[0].type == expected_enums["constraint_type"]  # enum property
        assert (
            record.identification.constraints[0].restriction_code == expected_enums["constraint_code"]
        )  # enum property
        assert isinstance(record.distribution, list)  # post-init default property

    def test_loads_invalid_schema(self):
        """Cannot create a Record from a JSON serialised dict referencing an unsupported JSON Schema."""
        config = {
            "$schema": "x",
            "hierarchy_level": HierarchyLevelCode.PRODUCT,
            "metadata": {
                "contacts": [{"organisation": {"name": "x"}, "role": [ContactRoleCode.POINT_OF_CONTACT]}],
                "date_stamp": date(2014, 6, 30).isoformat(),
            },
            "identification": {
                "title": {"value": "x"},
                "dates": {"creation": date(2014, 6, 30).isoformat()},
                "abstract": "x",
            },
        }

        with pytest.raises(ValueError, match=r"Unsupported JSON Schema in data."):
            _ = Record.loads(config)

    @pytest.mark.parametrize(
        ("sinfo", "expected"),
        [
            (None, None),
            ("x", "x"),  # can't parse so not changed
            (json.dumps([]), json.dumps([])),  # can't parse so not changed
            (json.dumps({}), None),
            (json.dumps({"admin_metadata": {}, "x": "x"}), json.dumps({"x": "x"})),
            (json.dumps({"admin_metadata": {}}), None),
        ],
    )
    def test_strip_admin_meta(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_lib_record_model_min_iso: Record,
        sinfo: str | None,
        expected: str,
    ):
        """Can strip admin metadata from a record if present."""
        fx_lib_record_model_min_iso.identification.supplemental_information = sinfo
        Record._strip_admin(fx_lib_record_model_min_iso)
        assert fx_lib_record_model_min_iso.identification.supplemental_information == expected

    fake_admin_version = DomainConsistency(
        specification=Citation(
            title="x",
            href="https://metadata-standards.data.bas.ac.uk/profiles/magic-administration/vX/",
            dates=Dates(publication=Date(date=date(2014, 6, 30))),
            edition="X",
        ),
        explanation="x",
        result=True,
    )
    simple_consistency = DomainConsistency(
        specification=Citation(
            title="x",
            dates=Dates(publication=Date(date=date(2014, 6, 30))),
            edition="X",
        ),
        explanation="x",
        result=True,
    )

    @pytest.mark.parametrize(
        ("dq", "expected"),
        [
            (DataQuality(), DataQuality()),
            # unrelated properties not changed
            (
                DataQuality(
                    domain_consistency=DomainConsistencies([MAGIC_ADMINISTRATION_V1]), lineage=Lineage(statement="x")
                ),
                DataQuality(lineage=Lineage(statement="x")),
            ),
            # unrelated conformance properties not changed
            (
                DataQuality(domain_consistency=DomainConsistencies([MAGIC_DISCOVERY_V2])),
                DataQuality(domain_consistency=DomainConsistencies([MAGIC_DISCOVERY_V2])),
            ),
            # conformance properties without specification href not changed
            (
                DataQuality(domain_consistency=DomainConsistencies([simple_consistency])),
                DataQuality(domain_consistency=DomainConsistencies([simple_consistency])),
            ),
            # removes target conformance
            (
                DataQuality(domain_consistency=DomainConsistencies([MAGIC_ADMINISTRATION_V1])),
                DataQuality(),
            ),
            # removes target conformance (any version)
            (
                DataQuality(domain_consistency=DomainConsistencies([fake_admin_version])),
                DataQuality(),
            ),
            # preserves unrelated conformance
            (
                DataQuality(domain_consistency=DomainConsistencies([MAGIC_DISCOVERY_V2, MAGIC_ADMINISTRATION_V1])),
                DataQuality(domain_consistency=DomainConsistencies([MAGIC_DISCOVERY_V2])),
            ),
        ],
    )
    def test_strip_admin_conformance(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        fx_lib_record_model_min_iso: Record,
        dq: DataQuality,
        expected: DataQuality,
    ):
        """Can strip admin metadata conformance from a record if present."""
        fx_lib_record_model_min_iso.data_quality = dq
        Record._strip_admin(fx_lib_record_model_min_iso)
        assert fx_lib_record_model_min_iso.data_quality == expected

    @pytest.mark.parametrize("strip_admin", [False, True])
    def test_dumps(
        self, fx_admin_meta_keys: AdministrationKeys, fx_lib_record_model_min_iso: Record, strip_admin: bool
    ):
        """
        Can encode record as a dict that can be serialised to JSON.

        This is not intended as an exhaustive/comprehensive test of all properties, rather it tests any properties
        that require special processing, such as non-standard nesting or enumerations.
        """
        value_str = "x"
        value_enums = {
            "hierarchy_level": HierarchyLevelCode.DATASET,
            "contact_role": ContactRoleCode.POINT_OF_CONTACT,
            "constraint_type": ConstraintTypeCode.USAGE,
            "constraint_code": ConstraintRestrictionCode.LICENSE,
        }
        fx_lib_record_model_min_iso.file_identifier = value_str  # required for administration metadata
        value_admin = AdministrationMetadata(id=fx_lib_record_model_min_iso.file_identifier)
        value_kv = {"x": "x"}
        fx_lib_record_model_min_iso.identification.constraints = Constraints(
            [Constraint(type=value_enums["constraint_type"], restriction_code=value_enums["constraint_code"])]
        )
        set_kv(kv=value_kv, record=fx_lib_record_model_min_iso)
        set_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso, admin_meta=value_admin)

        if not strip_admin:
            # `set_admin()` ensures an admin metadata key-value member is always added regardless of `strip_admin`,
            # this logic is to control whether that member is expected in the output.
            #
            # If included, we can't know the exact JWE to expect, as each is unique regardless of whether the data is
            # different. Therefore, a dummy value is expected.
            value_kv["admin_metadata"] = "x"
        expected = {
            "file_identifier": value_str,
            "hierarchy_level": value_enums["hierarchy_level"].value,
            "metadata": {
                "character_set": "utf8",
                "language": "eng",
                "contacts": [{"organisation": {"name": value_str}, "role": [value_enums["contact_role"].value]}],
                "date_stamp": fx_lib_record_model_min_iso.metadata.date_stamp.isoformat(),
                "metadata_standard": {
                    "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                    "version": "ISO 19115-2:2009(E)",
                },
            },
            "identification": {
                "title": {"value": value_str},
                "abstract": value_str,
                "dates": {"creation": "2014-06-30"},
                "constraints": [
                    {
                        "type": value_enums["constraint_type"].value,
                        "restriction_code": value_enums["constraint_code"].value,
                    }
                ],
                "character_set": "utf8",
                "language": "eng",
                "supplemental_information": json.dumps(value_kv),
            },
        }

        config = fx_lib_record_model_min_iso.dumps(strip_admin=strip_admin)
        kv = json.loads(config["identification"]["supplemental_information"])
        if not strip_admin:
            # admin meta values are a JWE, which are unique even when using the same data, so expected value is replaced
            kv["admin_metadata"] = value_kv["admin_metadata"]
            config["identification"]["supplemental_information"] = json.dumps(kv)
        assert config == expected

        if strip_admin:
            # guard against original record being modified
            assert get_admin(keys=fx_admin_meta_keys, record=fx_lib_record_model_min_iso) is not None

    def test_dumps_json(self, fx_lib_record_model_min_iso: Record):
        """
        Can encode record as a JSON schema instance encoded as a string.

        This only tests JSON schema specific properties are included, as other properties are tested elsewhere.
        """
        expected = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"

        result = fx_lib_record_model_min_iso.dumps_json()
        assert isinstance(result, str)

        decoded = json.loads(result)
        assert decoded["$schema"] == expected

    def test_dumps_xml(self, fx_lib_record_model_min_iso: Record):
        """
        Can encode record as ISO 19139 XML string.

        Internally this method dumps the record to a JSON config and uses the Metadata Library to encode this as XML.

        The Metadata Library's tests verify the conversion to and from a JSON dict extensively. As a result, this test
        is not intended as an exhaustive/comprehensive of this process.
        """
        expected = fx_lib_record_model_min_iso.dumps()

        result = fx_lib_record_model_min_iso.dumps_xml()
        config = _encode_date_properties(MetadataRecord(record=result).make_config().config)
        del config["$schema"]

        assert "<gmi:MI_Metadata" in result
        assert config == expected

    def test_validate_min_iso(self):
        """A minimally valid ISO record can be validated."""
        record = Record(
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})]
                ),
                date_stamp=datetime(2014, 6, 30, tzinfo=UTC).date(),
            ),
            identification=Identification(
                title="x", abstract="x", dates=Dates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC).date()))
            ),
        )

        assert record.validate() is None

    def test_validate_min_magic_discovery_v1(self):
        """Can validate a valid record using the MAGIC Discovery profile (v1, original href)."""
        record = deepcopy(self.magic_discovery_v1_valid)
        assert record._profile_schemas == [RecordSchema.MAGIC_DISCO_V1]
        assert record.validate() is None

    def test_validate_min_magic_discovery_v1_alt(self):
        """Can validate a valid record using the MAGIC Discovery profile (v1, replacement href)."""
        record = deepcopy(self.magic_discovery_v1_valid)
        record.data_quality.domain_consistency = DomainConsistencies([MAGIC_DISCOVERY_V1])

        assert record._profile_schemas == [RecordSchema.MAGIC_DISCO_V1]
        assert record.validate() is None

    def test_validate_min_magic_discovery_v2(self):
        """Can validate a valid record using the MAGIC Discovery profile (v2)."""
        record = deepcopy(self.magic_discovery_v1_valid)
        record.identification.other_citation_details = "x"
        record.identification.contacts.append(
            Contact(organisation=ContactIdentity(name="UKRI"), role={ContactRoleCode.RIGHTS_HOLDER})
        )
        record.data_quality.domain_consistency = DomainConsistencies([MAGIC_DISCOVERY_V2])

        assert record._profile_schemas == [RecordSchema.MAGIC_DISCO_V2]
        assert record.validate() is None

    def test_validate_min_magic_administration_v1(self):
        """Can validate a valid record using the MAGIC Discovery profile (v2)."""
        record = deepcopy(self.magic_administration_v1_valid)
        assert record._profile_schemas == [RecordSchema.MAGIC_ADMIN_V1]
        assert record.validate() is None

    def test_validate_invalid_iso(self, mocker: MockerFixture, fx_lib_record_model_min_iso: Record):
        """Can't validate a record that does not comply with the ISO schema."""
        mocker.patch.object(fx_lib_record_model_min_iso, "dumps", return_value={"invalid": "invalid"})

        with pytest.raises(RecordInvalidError):
            fx_lib_record_model_min_iso.validate()

    def test_validate_invalid_profile(self, fx_lib_record_model_min_iso: Record):
        """Can't validate a record that does not comply with a schema inferred from a domain consistency element."""
        fx_lib_record_model_min_iso.data_quality = DataQuality(
            domain_consistency=DomainConsistencies([MAGIC_DISCOVERY_V2])
        )

        with pytest.raises(RecordInvalidError):
            fx_lib_record_model_min_iso.validate()

    def test_validate_invalid_forced_schemas(self, fx_lib_record_model_min_iso: Record):
        """Can't validate a record that does not comply with a forced set of schemas."""
        with pytest.raises(RecordInvalidError):
            fx_lib_record_model_min_iso.validate(force_schemas=[RecordSchema.MAGIC_DISCO_V2])

    def test_validate_ignore_profiles(self, fx_lib_record_model_min_iso: Record):
        """Can validate a record that would not normally comply because of a schema indicated via domain consistency."""
        fx_lib_record_model_min_iso.data_quality = DataQuality(
            domain_consistency=DomainConsistencies([MAGIC_DISCOVERY_V2])
        )
        fx_lib_record_model_min_iso.validate(use_profiles=False)

    @pytest.mark.parametrize(
        ("run", "values"),
        [
            (
                "minimal-iso",
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "metadata": {
                        "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
                        "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date().isoformat(),
                    },
                    "hierarchy_level": "dataset",
                    "identification": {
                        "title": {"value": "x"},
                        "dates": {"creation": "2014-06-30"},
                        "abstract": "x",
                    },
                },
            ),
            (
                "minimal-magic-discovery",
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "dataset",
                    "metadata": {
                        "character_set": "utf8",
                        "contacts": [
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
                            }
                        ],
                        "date_stamp": "2014-06-30",
                        "language": "eng",
                        "metadata_standard": {
                            "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                            "version": "ISO 19115-2:2009(E)",
                        },
                    },
                    "identification": {
                        "abstract": "x",
                        "character_set": "utf8",
                        "constraints": [
                            {
                                "restriction_code": "unrestricted",
                                "statement": "Open Access (Anonymous)",
                                "type": "access",
                            },
                            {
                                "href": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                                "restriction_code": "license",
                                "statement": "This information is licensed under the Open Government Licence v3.0. To view this licence, visit https://www.nationalarchives.gov.uk/doc/open-government-licence/.",
                                "type": "usage",
                            },
                        ],
                        "contacts": [
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
                            {
                                "organisation": {
                                    "name": "UKRI",
                                },
                                "role": ["rightsHolder"],
                            },
                        ],
                        "dates": {"creation": "2014-06-30", "released": "2014-06-30"},
                        "domain_consistency": [
                            {
                                "specification": {
                                    "title": {
                                        "value": "British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
                                        "href": "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/",
                                    },
                                    "dates": {"publication": "2025-11-24"},
                                    "edition": "2",
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
                        ],
                        "edition": "x",
                        "extents": [
                            {
                                "geographic": {
                                    "bounding_box": {
                                        "east_longitude": 0,
                                        "north_latitude": 0,
                                        "south_latitude": 0,
                                        "west_longitude": 0,
                                    }
                                },
                                "identifier": "bounding",
                            }
                        ],
                        "identifiers": [
                            {"href": "https://data.bas.ac.uk/items/x", "identifier": "x", "namespace": "data.bas.ac.uk"}
                        ],
                        "language": "eng",
                        "lineage": {"statement": "x"},
                        "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
                        "other_citation_details": "x",
                        "title": {"value": "x"},
                    },
                },
            ),
            (
                "complete",
                {
                    "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
                    "file_identifier": "x",
                    "hierarchy_level": "dataset",
                    "metadata": {
                        "character_set": "utf8",
                        "language": "eng",
                        "contacts": [
                            {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["pointOfContact"],
                            }
                        ],
                        "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date().isoformat(),
                        "metadata_standard": {
                            "name": "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                            "version": "ISO 19115-2:2009(E)",
                        },
                    },
                    "reference_system_info": {
                        "code": {"value": "x", "href": "x"},
                        "version": "x",
                        "authority": {
                            "title": {"value": "x", "href": "x"},
                            "dates": {
                                "creation": "2014-06-30",
                                "publication": "2014-06-30",
                                "revision": "2014-06-30",
                                "adopted": "2014-06-30",
                                "deprecated": "2014-06-30",
                                "distribution": "2014-06-30",
                                "expiry": "2014-06-30",
                                "inForce": "2014-06-30",
                                "lastRevision": "2014-06-30",
                                "lastUpdate": "2014-06-30",
                                "nextUpdate": "2014-06-30",
                                "released": "2014-06-30",
                                "superseded": "2014-06-30",
                                "unavailable": "2014-06-30",
                                "validityBegins": "2014-06-30",
                                "validityExpires": "2014-06-30",
                            },
                            "edition": "x",
                            "identifiers": [{"identifier": "x", "href": "x", "namespace": "x"}],
                            "other_citation_details": "x",
                            "contact": {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["pointOfContact"],
                            },
                        },
                    },
                    "identification": {
                        "title": {"value": "x"},
                        "dates": {
                            "creation": "2014-06-30",
                            "publication": "2014-06-30",
                            "revision": "2014-06-30",
                            "adopted": "2014-06-30",
                            "deprecated": "2014-06-30",
                            "distribution": "2014-06-30",
                            "expiry": "2014-06-30",
                            "inForce": "2014-06-30",
                            "lastRevision": "2014-06-30",
                            "lastUpdate": "2014-06-30",
                            "nextUpdate": "2014-06-30",
                            "released": "2014-06-30",
                            "superseded": "2014-06-30",
                            "unavailable": "2014-06-30",
                            "validityBegins": "2014-06-30",
                            "validityExpires": "2014-06-30",
                        },
                        "edition": "x",
                        "series": {"name": "x", "edition": "x"},
                        "identifiers": [{"identifier": "x", "href": "x", "namespace": "x"}],
                        "other_citation_details": "x",
                        "abstract": "x",
                        "purpose": "x",
                        "contacts": [
                            {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["pointOfContact"],
                            }
                        ],
                        "graphic_overviews": [{"identifier": "x", "description": "x", "href": "x", "mime_type": "x"}],
                        "constraints": [
                            {"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}
                        ],
                        "aggregations": [
                            {
                                "identifier": {"identifier": "x", "href": "x", "namespace": "x"},
                                "association_type": "crossReference",
                                "initiative_type": "campaign",
                            }
                        ],
                        "maintenance": {"maintenance_frequency": "asNeeded", "progress": "completed"},
                        "language": "eng",
                        "character_set": "utf8",
                        "extents": [
                            {
                                "identifier": "x",
                                "geographic": {
                                    "bounding_box": {
                                        "west_longitude": 1.0,
                                        "east_longitude": 1.0,
                                        "south_latitude": 1.0,
                                        "north_latitude": 1.0,
                                    }
                                },
                                "temporal": {
                                    "period": {
                                        "start": "2014-06-30",
                                        "end": "2014-06-30",
                                    }
                                },
                            }
                        ],
                        "spatial_resolution": 1,
                        "supplemental_information": "x",
                        "lineage": {"statement": "x"},
                        "domain_consistency": [
                            {
                                "specification": {
                                    "title": {"value": "x", "href": "x"},
                                    "dates": {
                                        "creation": "2014-06-30",
                                        "publication": "2014-06-30",
                                        "revision": "2014-06-30",
                                        "adopted": "2014-06-30",
                                        "deprecated": "2014-06-30",
                                        "distribution": "2014-06-30",
                                        "expiry": "2014-06-30",
                                        "inForce": "2014-06-30",
                                        "lastRevision": "2014-06-30",
                                        "lastUpdate": "2014-06-30",
                                        "nextUpdate": "2014-06-30",
                                        "released": "2014-06-30",
                                        "superseded": "2014-06-30",
                                        "unavailable": "2014-06-30",
                                        "validityBegins": "2014-06-30",
                                        "validityExpires": "2014-06-30",
                                    },
                                    "edition": "x",
                                    "identifiers": [{"identifier": "x", "href": "x", "namespace": "x"}],
                                    "other_citation_details": "x",
                                    "contact": {
                                        "organisation": {"name": "x", "title": "x", "href": "x"},
                                        "individual": {"name": "x", "title": "x", "href": "x"},
                                        "phone": "x",
                                        "address": {
                                            "delivery_point": "x",
                                            "city": "x",
                                            "administrative_area": "x",
                                            "postal_code": "x",
                                            "country": "x",
                                        },
                                        "email": "x",
                                        "online_resource": {
                                            "href": "x",
                                            "protocol": "x",
                                            "title": "x",
                                            "description": "x",
                                            "function": "download",
                                        },
                                        "role": ["pointOfContact"],
                                    },
                                },
                                "explanation": "x",
                                "result": True,
                            }
                        ],
                    },
                    "distribution": [
                        {
                            "distributor": {
                                "organisation": {"name": "x", "title": "x", "href": "x"},
                                "individual": {"name": "x", "title": "x", "href": "x"},
                                "phone": "x",
                                "address": {
                                    "delivery_point": "x",
                                    "city": "x",
                                    "administrative_area": "x",
                                    "postal_code": "x",
                                    "country": "x",
                                },
                                "email": "x",
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                                "role": ["distributor"],
                            },
                            "format": {"format": "x", "href": "x"},
                            "transfer_option": {
                                "size": {"unit": "x", "magnitude": 1.0},
                                "online_resource": {
                                    "href": "x",
                                    "protocol": "x",
                                    "title": "x",
                                    "description": "x",
                                    "function": "download",
                                },
                            },
                        }
                    ],
                },
            ),
        ],
    )
    def test_loop(self, run: str, values: dict):
        """
        Can convert a JSON Schema instance dict into a Record and back again.

        Tests various configurations from minimal to complete.
        """
        record = Record.loads(values)
        result = json.loads(record.dumps_json(strip_admin=False))
        expected = values

        if run == "minimal-iso" or run == "minimal-magic":
            # preserve '$schema' key if present for an accurate comparison
            schema = expected.pop("$schema", None)
            expected = Record._normalise_static_config_values(expected)
            if schema:
                expected["$schema"] = schema

        assert result == expected
