import pytest

# Coverage test
@pytest.mark.usefixtures("classes_csw_client")
def test_csw_client(classes_csw_client):
    assert repr(classes_csw_client) == f"<CSWClient / Endpoint: {classes_csw_client._csw_endpoint}>"


# Coverage test
@pytest.mark.usefixtures("classes_record_summary")
def test_record_summary(classes_record_summary):
    assert (
        repr(classes_record_summary)
        == f"<RecordSummary / {classes_record_summary.identifier} / {classes_record_summary.title}>"
    )


# Coverage test
@pytest.mark.usefixtures("classes_record")
def test_record(classes_record):
    assert repr(classes_record) == f"<Record / {classes_record.identifier}>"


# Coverage test
@pytest.mark.usefixtures("classes_mirror_record_summary")
def test_mirror_record_summary(classes_mirror_record_summary):
    assert (
        repr(classes_mirror_record_summary)
        == f"<MirrorRecordSummary / {classes_mirror_record_summary.identifier} / Unpublished>"
    )


# Coverage test
@pytest.mark.usefixtures("classes_mirror_record")
def test_mirror_record(classes_mirror_record):
    assert repr(classes_mirror_record) == f"<MirrorRecord / {classes_mirror_record.identifier} / Unpublished>"


# Coverage test
@pytest.mark.usefixtures("classes_item")
def test_item(classes_item):
    assert repr(classes_item) == f"<Item / {classes_item.identifier}>"


# Coverage test
@pytest.mark.usefixtures("classes_collection")
def test_collection(classes_collection):
    assert repr(classes_collection) == f"<Collection / {classes_collection.identifier}>"
