import json
import logging
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError

from lantern.models.record import Record
from lantern.models.record.summary import RecordSummary
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import GitLabStore, RemoteStoreUnavailableError
from tests.resources.stores.fake_records_store import FakeRecordsStore


class TestGitLabStore:
    """Test GitLab store."""

    def test_init(self, fx_logger: logging.Logger):
        """Can initialise store."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"

        GitLabStore(
            logger=fx_logger,
            endpoint="https://gitlab.example.com",
            access_token="x",  # noqa: S106
            project_id="x",
            cache_path=cache_path,
        )

    def test_len(self, fx_gitlab_store_pop: GitLabStore):
        """
        Can get number of records loaded into store.

        Specifically records in the local subset, rather than records in the wider cache or remote repository.
        """
        assert len(fx_gitlab_store_pop) == 1

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("expected", [True, False])
    def test_is_online(self, mocker: MockerFixture, fx_gitlab_store: GitLabStore, expected: bool):
        """Can check if remote repository is available."""
        if not expected:
            mocker.patch.object(GitLabStore, "_project", new_callable=PropertyMock, side_effect=ConnectionError())

        assert fx_gitlab_store._is_online() == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_project(self, fx_gitlab_store: GitLabStore):
        """Can get the remote GitLab project object for the store."""
        result = fx_gitlab_store._project
        assert result.id == 1234

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_head_commit_id(self, fx_gitlab_store: GitLabStore):
        """Can get the ID of the latest commit in the remote repository."""
        result = fx_gitlab_store._head_commit_id
        assert result == "abc123"

    # summary and record methods tested in base store tests

    def test_load_add_record(self, fx_gitlab_store_cached: GitLabStore):
        """Can load a record config from the local cache as a Record and add to local (loaded) subset."""
        records_path = fx_gitlab_store_cached._cache_path / fx_gitlab_store_cached._records_path_name
        record_path = records_path / "a1b2c3.json"
        assert len(fx_gitlab_store_cached.records) == 0

        record = fx_gitlab_store_cached._load_record(record_path)
        assert isinstance(record, Record)

        fx_gitlab_store_cached._add_record(record)
        assert len(fx_gitlab_store_cached.records) == 1

    def test_load_add_summaries(self, fx_gitlab_store_cached: GitLabStore):
        """Can load a set of record configs from the local cache as RecordSummaries and add to local (local) subset."""
        assert len(fx_gitlab_store_cached.summaries) == 0
        fx_gitlab_store_cached._add_summaries(file_identifiers=["a1b2c3"])
        assert len(fx_gitlab_store_cached.summaries) == 1
        assert isinstance(fx_gitlab_store_cached.summaries[0], RecordSummary)

    @pytest.mark.parametrize("exists", [True, False])
    def test_purge(self, fx_gitlab_store_pop: GitLabStore, exists: bool):
        """Can purge loaded records with or without an existing local cache."""
        if not exists:
            shutil.rmtree(fx_gitlab_store_pop._cache_path)
            assert not fx_gitlab_store_pop._cache_path.exists()

        fx_gitlab_store_pop.purge()

        assert len(fx_gitlab_store_pop.records) == 0
        assert len(fx_gitlab_store_pop.summaries) == 0
        assert not fx_gitlab_store_pop._cache_path.exists()

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(("exists", "current"), [(False, False), (True, True), (True, False)])
    def test_cache_is_current(self, fx_gitlab_store_cached: GitLabStore, exists: bool, current: bool):
        """Can check if the local cache is up-to-date with the remote repository."""
        if not exists:
            shutil.rmtree(fx_gitlab_store_cached._cache_path)
            assert not fx_gitlab_store_cached._cache_path.exists()

        result = fx_gitlab_store_cached._cache_is_current()
        assert result == current

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("exists", [True, False])
    def test_create_cache(self, fx_gitlab_store: GitLabStore, exists: bool):
        """Can create a local cache from the remote repository."""
        expected_commit_id = "abc123"
        expected_record_name = "a1b2c3.json"
        expected_file_identifier = "x"
        expected_sha1 = "e9dc256d287ce17eb8feeddc4cb34e53da61d459"

        initial_mtime = 0
        if exists:
            fx_gitlab_store._cache_path.mkdir(parents=True, exist_ok=True)
            assert fx_gitlab_store._cache_path.exists()
            initial_mtime = fx_gitlab_store._cache_path.stat().st_mtime

        fx_gitlab_store._create_cache()

        assert fx_gitlab_store._cache_path.exists()
        assert fx_gitlab_store._cache_path.stat().st_mtime != initial_mtime

        records_path = fx_gitlab_store._cache_path / fx_gitlab_store._records_path_name
        assert records_path.exists()
        assert records_path.joinpath(expected_record_name).exists()

        assert fx_gitlab_store._cache_summaries_path.exists()
        with fx_gitlab_store._cache_summaries_path.open() as f:
            summaries = json.load(f)
            assert expected_file_identifier in summaries["summaries"]

        assert fx_gitlab_store._cache_head_path.exists()
        with fx_gitlab_store._cache_head_path.open() as f:
            head_commit = json.load(f)
            assert head_commit["id"] == expected_commit_id

        assert fx_gitlab_store._cache_index_path.exists()
        with fx_gitlab_store._cache_index_path.open() as f:
            index = json.load(f)
            assert index["index"][expected_file_identifier] == expected_sha1

    @pytest.mark.parametrize(
        ("online", "cached", "current"),
        [(False, False, False), (True, False, False), (False, True, False), (True, True, False), (True, True, True)],
    )
    def test_ensure_cache(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_gitlab_store_cached: GitLabStore,
        online: bool,
        cached: bool,
        current: bool,
    ):
        """Can make sure an up-to-date local cache of the remote repository exists."""
        fx_gitlab_store_cached._online = online
        if not cached:
            shutil.rmtree(fx_gitlab_store_cached._cache_path)
            assert not fx_gitlab_store_cached._cache_path.exists()
        if online and not cached:
            fx_gitlab_store_cached._create_cache()
        mocker.patch.object(fx_gitlab_store_cached, "_cache_is_current", return_value=current)

        if not online and not cached:
            with pytest.raises(RemoteStoreUnavailableError):
                fx_gitlab_store_cached._ensure_cache()
            return

        fx_gitlab_store_cached._ensure_cache()

        if not online:
            assert "Cannot check if records cache is current, loading possibly stale records" in caplog.text

        if online and not current:
            assert "Cached records are not up to date, reloading from GitLab" in caplog.text

        if online and current:
            assert "Records cache exists and is current, no changes needed." in caplog.text

        assert fx_gitlab_store_cached._cache_path.exists()

    @pytest.mark.parametrize(
        ("include", "exclude", "include_related", "expected"),
        [
            ([], [], False, ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea", "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"]),
            (["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea"], [], False, ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea"]),
            (
                ["53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"],
                [],
                True,
                [
                    "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",
                    "bcacfe16-52da-4b26-94db-8a567e4292db",
                    "dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    "e30ac1c0-ed6a-49bd-8ca3-205610bf91bf",
                ],
            ),
            ([], ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea"], False, ["53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"]),
        ],
    )
    def test_filter_cache(
        self,
        fx_gitlab_store: GitLabStore,
        include: list[str],
        exclude: list[str],
        include_related: bool,
        expected: list[str],
    ):
        """
        Can filter records loaded from the cache by including or excluding certain records.

        Populates cache in GitLab store with the records in the FakeRecordsStore to give a pool of records to filter.

        - 8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea is a single standalone record
        - 53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2 is a record with two related records
        """
        fake_store = FakeRecordsStore(logger=fx_gitlab_store._logger)
        _inc_records = ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea", "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"]
        fake_store.populate(
            inc_records=_inc_records if not include_related else [],
            inc_related=include_related,
        )
        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)
            for record in fake_store.records:
                config_path = temp_path / f"{record.file_identifier}.json"
                with config_path.open("w") as f:
                    json.dump(record.dumps(), f, indent=2)
            config_paths = list(temp_path.glob("*.json"))
            fx_gitlab_store._populate_cache(config_paths=config_paths, head_commit={"x": "x"})

            fx_gitlab_store._filter_cache(inc_records=include, exc_records=exclude, inc_related=include_related)

            results = [record.file_identifier for record in fx_gitlab_store.records]
            assert sorted(expected) == sorted(results)

    @pytest.mark.cov()
    def test_filter_cache_invalid(self, fx_gitlab_store_cached: GitLabStore):
        """Cannot filter records by including and excepting records at the same time."""
        with pytest.raises(ValueError, match="Including and excluding records is not supported."):
            fx_gitlab_store_cached._filter_cache(inc_records=["x"], exc_records=["x"], inc_related=False)

    def test_get_remote_hashed_path(self, fx_gitlab_store: GitLabStore):
        """Can get the path to a record within the remote repository."""
        value = "123456.ext"
        expected = f"{fx_gitlab_store._records_path_name}/12/34/{value}"

        assert fx_gitlab_store._get_remote_hashed_path(value) == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            ("none", {"additions_ids": 0, "additions_total": 0, "updates_ids": 0, "updates_total": 0}),
            ("add", {"additions_ids": 1, "additions_total": 2, "updates_ids": 0, "updates_total": 0}),
            ("update", {"additions_ids": 0, "additions_total": 0, "updates_ids": 1, "updates_total": 2}),
        ],
    )
    def test_commit(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        fx_gitlab_store_cached: GitLabStore,
        fx_record_minimal_iso: Record,
        mode: str,
        expected: dict[str, int],
    ):
        """Can create, update or delete one or more records in the remote repository."""
        records = []
        if mode == "add":
            fx_record_minimal_iso.file_identifier = "d4e5f6"
            records.append(fx_record_minimal_iso)
        if mode == "update":
            mocker.patch.object(fx_gitlab_store_cached, "_cache_is_current", return_value=True)
            fx_gitlab_store_cached.populate()
            record = fx_gitlab_store_cached.get("a1b2c3")
            record.identification.edition = str(1)
            records.append(record)

        results = fx_gitlab_store_cached._commit(records=records, title="x", message="x", author=("x", "x@example.com"))
        assert results == expected
        if mode == "none":
            assert "No actions to perform, skipping" in caplog.text
            return
        if mode == "add":
            assert "Committing 1 added records across 2 new files, 0 updated records" in caplog.text
        if mode == "update":
            assert "Committing 0 additional records, 1 updated records across 2 modified files" in caplog.text

    def test_populate(self, fx_gitlab_store_cached: GitLabStore):
        """
        Can populate the store with records from the remote repository, via a local cache.

        High level public method.
        """
        assert len(fx_gitlab_store_cached.records) == 0
        assert len(fx_gitlab_store_cached.summaries) == 0

        fx_gitlab_store_cached.populate()
        assert len(fx_gitlab_store_cached.records) > 0
        assert len(fx_gitlab_store_cached.summaries) > 0

    @pytest.mark.parametrize("exists", [True, False])
    def test_get(self, fx_gitlab_store_pop: GitLabStore, exists: bool):
        """Can get a record if loaded into the local subset via `populate()`."""
        value = "a1b2c3" if exists else "invalid"

        if not exists:
            with pytest.raises(RecordNotFoundError):
                fx_gitlab_store_pop.get(value)
            return

        result = fx_gitlab_store_pop.get(value)
        assert isinstance(result, Record)
        assert result.file_identifier == value

    @pytest.mark.vcr
    # @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("mode", "stats"),
        [
            ("none", {"additions": 0, "updates": 0}),
            ("noop", {"additions": 0, "updates": 0}),
            ("add", {"additions": 1, "updates": 0}),
            ("update", {"additions": 0, "updates": 1}),
        ],
    )
    def test_push(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        fx_gitlab_store_cached: GitLabStore,
        mode: str,
        stats: dict[str, int],
    ):
        """
        Can create, update or delete Records in the remote repository.

        High level public method.

        No-op case for submitted records that don't trigger any changes to remote repo.
        """
        records = [] if mode == "none" else ["x"]
        mocker.patch.object(fx_gitlab_store_cached, "_commit", return_value=stats)
        mocker.patch.object(fx_gitlab_store_cached, "_cache_is_current", return_value=True)
        mocker.patch.object(fx_gitlab_store_cached, "_create_cache", return_value=None)
        mocker.patch.object(fx_gitlab_store_cached, "_add_record", return_value=None)

        fx_gitlab_store_cached.push(records=records, title="title", message="x", author=("x", "x@example.com"))

        if mode == "none":
            assert "No records to push, skipping" in caplog.text
        elif mode == "noop":
            assert "No records pushed, skipping cache invalidation" in caplog.text
        else:
            assert "Recreating cache to reflect pushed changes" in caplog.text
