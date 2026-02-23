from datetime import date

import pytest
from cattrs import ClassValidationError

from lantern.lib.metadata_library.models.record.elements.common import (
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
)
from lantern.lib.metadata_library.models.record.elements.identification import Extent, Identification
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role
from lantern.lib.metadata_library.models.record.presets.extents import make_bbox_extent
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record as RecordBase
from lantern.lib.metadata_library.models.record.record import RecordInvalidError
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.record import Record


class TestRecord:
    """Test derived Record class."""

    @staticmethod
    def _make_record(file_identifier: str) -> Record:
        return Record(
            file_identifier=file_identifier,
            hierarchy_level=HierarchyLevelCode.PRODUCT,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})]
                ),
                date_stamp=date(2014, 6, 30),
            ),
            identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))),
        )

    @staticmethod
    def _make_valid_record(file_identifier: str | None = "5d5b4e21-fd32-409c-be83-ca1c339903e5") -> Record:
        record = TestRecord._make_record(file_identifier)
        record.identification.identifiers.append(make_bas_cat(record.file_identifier))
        record.identification.contacts.append(make_magic_role(roles={ContactRoleCode.POINT_OF_CONTACT}))
        record.identification.identifiers.append(
            Identifier(identifier="products/x", href="https://data.bas.ac.uk/products/x", namespace=ALIAS_NAMESPACE)
        )
        record.identification.extents.extend(
            [
                Extent(identifier="x", geographic=make_bbox_extent(0, 0, 0, 0)),
                Extent(identifier="y", geographic=make_bbox_extent(0, 0, 0, 0)),
            ]
        )
        return record

    def test_init(self):
        """Can create a minimal Record class instance from directly assigned properties."""
        expected_str = "x"
        record = self._make_record(file_identifier=expected_str)

        assert isinstance(record, RecordBase)
        assert isinstance(record, Record)
        assert record.identification.title == expected_str  # base record property
        assert record.file_identifier == expected_str  # record property
        assert isinstance(record.distribution, list)  # parent post-init property

    def test_no_file_identifier(self):
        """Cannot create a Record class instance directly without a file_identifier."""
        record = self._make_record(file_identifier="x")
        with pytest.raises(ValueError, match=r"Records require a file_identifier."):
            # noinspection PyArgumentList
            _ = Record(
                hierarchy_level=record.hierarchy_level,
                metadata=record.metadata,
                identification=record.identification,
            )

    @pytest.mark.parametrize(("extra_config", "expected"), [({}, True), ({"x": "x"}, False)])
    def test_config_supported(self, fx_record_config_min: dict, extra_config: dict, expected: bool):
        """Can accurately determine if a record config contains unsupported properties."""
        config = {**fx_record_config_min, **extra_config}
        result = Record._config_supported(config=config)
        assert result == expected

    @pytest.mark.parametrize("has_schema", [False, True])
    def test_loads(self, fx_record_config_min: dict, has_schema: bool):
        """
        Can create a Record from a JSON serialised dict.

        This only tests minimum properties and the returned instance type.
        """
        expected_str = "x"
        schema = RecordBase._schema

        fx_record_config_min["file_identifier"] = expected_str
        fx_record_config_min["identification"]["title"]["value"] = expected_str
        if has_schema:
            fx_record_config_min["$schema"] = schema

        # has_schema used as coverage branching workaround
        record = Record.loads(fx_record_config_min, check_supported=has_schema)

        assert record.identification.title == expected_str  # base record property
        assert record.file_identifier == expected_str  # record property
        assert isinstance(record.distribution, list)  # parent post-init property

    def test_loads_no_file_identifier(self, fx_record_config_min: dict):
        """Cannot create a Record class instance from a JSON serialised dict without a file_identifier."""
        del fx_record_config_min["file_identifier"]
        with pytest.raises(ClassValidationError) as excinfo:
            Record.loads(fx_record_config_min)
        assert "Records require a file_identifier." in str(excinfo.value.exceptions[0])

    def test_valid(self):
        """Can validate a Record complying with catalogue record requirements."""
        record = self._make_valid_record()
        record.validate()

    @pytest.mark.cov()
    def test_file_identifier(self):
        """Can use testing value as file identifier."""
        record = self._make_valid_record(file_identifier="x")
        record.validate()

    def test_invalid_file_identifier(self):
        """Cannot validate a Record with file identifier that isn't a UUID."""
        record = self._make_valid_record(file_identifier="⭐️")

        with pytest.raises(RecordInvalidError) as excinfo:
            record.validate()
        assert isinstance(excinfo.value.validation_error, ValueError)
        assert f"Invalid file identifier '{record.file_identifier}' must be a UUID" in str(
            excinfo.value.validation_error
        )

    @pytest.mark.parametrize(
        ("identifier", "match"),
        [
            (
                Identifier(identifier="x", namespace="x"),
                "No resource identifier with catalogue namespace.",
            ),
            (
                Identifier(identifier="y", namespace=CATALOGUE_NAMESPACE),
                "Invalid identifier value in Catalogue resource identifier.",
            ),
            (
                Identifier(identifier="5d5b4e21-fd32-409c-be83-ca1c339903e5", href="y", namespace=CATALOGUE_NAMESPACE),
                "Invalid href in Catalogue resource identifier.",
            ),
        ],
    )
    def test_invalid_identifier(self, identifier: Identifier, match: str):
        """Cannot validate a Record with an invalid resource identifier."""
        record = self._make_valid_record()
        record.identification.identifiers.clear()
        record.identification.identifiers.append(identifier)

        with pytest.raises(RecordInvalidError) as excinfo:
            record.validate()
        assert isinstance(excinfo.value.validation_error, ValueError)
        assert match in str(excinfo.value.validation_error)

    def test_invalid_poc(self):
        """Cannot validate a Record with a missing point of contact."""
        record = self._make_valid_record()
        record.identification.contacts.clear()

        with pytest.raises(RecordInvalidError) as excinfo:
            record.validate()
        assert isinstance(excinfo.value.validation_error, ValueError)
        assert "No resource contact with Point of Contact role." in str(excinfo.value.validation_error)

    def test_invalid_extents(self):
        """Cannot validate a Record with non-distinct extent identifiers."""
        record = self._make_valid_record()
        extent = Extent(identifier="x", geographic=make_bbox_extent(0, 0, 0, 0))
        record.identification.extents.clear()
        record.identification.extents.extend([extent, extent])

        with pytest.raises(RecordInvalidError) as excinfo:
            record.validate()
        assert isinstance(excinfo.value.validation_error, ValueError)
        assert "Duplicate extent identifier 'x', must be unique." in str(excinfo.value.validation_error)

    @pytest.mark.parametrize(
        ("identifier", "match"),
        [
            (
                Identifier(identifier="x", namespace=ALIAS_NAMESPACE),
                "Invalid alias href 'None' must be 'https://data.bas.ac.uk/x'.",
            ),
            (
                Identifier(identifier="x", href="/x", namespace=ALIAS_NAMESPACE),
                "Invalid alias href '/x' must be 'https://data.bas.ac.uk/x'.",
            ),
            (
                Identifier(identifier="x/x/x", href="https://data.bas.ac.uk/x/x/x", namespace=ALIAS_NAMESPACE),
                "Invalid alias identifier 'x/x/x' must not contain additional '/' values.",
            ),
            (
                Identifier(identifier="x/x", href="https://data.bas.ac.uk/x/x", namespace=ALIAS_NAMESPACE),
                "Invalid prefix in alias identifier 'x/x' for hierarchy level.",
            ),
            (
                Identifier(
                    identifier="products/123e4567-e89b-12d3-a456-426614174000",
                    href="https://data.bas.ac.uk/products/123e4567-e89b-12d3-a456-426614174000",
                    namespace=ALIAS_NAMESPACE,
                ),
                "Invalid alias identifier 'products/123e4567-e89b-12d3-a456-426614174000' must not contain a UUID.",
            ),
        ],
    )
    def test_invalid_aliases(self, identifier: Identifier, match: str):
        """Cannot validate a Record with invalid aliases."""
        record = self._make_valid_record()
        record.identification.identifiers.append(identifier)

        with pytest.raises(RecordInvalidError) as excinfo:
            record.validate()
        assert isinstance(excinfo.value.validation_error, ValueError)
        assert match in str(excinfo.value.validation_error)
