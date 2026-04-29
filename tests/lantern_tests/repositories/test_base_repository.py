import logging

from lantern.config import Config
from lantern.models.record.record import Record
from tests.resources.repositories.fake_repository import FakeRepository
from tests.resources.stores.fake_records_store import FakeRecordsStore


class TestRepositoryBase:
    """Test repository abstract base class via fake repo implementation."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config, fx_fake_store: FakeRecordsStore):
        """Can create a catalogue instance."""
        cat = FakeRepository(logger=fx_logger, config=fx_config, store=fx_fake_store)
        assert isinstance(cat, FakeRepository)

    def test_select(self, fx_fake_repo: FakeRepository):
        """Can select one or more records."""
        results = fx_fake_repo.select()
        selected = results[0].file_identifier
        assert len(results) > 0
        assert len(fx_fake_repo.select(file_identifiers={selected})) == 1

    def test_upsert(self, fx_fake_repo: FakeRepository, fx_record_model_min: Record):
        """
        Can insert/update one or more records.

        This is essentially a no-op as there's nothing behind the fake repo.
        """
        results = fx_fake_repo.upsert([fx_record_model_min])
        assert results is None
