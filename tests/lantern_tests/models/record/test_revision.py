from datetime import date

import pytest

from lantern.lib.metadata_library.models.record import Identification, Metadata, Record
from lantern.lib.metadata_library.models.record.elements.common import Contact, ContactIdentity, Contacts, Date, Dates
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, HierarchyLevelCode
from lantern.lib.metadata_library.models.record.summary import RecordSummary
from lantern.models.record.revision import RecordRevision, RecordRevisionSummary


class TestRecordRevision:
    """Test derived Record Revision class."""

    def test_init(self):
        """Can create a minimal Record Revision class instance from directly assigned properties."""
        record = RecordRevision(
            file_revision="x",
            hierarchy_level=HierarchyLevelCode.DATASET,
            metadata=Metadata(
                contacts=Contacts(
                    [Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])]
                ),
                date_stamp=date(2014, 6, 30),
            ),
            identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=date(2014, 6, 30)))),
        )

        assert isinstance(record, Record)
        assert isinstance(record, RecordRevision)
        assert record.file_revision == "x"

    @pytest.mark.parametrize(("extra_config", "expected"), [({}, True), ({"x": "x"}, False)])
    def test_config_supported(self, fx_record_config_minimal_iso: dict, extra_config: dict, expected: bool):
        """Can accurately determine if a record config contains unsupported properties."""
        config = {**fx_record_config_minimal_iso, "file_revision": "x", **extra_config}
        result = RecordRevision._config_supported(config=config)
        assert result == expected

    @pytest.mark.parametrize("has_schema", [False, True])
    def test_loads(self, has_schema: bool):
        """
        Can create a Record Revision from a JSON serialised dict plus additional context.

        This only tests revision specific properties can be combined with regular Record properties.
        """
        expected_str = "x"
        schema = "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json"

        base_config = {
            "hierarchy_level": HierarchyLevelCode.DATASET,
            "metadata": {
                "contacts": [{"organisation": {"name": expected_str}, "role": [ContactRoleCode.POINT_OF_CONTACT]}],
                "date_stamp": date(2014, 6, 30).isoformat(),
            },
            "identification": {
                "title": {"value": expected_str},
                "dates": {"creation": date(2014, 6, 30).isoformat()},
                "abstract": expected_str,
            },
        }
        config = {**base_config, "file_revision": expected_str}
        if has_schema:
            config["$schema"] = schema

        record = RecordRevision.loads(config)

        assert record.identification.title == expected_str  # record property
        assert record.file_revision == expected_str  # record revision property

    @pytest.mark.parametrize("inc_revision", [False, True])
    def test_dumps(
        self, fx_record_config_minimal_iso: dict, fx_record_revision_minimal_iso: RecordRevision, inc_revision: bool
    ):
        """
        Can encode record revision as a dict that can be serialised to JSON with optional file revision property.

        This only tests revision specific properties can be optionally included along with regular Record properties.
        """
        config = fx_record_revision_minimal_iso.dumps(with_revision=inc_revision)

        assert (
            config["identification"]["title"]["value"]
            == fx_record_config_minimal_iso["identification"]["title"]["value"]
        )
        if inc_revision:
            assert config["file_revision"] == "x"
        else:
            assert "file_revision" not in config

    def test_empty_revision(self):
        """Cannot create a RecordRevision directly without a file_revision."""
        with pytest.raises(ValueError, match="RecordRevision cannot be empty."):
            # noinspection PyTypeChecker
            _ = RecordRevision(
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

    def test_no_revision_loads(self, fx_record_config_minimal_iso: dict):
        """Cannot create a RecordRevision from a record config without a file_revision."""
        fx_record_config_minimal_iso = {**fx_record_config_minimal_iso, "file_revision": None}
        with pytest.raises(ValueError, match="RecordRevision cannot be empty."):
            _ = RecordRevision.loads(fx_record_config_minimal_iso)


class TestRecordRevisionSummary:
    """Test derived Record Revision Summary class."""

    def test_init(self):
        """Can create a minimal RecordRevisionSummary element from directly assigned properties."""
        expected = "x"
        expected_hierarchy_level = HierarchyLevelCode.DATASET
        expected_date = Date(date=date(2014, 6, 30))

        summary = RecordRevisionSummary(
            file_revision="x",
            hierarchy_level=expected_hierarchy_level,
            date_stamp=expected_date.date,
            title=expected,
            creation=expected_date,
        )

        assert isinstance(summary, RecordSummary)
        assert isinstance(summary, RecordRevisionSummary)
        assert summary.file_revision == "x"

    def test_loads_json_config(self):
        """Can create a RecordRevisionSummary from a dict loaded from JSON."""
        base_config = {
            "file_identifier": "59be7b09-4024-48e2-b7b3-6a0799196400",
            "hierarchy_level": "dataset",
            "date_stamp": "2025-05-18",
            "title": "x",
            "creation": "2014",
        }
        config = {"file_revision": "x", **base_config}

        summary = RecordRevisionSummary.loads(config)

        assert isinstance(summary, RecordRevisionSummary)
        assert summary.file_revision == "x"
        assert summary.creation.date.year == 2014

    def test_loads_record(self, fx_record_revision_minimal_iso: RecordRevision):
        """Can create a RecordRevisionSummary from a RecordRevision."""
        summary = RecordRevisionSummary.loads(fx_record_revision_minimal_iso)

        assert isinstance(summary, RecordRevisionSummary)
        assert summary.file_revision == "x"
        assert summary.creation.date.year == 2014

    def test_dumps(self, fx_record_revision_minimal_iso: RecordRevision):
        """Can create a dict that can be serialised to JSON from a RecordRevisionSummary."""
        summary = RecordRevisionSummary.loads(fx_record_revision_minimal_iso)
        result = summary.dumps()
        assert isinstance(result, dict)
        assert result["file_revision"] == "x"
        assert result["creation"] == "2014-06-30"
