import json
from copy import deepcopy
from datetime import UTC, date, datetime

import pytest

from lantern.lib.metadata_library.models.record.elements.common import ContactIdentity
from lantern.models.item.algolia.item import ItemAlgolia, ObjectRecord
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import SiteMeta


class TestItemAlgolia:
    """Test Algolia search item."""

    def test_init_record_revision(self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision):
        """Can create an ItemAlgolia from a Catalogue record revision."""
        fx_revision_model_min.identification.supplemental_information = "x"

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=None)
        assert isinstance(item, ItemAlgolia)
        assert item.record.file_identifier == fx_revision_model_min.file_identifier

        # Check properties not covered by Algolia objects are removed for consistency with items created from objects
        assert item.record.identification.supplemental_information is None

    def test_init_object(self, fx_site_meta: SiteMeta, fx_item_algolia_object_min: ObjectRecord):
        """Can create an ItemAlgolia from an Algolia search index object."""
        item = ItemAlgolia(algolia_object=fx_item_algolia_object_min, admin_keys=None)
        assert isinstance(item, ItemAlgolia)
        assert isinstance(item.record, RecordRevision)

    def test_init_record(self, fx_site_meta: SiteMeta, fx_record_model_min: Record):
        """Cannot create an ItemAlgolia from a record without a revision."""
        with pytest.raises(TypeError, match=r"Record must be a RecordRevision."):
            _ = ItemAlgolia(record=fx_record_model_min, admin_keys=None)

    def test_init_empty(self, fx_site_meta: SiteMeta):
        """Cannot create an ItemAlgolia without a record or index object."""
        with pytest.raises(TypeError, match=r"Catalogue record revision or an Algolia object must be provided."):
            ItemAlgolia()

    @pytest.mark.parametrize("poc_type", ["o", "i"])
    def test_loads_from_algolia_object(self, fx_item_algolia_object_min: ObjectRecord, poc_type: str):
        """Can create a minimal record from an Algolia search object."""
        record_data = json.loads(fx_item_algolia_object_min["_recordData"])
        record_data[0] = poc_type
        fx_item_algolia_object_min["_recordData"] = json.dumps(record_data, ensure_ascii=False)

        result = ItemAlgolia._loads_from_algolia_object(fx_item_algolia_object_min)
        assert isinstance(result, RecordRevision)
        result.validate()

        _poc_org = result.metadata.contacts[0].organisation
        _poc_inv = result.metadata.contacts[0].individual
        if poc_type == "o":
            assert _poc_org is not None
            assert _poc_inv is None
        elif poc_type == "i":
            assert _poc_org is None
            assert _poc_inv is not None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (date(2014, 6, 30), 1404086400),  # 2014-06-30 00:00:00
            (datetime(2014, 6, 30, 14, 20, 45, tzinfo=UTC), 1404138045),
        ],
    )
    def test_to_timestamp(self, value: date | datetime, expected: int):
        """Can encode date(time) as a Unix timestamp."""
        assert ItemAlgolia._to_timestamp(value) == expected

    def test_object(self, fx_revision_model_min: RecordRevision, fx_item_algolia_object_min: ObjectRecord):
        """Can create an Algolia search object from a record."""
        fx_revision_model_min.identification.purpose = "x"

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=None)
        result = item.object
        assert result == fx_item_algolia_object_min

    @pytest.mark.parametrize("poc_type", ["o", "i"])
    def test_record_data(self, fx_revision_model_min: RecordRevision, poc_type: str):
        """Can generate JSON encoded tuple for additional information from record."""
        expected_name = "x" if poc_type == "o" else "xx"
        expected_poc_email = "e"
        expected_creation = "2014-06-30"
        if poc_type == "i":
            fx_revision_model_min.identification.contacts[0].organisation = None
            fx_revision_model_min.identification.contacts[0].individual = ContactIdentity(name=expected_name)
        fx_revision_model_min.identification.contacts[0].email = expected_poc_email

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=None)
        result = item._record_data
        data = json.loads(result)

        assert isinstance(data, list)  # Tuples become lists in JSON
        assert len(data) == 4
        assert data[0] == poc_type
        assert data[1] == expected_name
        assert data[2] == expected_poc_email
        assert data[3] == expected_creation

    def test_loop(self, fx_revision_model_min: RecordRevision):
        """
        Can convert from minimal record to Algolia search object and back.

        This is only lossless for a minimal record.
        """
        fx_revision_model_min.identification.purpose = "x"

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=None)
        obj_from_record = item.object
        record_from_obj = item._loads_from_algolia_object(obj_from_record)

        expected = deepcopy(fx_revision_model_min)
        # reconstructed records have an 'empty' abstract
        expected.identification.abstract = "-"
        # reconstructed records include email in metadata PoC
        expected.metadata.contacts[0].email = expected.identification.contacts[0].email

        assert record_from_obj == expected
