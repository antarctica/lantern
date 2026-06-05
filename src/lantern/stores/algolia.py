import logging
from collections.abc import Collection
from functools import cached_property

from algoliasearch.http.exceptions import RequestException
from algoliasearch.search.client import SearchClientSync
from algoliasearch.search.models import FetchedIndex

from lantern.models.item.algolia.item import ItemAlgolia, ObjectRecord
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, StoreBase, StoreFrozenUnsupportedError


class AlgoliaStore(StoreBase):
    """
    Basic read-write store backed by a remote Algolia application/site.

    Primary used for writing record summaries for fast querying.
    """

    def __init__(self, logger: logging.Logger, app_id: str, api_key: str, index: str) -> None:
        self._logger = logger
        self._app_id = app_id
        self._api_key = api_key
        self._index = index

    def __len__(self) -> int:
        """Count of records in store."""
        return self._index_info.entries

    @property
    def frozen(self) -> bool:
        """Static value, as Algolia stores cannot be frozen."""
        return False

    @cached_property
    def _client(self) -> SearchClientSync:
        """Algolia API client."""
        return SearchClientSync(app_id=self._app_id, api_key=self._api_key)

    @property
    def _index_info(self) -> FetchedIndex:
        """
        Get index information.

        See https://www.algolia.com/doc/rest-api/search/list-indices#response-items for available fields.
        """
        try:
            return next(index for index in self._client.list_indices().items if index.name == self._index)
        except StopIteration:
            raise LookupError from None

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """
        Get some or all records filtered by file identifier.

        ... no way to pass a list of records to Algolia, will work up to 1k records. (add to future)
        ... Browse used instead of search to avoid analytics.

        Raises a `RecordsNotFoundError` exception if any selected records aren't found (i.e. all or nothing).
        """
        file_identifiers = file_identifiers or set()
        selected: list[RecordRevision] = []
        missing_fids = set()

        results: list[ObjectRecord] = [
            {"objectID": hit.object_id, **(hit.model_extra or {})}  # ty:ignore[missing-typed-dict-key]
            for hit in self._client.browse(index_name=self._index).hits
        ]  # ty:ignore[invalid-assignment]

        if len(file_identifiers) == 0:
            self._logger.info("Selecting all records.")
            return [ItemAlgolia(algolia_object=result).record for result in results]

        self._logger.info(f"Selecting {len(file_identifiers)} records.")
        results_indexed = {result["objectID"]: result for result in results}
        for file_identifier in file_identifiers:
            try:
                selected.append(ItemAlgolia(algolia_object=results_indexed[file_identifier]).record)
            except KeyError:
                missing_fids.add(file_identifier)

        if len(missing_fids) > 0:
            raise RecordsNotFoundError(missing_fids) from None

        return selected

    def select_one(self, file_identifier: str) -> RecordRevision:
        """
        Get specific record by file identifier.

        Returns a record constructed from an Algolia object which contain a limited subset of properties. These records
        therefore have limited utility and are not intended or supported for general use.

        Raises a `RecordNotFoundError` exception if not found.
        """
        self._logger.info(f"Selecting record '{file_identifier}'.")
        try:
            result: ObjectRecord = self._client.get_object(index_name=self._index, object_id=file_identifier)  # ty:ignore[invalid-assignment]
        except RequestException as e:
            raise RecordNotFoundError(file_identifier) from e
        return ItemAlgolia(algolia_object=result).record

    def push(self, records: Collection[RecordRevision]) -> None:
        """Add or update records in index."""
        self._logger.info(f"Upserting {len(records)} records.")
        data = [dict(ItemAlgolia(record).object) for record in records]
        self._client.save_objects(index_name=self._index, objects=data, wait_for_tasks=True)

    def freeze(self) -> None:
        """Attempt to freeze store."""
        raise StoreFrozenUnsupportedError() from None
