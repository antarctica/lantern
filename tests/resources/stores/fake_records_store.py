import logging
from copy import copy

from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, Store
from tests.resources.records.item_cat_collection_all import record as collection_all_supported
from tests.resources.records.item_cat_collection_min import record as collection_min_required
from tests.resources.records.item_cat_data import record as data_all_supported
from tests.resources.records.item_cat_formatting import record as formatting_supported
from tests.resources.records.item_cat_initiative_all import record as initiative_all_supported
from tests.resources.records.item_cat_initiative_min import record as initiative_min_required
from tests.resources.records.item_cat_licence import (
    cc_record,
    magic_products_record,
    ogl_record,
    ops_record,
    rights_reversed_record,
)
from tests.resources.records.item_cat_product_all import record as product_all_supported
from tests.resources.records.item_cat_product_min import record as product_min_required
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

    Termed 'fake' rather than 'test' to avoid confusion between testing a store, and a store used for that testing.
    """

    def __init__(self, logger: logging.Logger, frozen: bool = False) -> None:
        self._logger = logger
        self._records: list[RecordRevision] = self._fake_records
        self._frozen = frozen

    @property
    def frozen(self) -> bool:
        """
        Whether store can be modified/updated.

        Not used for anything in this store but tracked for checking in tests
        """
        return self._frozen

    @property
    def _fake_records(self) -> list[RecordRevision]:
        records = [
            initiative_min_required,
            initiative_all_supported,
            collection_min_required,
            collection_all_supported,
            product_min_required,
            product_restricted,
            product_replaced,
            product_all_supported,
            formatting_supported,
            data_all_supported,
            verify,
            ogl_record,
            cc_record,
            ops_record,
            magic_products_record,
            rights_reversed_record,
            product_published_map_combined,
            product_published_map_side_a,
            product_published_map_side_b,
            product_diff_published_map_combined,
            product_diff_published_map_side_a,
            product_diff_published_map_side_b,
        ]
        return [copy(record) for record in records]

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """
        Get all records optionally filtered by file identifier.

        Raises a `RecordsNotFoundError` exception if any selected record not found.
        """
        if file_identifiers is None or len(file_identifiers) == 0:
            return sorted(self._fake_records, key=lambda r: r.file_identifier)

        records = []
        for record in self._records:
            if record.file_identifier in file_identifiers:
                records.append(record)

        missing_ids = file_identifiers - {r.file_identifier for r in records}
        if not missing_ids:
            return sorted(records, key=lambda r: r.file_identifier)
        raise RecordsNotFoundError(missing_ids) from None

    def select_one(self, file_identifier: str) -> RecordRevision:
        """
        Get record by file identifier.

        Raises a `RecordNotFoundError` exception if not found.
        """
        try:
            return self.select(file_identifiers={file_identifier})[0]
        except RecordsNotFoundError as e:
            raise RecordNotFoundError(file_identifier) from e
