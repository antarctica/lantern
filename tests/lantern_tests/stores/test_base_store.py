import pytest

from lantern.models.record.record import Record
from lantern.stores.base import RecordNotFoundError
from tests.resources.stores.fake_records_store import FakeRecordsStore


class TestRecordNotFoundError:
    """Test record not found exception."""

    def test_init(self):
        """Can initialise exception."""
        file_identifier = "x"

        e = RecordNotFoundError(file_identifier=file_identifier)

        assert e.file_identifier == "x"
        assert str(e) == f"Record '{file_identifier}' not found."


class TestBaseStore:
    """
    Test base store.

    The base store is an abstract class so for testing the FakeRecordsStore is used.
    """

    def test_len(self, fx_fake_store: FakeRecordsStore):
        """Can get number of records in store."""
        assert len(fx_fake_store) == 0
        fx_fake_store.populate()
        assert len(fx_fake_store) > 0

    def test_records(self, fx_fake_store: FakeRecordsStore):
        """Can get all records from store."""
        fx_fake_store.populate()
        assert len(fx_fake_store.records) > 0
        assert all(isinstance(record, Record) for record in fx_fake_store.records)

    def test_get(self, fx_fake_store: FakeRecordsStore):
        """Can get a specific record from store."""
        fx_fake_store.populate()
        expected = fx_fake_store.records[0]
        assert fx_fake_store.get(expected.file_identifier) == expected

    def test_get_unknown(self, fx_fake_store: FakeRecordsStore):
        """Can raise error when record is not found."""
        with pytest.raises(RecordNotFoundError):
            fx_fake_store.get("x")
