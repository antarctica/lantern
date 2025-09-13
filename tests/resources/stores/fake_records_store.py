import logging

from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, Store
from tests.resources.records.item_cat_collection_all import record as collection_all_supported
from tests.resources.records.item_cat_collection_min import record as collection_min_supported
from tests.resources.records.item_cat_data import record as data_all_supported
from tests.resources.records.item_cat_formatting import record as formatting_supported
from tests.resources.records.item_cat_licence import cc_record, ogl_record, ops_record, rights_reversed_record
from tests.resources.records.item_cat_product_all import record as product_all_supported
from tests.resources.records.item_cat_product_min import record as product_min_supported
from tests.resources.records.item_cat_product_replaced import record as product_replaced
from tests.resources.records.item_cat_product_restricted import record as product_restricted
from tests.resources.records.item_cat_pub_map import combined as product_published_map_combined
from tests.resources.records.item_cat_pub_map import side_a as product_published_map_side_a
from tests.resources.records.item_cat_pub_map import side_b as product_published_map_side_b
from tests.resources.records.item_cat_pub_map_diff import combined as product_diff_published_map_combined
from tests.resources.records.item_cat_pub_map_diff import side_a as product_diff_published_map_side_a
from tests.resources.records.item_cat_pub_map_diff import side_b as product_diff_published_map_side_b
from tests.resources.records.item_cat_verify import record as verify


class FakeRecordsStore(Store):
    """
    Simple in-memory store of fake/test records.

    Termed 'fake' rather than 'test' to avoid confusion between testing a store, vs. a store used for testing.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._records: list[RecordRevision] = []

    @property
    def _fake_records(self) -> list[RecordRevision]:
        return [
            collection_min_supported,
            collection_all_supported,
            product_min_supported,
            product_restricted,
            product_replaced,
            product_all_supported,
            formatting_supported,
            data_all_supported,
            verify,
            ogl_record,
            cc_record,
            ops_record,
            rights_reversed_record,
            product_published_map_combined,
            product_published_map_side_a,
            product_published_map_side_b,
            product_diff_published_map_combined,
            product_diff_published_map_side_a,
            product_diff_published_map_side_b,
        ]

    @staticmethod
    def _get_related_identifiers(record: RecordRevision) -> set[str]:
        """For building a single item with its direct relations."""
        return {
            related.identifier.identifier
            for related in record.identification.aggregations
            if related.identifier.identifier != record.file_identifier
        }

    @property
    def records(self) -> list[RecordRevision]:
        """All records."""
        return self._records

    def populate(self, inc_records: list[str] | None = None, inc_related: bool = False) -> None:
        """Load test records, optionally limited to a set of file identifiers and their direct dependencies."""
        if inc_records is None:
            inc_records = []

        if not inc_records:
            self._logger.info("Loading all test records")
            self._records = self._fake_records
            return

        records_indexed = {record.file_identifier: record for record in self._fake_records}
        for file_identifier in inc_records:
            if file_identifier not in records_indexed:
                self._logger.warning(f"No test record found with identifier '{file_identifier}', skipping.")
                continue

            record = records_indexed[file_identifier]
            self._records.append(record)
            if not inc_related:
                self._logger.info(f"Loading single test record '{file_identifier}'")
                continue

            self._logger.info(f"Loading single test record '{file_identifier}' with direct dependencies")
            related_records = [records_indexed[related_id] for related_id in self._get_related_identifiers(record)]
            self._records.extend(related_records)

    def get(self, file_identifier: str) -> RecordRevision:
        """
        Get record by file identifier.

        Raises RecordNotFoundError exception if not found.
        """
        for record in self.records:
            if record.file_identifier == file_identifier:
                return record
        raise RecordNotFoundError(file_identifier) from None
