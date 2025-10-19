from datetime import date

import pytest
from cattrs import ClassValidationError

from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.elements.common import Contact, ContactIdentity, Contacts, Date, Dates
from lantern.lib.metadata_library.models.record.elements.identification import Identification
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin, set_admin
from lantern.lib.metadata_library.models.record.utils.kv import get_kv
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision


class TestRecordRevision:
    """Test derived Record Revision class."""

    def test_init(self):
        """Can create a minimal Record Revision class instance from directly assigned properties."""
        expected_str = "x"

        record = RecordRevision(
            file_identifier="x",
            file_revision=expected_str,
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

        assert isinstance(record, Record)
        assert isinstance(record, RecordRevision)
        assert record.identification.title == expected_str  # base record property
        assert record.file_identifier == expected_str  # record property
        assert record.file_revision == expected_str  # record revision property
        assert isinstance(record.distribution, list)  # base record post-init property

    def test_no_revision(self):
        """Cannot create a RecordRevision directly without a file_revision."""
        with pytest.raises(ValueError, match=r"Record Revisions require a file_revision."):
            # noinspection PyTypeChecker
            _ = RecordRevision(
                file_identifier="x",
                file_revision=None,
                hierarchy_level=HierarchyLevelCode.DATASET,
                metadata=Metadata(
                    contacts=Contacts(
                        [Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])]
                    ),
                    date_stamp=date(2014, 6, 30),
                ),
                identification=Identification(
                    title="x", abstract="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))
                ),
            )

    @pytest.mark.parametrize(("extra_config", "expected"), [({}, True), ({"x": "x"}, False)])
    def test_config_supported(self, fx_revision_config_min: dict, extra_config: dict, expected: bool):
        """Can accurately determine if a record config contains unsupported properties."""
        config = {**fx_revision_config_min, **extra_config}
        result = RecordRevision._config_supported(config=config)
        assert result == expected

    @pytest.mark.parametrize("has_schema", [False, True])
    def test_loads(self, fx_revision_config_min: dict, has_schema: bool):
        """
        Can create a Record Revision from a JSON serialised dict plus additional context.

        This only tests revision specific properties can be combined with regular Record properties.
        """
        expected_str = "x"
        schema = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"

        fx_revision_config_min["file_identifier"] = expected_str
        fx_revision_config_min["file_revision"] = expected_str
        fx_revision_config_min["identification"]["title"]["value"] = expected_str
        if has_schema:
            fx_revision_config_min["$schema"] = schema

        record = RecordRevision.loads(fx_revision_config_min)

        assert record.identification.title == expected_str  # record property
        assert record.file_revision == expected_str  # record revision property
        assert isinstance(record.distribution, list)  # parent post-init property

    def test_no_revision_loads(self, fx_revision_config_min: dict):
        """Cannot create a RecordRevision from a record config without a file_revision."""
        del fx_revision_config_min["file_revision"]
        with pytest.raises(ClassValidationError) as excinfo:
            _ = RecordRevision.loads(fx_revision_config_min)
        assert any(isinstance(e, KeyError) and e.args[0] == "file_revision" for e in excinfo.value.exceptions)

    @pytest.mark.parametrize("strip_admin", [False, True])
    @pytest.mark.parametrize("inc_revision", [False, True])
    def test_dumps(
        self,
        fx_revision_config_min: dict,
        fx_revision_model_min: RecordRevision,
        fx_admin_meta_keys: AdministrationKeys,
        strip_admin: bool,
        inc_revision: bool,
    ):
        """
        Can encode record revision as a dict that can be serialised to JSON with optional file revision property.

        This only tests revision specific properties can be optionally included along with regular Record properties.
        """
        value_admin = Administration(id=fx_revision_model_min.file_identifier)
        set_admin(keys=fx_admin_meta_keys, record=fx_revision_model_min, admin_meta=value_admin)

        config = fx_revision_model_min.dumps(strip_admin=strip_admin, with_revision=inc_revision)
        result = Record.loads(config)
        if inc_revision:
            result = RecordRevision.loads(config)
        kv = get_kv(result)

        assert config["identification"]["title"]["value"] == fx_revision_config_min["identification"]["title"]["value"]
        if inc_revision:
            assert config["file_revision"] == "x"
        else:
            assert "file_revision" not in config
        if strip_admin:
            assert "administrative_metadata" not in kv
            # guard against original record being modified
            assert get_admin(keys=fx_admin_meta_keys, record=fx_revision_model_min) is not None
            assert get_admin(keys=fx_admin_meta_keys, record=result) is None
        else:
            assert "administrative_metadata" in kv
