from datetime import date

import pytest
from cattrs import ClassValidationError

from lantern.lib.metadata_library.models.record import Identification, Metadata
from lantern.lib.metadata_library.models.record import Record as RecordBase
from lantern.lib.metadata_library.models.record.elements.common import Contact, ContactIdentity, Contacts, Date, Dates
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.models.record import Record


class TestRecord:
    """Test derived Record class."""

    def test_init(self):
        """Can create a minimal Record class instance from directly assigned properties."""
        expected_str = "x"
        record = Record(
            file_identifier=expected_str,
            hierarchy_level=HierarchyLevelCode.DATASET,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})]
                ),
                date_stamp=date(2014, 6, 30),
            ),
            identification=Identification(
                title=expected_str, abstract="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))
            ),
        )

        assert isinstance(record, RecordBase)
        assert isinstance(record, Record)
        assert record.identification.title == expected_str  # base record property
        assert record.file_identifier == expected_str  # record property
        assert isinstance(record.distribution, list)  # parent post-init property

    def test_no_file_identifier(self):
        """Cannot create a Record class instance directly without a file_identifier."""
        with pytest.raises(ValueError, match="Records require a file_identifier."):
            # noinspection PyArgumentList
            _ = Record(
                hierarchy_level=HierarchyLevelCode.DATASET,
                metadata=Metadata(
                    contacts=Contacts(
                        [Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})]
                    ),
                    date_stamp=date(2014, 6, 30),
                ),
                identification=Identification(
                    title="x", abstract="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))
                ),
            )

    @pytest.mark.parametrize("has_schema", [False, True])
    def test_loads(self, fx_record_config_min: dict, has_schema: bool):
        """
        Can create a Record from a JSON serialised dict.

        This only tests minimum properties and the returned instance type.
        """
        expected_str = "x"
        schema = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"

        fx_record_config_min["file_identifier"] = expected_str
        fx_record_config_min["identification"]["title"]["value"] = expected_str
        if has_schema:
            fx_record_config_min["$schema"] = schema

        record = Record.loads(fx_record_config_min)

        assert record.identification.title == expected_str  # base record property
        assert record.file_identifier == expected_str  # record property
        assert isinstance(record.distribution, list)  # parent post-init property

    def test_loads_no_file_identifier(self, fx_record_config_min: dict):
        """Cannot create a Record class instance from a JSON serialised dict without a file_identifier."""
        del fx_record_config_min["file_identifier"]
        with pytest.raises(ClassValidationError):
            Record.loads(fx_record_config_min)
