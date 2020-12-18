import pytest

from scar_add_metadata_toolbox.classes import (
    Collection,
    Item,
    Record,
    MirrorRecord,
    MirrorRecordSummary,
    RecordSummary,
    CSWClient,
)


# Coverage test
def test_csw_client_repr():
    csw_client = CSWClient(config={"endpoint": "test", "auth": {}})
    assert repr(csw_client) == f"<CSWClient / Endpoint: {csw_client._csw_endpoint}>"


# Coverage test
def test_record_summary_repr():
    record_summary = RecordSummary(config={"file_identifier": "test", "resource": {"title": {"value": "test"}}})
    assert repr(record_summary) == f"<RecordSummary / {record_summary.identifier} / {record_summary.title}>"


# Coverage test
def test_record_repr():
    record = Record(config={"file_identifier": "test", "resource": {"title": {"value": "test"}}})
    assert repr(record) == f"<Record / {record.identifier}>"


# Coverage test
def test_mirror_record_summary_repr():
    mirror_record_summary = MirrorRecordSummary(
        config={"file_identifier": "test", "resource": {"title": {"value": "test"}}}, published=False
    )
    assert repr(mirror_record_summary) == f"<MirrorRecordSummary / {mirror_record_summary.identifier} / Unpublished>"


# Coverage test
def test_mirror_record_repr():
    mirror_record = MirrorRecord(
        config={"file_identifier": "test", "resource": {"title": {"value": "test"}}}, published=False
    )
    assert repr(mirror_record) == f"<MirrorRecord / {mirror_record.identifier} / Unpublished>"


# Coverage test
def test_item_repr():
    item = Item(record=Record(config={"file_identifier": "test", "title": "test"}))
    assert repr(item) == f"<Item / {item.identifier}>"


# Coverage test
def test_collection_repr():
    collection = Collection(config={"identifier": "test"})
    assert repr(collection) == f"<Collection / {collection.identifier}>"


# Coverage test
def test_record_lineage_none():
    record = Record(config={})
    assert record.lineage is None


# Coverage test
def test_record_transfer_options_none():
    record = Record(config={})
    assert record.transfer_options is None
