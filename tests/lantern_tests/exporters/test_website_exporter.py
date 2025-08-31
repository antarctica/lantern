import logging
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.exporters.website import WebsiteSearchExporter, WordPressClient, WordPressSearchItem
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation, Constraint
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.models.item.website.search import ItemWebsiteSearch
from lantern.models.record.revision import RecordRevision
from tests.conftest import _get_record_open, _revision_config_min


class TestWordPressSearchItem:
    """Minimal tests for stop-gap WordPressSearchItem model."""

    def test_init(self):
        """Can create an instance directly."""
        item = WordPressSearchItem(
            title="x",
            content="x",
            file_identifier="x",
            file_revision="x",
            href="x",
            hierarchy_level="x",
            publication_date="x",
            edition="x",
            source="x",
            href_thumbnail="x",
        )
        assert isinstance(item, WordPressSearchItem)

    def test_loads(self, fx_revision_model_min: RecordRevision):
        """Can create an instance from a ItemWebsiteSearch instance."""
        source = "y"
        base_url = "z"
        search_item = ItemWebsiteSearch(record=fx_revision_model_min, source=source, base_url=base_url)
        item = WordPressSearchItem.loads(search_item)

        assert item.source == source
        assert item.href == search_item.dumps()["content"]["href"]


class TestWordPressClient:
    """Tests for proof of concept WordPress API client."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config):
        """Can initialise."""
        client = WordPressClient(logger=fx_logger, config=fx_config)
        assert isinstance(client, WordPressClient)

    def test_posts(self, mocker: MockerFixture, fx_wordpress_client: WordPressClient):
        """Can get posts of given type indexed by ID."""
        mocker.patch.object(
            fx_wordpress_client,
            "_fetch_posts",
            return_value=[
                {
                    "id": 123,
                    "slug": "x",
                    "status": "publish",
                    "type": "data_catalogue_stub",
                    "link": "http://example.com/items/x",
                    "title": {"raw": "x", "rendered": "x"},
                    "content": {
                        "raw": r"<p>x</p>",
                        "rendered": "<p>x</p>\n",
                        "protected": False,
                        "block_version": 0,
                    },
                    "meta": {
                        "file_identifier": "x",
                        "file_revision": "x",
                        "href": "http://example.com/items/x",
                        "hierarchy_level": "DATASET",
                        "publication_date": "2014-06-30",
                        "edition": "",
                        "source": "x",
                        "href_thumbnail": "",
                    },
                }
            ],
        )
        results = fx_wordpress_client.posts
        assert isinstance(results, dict)
        assert len(results) > 0
        assert 123 in results

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("paginate", [False, True])
    def test_fetch_posts(self, fx_wordpress_client: WordPressClient, paginate: bool):
        """Can get posts of given type."""
        results = fx_wordpress_client._fetch_posts()
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("post_id", [None, 123])
    def test_upsert(
        self, fx_wordpress_client: WordPressClient, fx_revision_model_min: RecordRevision, post_id: int | None
    ):
        """Can insert or update a post of a given type."""
        item = ItemWebsiteSearch(record=fx_revision_model_min, source="x", base_url="x")
        fields = asdict(WordPressSearchItem.loads(item))
        fx_wordpress_client.upsert(fields=fields, post_id=post_id)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_delete(self, fx_wordpress_client: WordPressClient):
        """Can delete a post of a given type."""
        fx_wordpress_client.delete(post_id="115")


class TestWebsiteSearchExporter:
    """Test public website search exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)

        exporter = WebsiteSearchExporter(
            config=mock_config, s3=s3_client, logger=fx_logger, get_record=_get_record_open
        )

        assert isinstance(exporter, WebsiteSearchExporter)
        assert exporter.name == "Public Website search results"

    def test_get_superseded_records(
        self, fx_exporter_website_search: WebsiteSearchExporter, fx_revision_model_min: RecordRevision
    ):
        """Can determine superseded records."""
        successor = deepcopy(fx_revision_model_min)
        successor.file_identifier = "y"
        successor.identification.aggregations.append(
            Aggregation(
                identifier=Identifier(identifier=fx_revision_model_min.file_identifier, namespace="data.bas.ac.uk"),
                association_type=AggregationAssociationCode.REVISION_OF,
            )
        )

        results = fx_exporter_website_search._get_superseded_records(records=[fx_revision_model_min, successor])
        assert results == [fx_revision_model_min.file_identifier]

    @staticmethod
    def _get_record_in_scope(identifier: str) -> RecordRevision:
        """Record lookup method for testing in_scope_items method."""
        record = RecordRevision.loads(deepcopy(_revision_config_min()))
        record.file_identifier = identifier

        if identifier == "in_scope":
            record.identification.constraints.append(
                Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
            )
            record.identification.aggregations.append(
                Aggregation(
                    identifier=Identifier(identifier="out_scope_superseded", namespace="data.bas.ac.uk"),
                    association_type=AggregationAssociationCode.REVISION_OF,
                )
            )

        return record

    def test_in_scope_items(self, fx_exporter_website_search: WebsiteSearchExporter):
        """Can select items in-scope for inclusion in website search."""
        fx_exporter_website_search._get_record = self._get_record_in_scope
        fx_exporter_website_search.selected_identifiers = {"out_scope_superseded", "out_scope_not_open", "in_scope"}

        results = fx_exporter_website_search._in_scope_items
        assert len(results) == 1
        assert results[0].resource_id == "in_scope"

    def test_in_scope_references(
        self,
        mocker: MockerFixture,
        fx_exporter_website_search: WebsiteSearchExporter,
        fx_revision_model_min: RecordRevision,
    ):
        """Can get in-scope record references."""
        record = fx_revision_model_min
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_in_scope_items",
            new_callable=PropertyMock,
            return_value=[ItemWebsiteSearch(record=record, source="x", base_url="x")],
        )

        results = fx_exporter_website_search._in_scope_references
        assert len(results) == 1
        assert results == {record.file_identifier: record.file_revision}

    def test_remote_references(
        self,
        mocker: MockerFixture,
        fx_exporter_website_search: WebsiteSearchExporter,
        fx_revision_model_min: RecordRevision,
    ):
        """Can get record references from remote resources."""
        file_identifier = "x"
        file_revision = "y"
        post_id = "z"
        mocker.patch.object(
            type(fx_exporter_website_search._wordpress_client),
            "posts",
            new_callable=PropertyMock,
            return_value={
                post_id: {"id": post_id, "meta": {"file_identifier": file_identifier, "file_revision": file_revision}}
            },
        )

        results = fx_exporter_website_search._remote_references
        assert len(results) == 1
        assert results == {file_identifier: (file_revision, post_id)}

    @staticmethod
    def _get_record_new_outdated(identifier: str) -> RecordRevision:
        """Record lookup method for testing new_outdated_items method."""
        _revisions = {"a": "1", "b": "2", "c": "3"}

        record = RecordRevision.loads(deepcopy(_revision_config_min()))
        record.file_identifier = identifier
        record.file_revision = _revisions[identifier]
        record.identification.constraints.append(
            Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
        )

        return record

    def test_new_outdated_items(
        self,
        mocker: MockerFixture,
        fx_exporter_website_search: WebsiteSearchExporter,
        fx_revision_model_min: RecordRevision,
    ):
        """Can determine new and outdated items from loaded local items and remote items."""
        new_item = {"file_identifier": "a", "file_revision": "1"}
        outdated_item = {"file_identifier": "b", "file_revision": "2"}
        unchanged_item = {"file_identifier": "c", "file_revision": "3"}

        fx_exporter_website_search._get_record = self._get_record_new_outdated
        fx_exporter_website_search.selected_identifiers = {
            reference["file_identifier"] for reference in [new_item, outdated_item, unchanged_item]
        }

        # include unchanged and previous revision of outdated item remotely
        remote_references = {
            unchanged_item["file_identifier"]: (unchanged_item["file_revision"], "x"),
            outdated_item["file_identifier"]: ("0", "x"),
        }
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_remote_references",
            new_callable=PropertyMock,
            return_value=remote_references,
        )

        expected = sorted([new_item["file_identifier"], outdated_item["file_identifier"]])
        results = sorted([item.resource_id for item in fx_exporter_website_search._new_outdated_items])
        assert results == expected

    def test_orphaned_items(
        self,
        mocker: MockerFixture,
        fx_exporter_website_search: WebsiteSearchExporter,
        fx_revision_model_min: RecordRevision,
    ):
        """Can determine items that exist remotely but not locally."""
        item_a = {"file_identifier": "a", "file_revision": "1", "post_id": 101}
        item_b = {"file_identifier": "b", "file_revision": "2", "post_id": 102}

        # include some items locally
        local_references = {reference["file_identifier"]: reference["file_revision"] for reference in [item_a]}
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_in_scope_references",
            new_callable=PropertyMock,
            return_value=local_references,
        )
        # include all items remotely
        remote_references = {
            item_a["file_identifier"]: (item_a["file_revision"], item_a["post_id"]),
            item_b["file_identifier"]: (item_b["file_revision"], item_b["post_id"]),
        }
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_remote_references",
            new_callable=PropertyMock,
            return_value=remote_references,
        )

        expected_items = {item_b["file_identifier"]: item_b["post_id"]}

        assert fx_exporter_website_search._orphaned_items == expected_items

    def test_export(self, fx_exporter_website_search: WebsiteSearchExporter):
        """Cannot export."""
        with pytest.raises(NotImplementedError):
            fx_exporter_website_search.export()

    def test_publish(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_exporter_website_search: WebsiteSearchExporter,
        fx_revision_model_min: RecordRevision,
    ):
        """Can add, update or delete items from WordPress site as needed."""
        new_item = {"file_identifier": "a", "file_revision": "a1", "post_id": 1}
        outdated_item_local = {"file_identifier": "b", "file_revision": "b2", "post_id": 2}
        outdated_item_remote = {"file_identifier": "b", "file_revision": "b1", "post_id": 2}
        orphaned_item = {"file_identifier": "c", "file_revision": "c1", "post_id": 3}
        unchanged_item = {"file_identifier": "d", "file_revision": "d1", "post_id": 4}
        _items = [new_item, outdated_item_local, outdated_item_remote, unchanged_item]

        # remote references
        remote_references = {
            item["file_identifier"]: (item["file_revision"], item["post_id"])
            for item in [outdated_item_remote, orphaned_item, unchanged_item]
        }
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_remote_references",
            new_callable=PropertyMock,
            return_value=remote_references,
        )

        # items
        items: dict[str, ItemWebsiteSearch] = {}
        fx_revision_model_min.identification.constraints.append(
            Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
        )
        for _item in _items:
            record = deepcopy(fx_revision_model_min)
            record.file_identifier = _item["file_identifier"]
            record.file_revision = _item["file_revision"]
            items[_item["file_identifier"]] = ItemWebsiteSearch(record=record, source="x", base_url="x")
        # local in-scope items
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_in_scope_items",
            new_callable=PropertyMock,
            return_value=[
                items[new_item["file_identifier"]],
                items[outdated_item_local["file_identifier"]],
                items[unchanged_item["file_identifier"]],
            ],
        )
        # local new/outdated items
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_new_outdated_items",
            new_callable=PropertyMock,
            return_value=[
                items[new_item["file_identifier"]],
                items[outdated_item_local["file_identifier"]],
            ],
        )
        # remote orphaned items
        mocker.patch.object(
            type(fx_exporter_website_search),
            "_orphaned_items",
            new_callable=PropertyMock,
            return_value={orphaned_item["file_identifier"]: orphaned_item["post_id"]},
        )

        mocker.patch.object(fx_exporter_website_search._wordpress_client, "upsert", return_value=None)
        mocker.patch.object(fx_exporter_website_search._wordpress_client, "delete", return_value=None)

        fx_exporter_website_search.publish()
        assert f"Synced item for record '{new_item['file_identifier']}'" in caplog.text
        assert f"Synced item for record '{outdated_item_local['file_identifier']}'" in caplog.text
        assert f"Deleted orphaned item for record '{orphaned_item['file_identifier']}'" in caplog.text
        assert f"Item for record '{unchanged_item['file_identifier']}' unchanged, skipped." in caplog.text
