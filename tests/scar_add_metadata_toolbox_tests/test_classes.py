from datetime import datetime, timezone

import pytest

from scar_add_metadata_toolbox.classes import (
    Collection,
    CollectionInvalidSourceRecordError,
    CSWClient,
    Item,
    ItemInvalidSourceRecordError,
    MirrorRecord,
    MirrorRecordSummary,
    Record,
    RecordSummary,
)


# Coverage test
def test_csw_client_repr():
    csw_client = CSWClient(config={"endpoint": "test", "auth": {}})
    assert repr(csw_client) == f"<CSWClient / Endpoint: {csw_client._csw_endpoint}>"


# Coverage test
def test_record_summary_repr():
    record_summary = RecordSummary(config={"file_identifier": "test", "identification": {"title": {"value": "test"}}})
    assert repr(record_summary) == f"<RecordSummary / {record_summary.identifier} / {record_summary.title}>"


# Coverage test
def test_record_repr():
    record = Record(config={"file_identifier": "test", "identification": {"title": {"value": "test"}}})
    assert repr(record) == f"<Record / {record.identifier}>"


# Coverage test
def test_mirror_record_summary_repr():
    mirror_record_summary = MirrorRecordSummary(
        config={"file_identifier": "test", "identification": {"title": {"value": "test"}}}, published=False
    )
    assert repr(mirror_record_summary) == f"<MirrorRecordSummary / {mirror_record_summary.identifier} / Unpublished>"


# Coverage test
def test_mirror_record_repr():
    mirror_record = MirrorRecord(
        config={"file_identifier": "test", "identification": {"title": {"value": "test"}}}, published=False
    )
    assert repr(mirror_record) == f"<MirrorRecord / {mirror_record.identifier} / Unpublished>"


# Coverage test
def test_item_repr():
    item = Item(
        record=Record(config={"file_identifier": "test", "hierarchy_level": "dataset", "title": "test"}),
        related_summaries=[],
    )
    assert repr(item) == f"<Item / {item.identifier}>"


# Coverage test
def test_collection_repr():
    collection = Collection(
        record=Record(config={"file_identifier": "test", "hierarchy_level": "collection", "title": "test"})
    )
    assert repr(collection) == f"<Collection / {collection.identifier}>"


# Coverage test
def test_record_lineage_none():
    record = Record(config={})
    assert record.lineage is None


# Coverage test
def test_record_distributions_none():
    record = Record(config={})
    assert len(record.distributions) == 0


# Coverage test
def test_record_extent_none():
    record = Record(config={})
    assert len(record.extents) == 0


# Coverage test
def test_record_temporal_extent_none():
    record = Record(
        config={
            "identification": {
                "extents": [
                    {
                        "identifier": "bounding",
                        "geographic": {
                            "bounding_box": {
                                "west_longitude": -45.61521,
                                "east_longitude": -27.04976,
                                "south_latitude": -68.1511,
                                "north_latitude": -54.30761,
                            }
                        },
                    }
                ]
            }
        }
    )
    assert record.extents[0]["temporal"]["start"] is None
    assert record.extents[0]["temporal"]["end"] is None


# Coverage test
def test_record_temporal_extent_start_none():
    start = datetime.now(tz=timezone.utc)
    record = Record(
        config={
            "identification": {
                "extents": [
                    {
                        "identifier": "bounding",
                        "geographic": {
                            "bounding_box": {
                                "west_longitude": -45.61521,
                                "east_longitude": -27.04976,
                                "south_latitude": -68.1511,
                                "north_latitude": -54.30761,
                            }
                        },
                        "temporal": {"period": {"start": {"date": start}}},
                    }
                ]
            }
        }
    )
    assert record.extents[0]["temporal"]["start"] == start
    assert record.extents[0]["temporal"]["end"] is None


# Coverage test
def test_record_temporal_extent_end_none():
    end = datetime.now(tz=timezone.utc)
    record = Record(
        config={
            "identification": {
                "extents": [
                    {
                        "identifier": "bounding",
                        "geographic": {
                            "bounding_box": {
                                "west_longitude": -45.61521,
                                "east_longitude": -27.04976,
                                "south_latitude": -68.1511,
                                "north_latitude": -54.30761,
                            }
                        },
                        "temporal": {"period": {"end": {"date": end}}},
                    }
                ]
            }
        }
    )
    assert record.extents[0]["temporal"]["start"] is None
    assert record.extents[0]["temporal"]["end"] == end


# Coverage test
def test_item__format_spatial_reference_system_projections():
    test_cases = [
        {
            "in": {"value": "EPSG:3031", "href": "http://www.opengis.net/def/crs/EPSG/0/3031"},
            "out": "WGS 84 / Antarctic Polar Stereographic ([EPSG:3031](https://spatialreference.org/ref/epsg/3031/))",
        },
        {
            "in": {"value": "EPSG:4326", "href": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            "out": "WGS 84 ([EPSG:4326](https://spatialreference.org/ref/epsg/wgs-84/))",
        },
        {"in": {"value": "EPSG:unsupported", "href": "http://www.opengis.net/def/crs/EPSG/0/unsupported"}, "out": None},
    ]

    for test_case in test_cases:
        s = Item._format_spatial_reference_system(test_case["in"])
        assert s == test_case["out"]


# Coverage test
def test_item_invalid_record_type():
    with pytest.raises(ItemInvalidSourceRecordError):
        Item(record=Record(config={"hierarchy_level": "collection"}), related_summaries=[])


# Coverage test
def test_collection_invalid_record_type():
    with pytest.raises(CollectionInvalidSourceRecordError):
        Collection(record=Record(config={"hierarchy_level": "dataset"}))


# Coverage test
def test_collection_no_item_identifiers():
    collection = Collection(record=Record(config={"hierarchy_level": "collection"}))
    assert collection.item_identifiers is None
