import logging

import pytest

from lantern.models.record.record import Record
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError
from tests.resources.stores.fake_records_store import FakeRecordsStore


class TestRecordNotFoundError:
    """Test record not found exception."""

    def test_init(self):
        """Can initialise exception."""
        file_identifier = "x"

        e = RecordNotFoundError(file_identifier=file_identifier)

        assert e.file_identifier == "x"
        assert str(e) == f"Record '{file_identifier}' not found."


class TestRecordsNotFoundError:
    """Test records not found exception."""

    def test_init(self):
        """Can initialise exception."""
        file_identifiers = {"x", "y"}

        e = RecordsNotFoundError(file_identifiers=file_identifiers)

        assert e.file_identifiers == {"x", "y"}
        assert str(e) == f"Records '{', '.join(file_identifiers)}' not found."


class TestBaseStore:
    """
    Test base store.

    The base store is an abstract class so for testing the FakeRecordsStore is used.
    """

    def test_len(self, fx_fake_store: FakeRecordsStore):
        """Can get count of records in store."""
        assert len(fx_fake_store) > 0

    @pytest.mark.cov()
    @pytest.mark.parametrize("frozen", [False, True])
    def test_frozen(self, fx_logger: logging.Logger, frozen: bool):
        """Can get whether store is frozen."""
        store = FakeRecordsStore(logger=fx_logger, frozen=frozen)
        assert store.frozen is frozen

    def test_ref(self, fx_logger: logging.Logger):
        """Can get unique instances of records from store."""
        store_a = FakeRecordsStore(logger=fx_logger)
        store_b = FakeRecordsStore(logger=fx_logger)
        assert id(store_a._records[0]) != id(store_b._records[0])

    def test_select(self, fx_fake_store: FakeRecordsStore):
        """Can get all records from store."""
        assert all(isinstance(record, Record) for record in fx_fake_store.select())

    def test_select_unknown(self, fx_fake_store: FakeRecordsStore):
        """Cannot get one or more unknown records from store."""
        with pytest.raises(RecordsNotFoundError):
            fx_fake_store.select(file_identifiers={"invalid"})

    def test_select_one(self, fx_fake_store: FakeRecordsStore):
        """Can get a specific record from store."""
        expected = fx_fake_store._records[0]

        assert fx_fake_store.select_one(expected.file_identifier) == expected

    def test_select_one_unknown(self, fx_fake_store: FakeRecordsStore):
        """Cannot get an unknown record."""
        with pytest.raises(RecordNotFoundError):
            fx_fake_store.select_one("invalid")
