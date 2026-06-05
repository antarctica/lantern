import logging

import pytest
from algoliasearch.search.models import FetchedIndex

from lantern.models.item.algolia.item import ObjectRecord
from lantern.models.record.revision import RecordRevision
from lantern.stores.algolia import AlgoliaStore
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, StoreFrozenUnsupportedError


class TestAlgoliaStore:
    """Test Algolia store."""

    def test_init(self, fx_logger: logging.Logger):
        """Can initialise store."""
        store = AlgoliaStore(logger=fx_logger, app_id="x", api_key="x", index="x")
        assert isinstance(store, AlgoliaStore)
        assert store.frozen is False

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_index_info(self, fx_algolia_store: AlgoliaStore):
        """Can get information about selected index."""
        result = fx_algolia_store._index_info
        assert isinstance(result, FetchedIndex)
        assert result.name == fx_algolia_store._index

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.cov()
    def test_index_info_error(self, fx_algolia_store: AlgoliaStore):
        """Getting index information raises error if index does not exist."""
        fx_algolia_store._index = "invalid"

        with pytest.raises(LookupError):
            _ = fx_algolia_store._index_info

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_len(self, fx_algolia_store: AlgoliaStore):
        """Can get count of records in store."""
        assert len(fx_algolia_store) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("selected", [None, set(), {"x"}, {"x", "invalid"}])
    def test_select(self, fx_algolia_store: AlgoliaStore, selected: set[str] | None):
        """Can get selected records that exist."""
        expected_length = len(selected) if selected else 2  # local arbitrary value

        if selected is not None and "invalid" in selected:
            with pytest.raises(RecordsNotFoundError) as exc_info:
                fx_algolia_store.select(file_identifiers=selected)
            assert exc_info.value.file_identifiers == {"invalid"}
            return

        result = fx_algolia_store.select(file_identifiers=selected)
        assert len(result) == expected_length
        assert all(isinstance(r, RecordRevision) for r in result)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("selected", ["x", "invalid"])
    def test_select_one(self, fx_algolia_store: AlgoliaStore, selected: str):
        """Can get a record from an object if it exists."""
        if selected == "invalid":
            with pytest.raises(RecordNotFoundError):
                fx_algolia_store.select_one(file_identifier=selected)
            return

        result = fx_algolia_store.select_one(selected)
        assert isinstance(result, RecordRevision)
        assert result.file_identifier == selected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("mode", ["insert", "update"])
    def test_push(self, fx_algolia_store: AlgoliaStore, fx_revision_model_min: RecordRevision, mode: str):
        """Can create or update objects in the remote index."""
        fx_revision_model_min.identification.purpose = "x"
        if mode == "update":
            fx_revision_model_min.file_revision = "xx"

        fx_algolia_store.push([fx_revision_model_min])
        result: ObjectRecord = fx_algolia_store._client.get_object(
            index_name=fx_algolia_store._index, object_id=fx_revision_model_min.file_identifier
        )
        assert result["objectRevID"] == fx_revision_model_min.file_revision

    @pytest.mark.cov()
    def test_freeze(self, fx_algolia_store: AlgoliaStore):
        """Cannot freeze store (unsupported when not cached)."""
        with pytest.raises(StoreFrozenUnsupportedError):
            fx_algolia_store.freeze()
