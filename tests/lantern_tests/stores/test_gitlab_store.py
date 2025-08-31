import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, PropertyMock

import pytest
from gitlab import Gitlab
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.config import Config
from lantern.models.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import (
    CacheIntegrityError,
    GitLabLocalCache,
    GitLabStore,
    RemoteStoreUnavailableError,
    _fetch_record_commit,
)


class TestGitLabLocalCache:
    """Test GitLab local cache."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config):
        """Can initialise store."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"

        GitLabLocalCache(
            logger=fx_logger,
            parallel_jobs=fx_config.PARALLEL_JOBS,
            path=cache_path,
            project_id="x",
            gitlab_client=Gitlab(url="x", private_token="x"),  # noqa: S106
        )

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("expected", [True, False])
    def test_online(self, mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache, expected: bool):
        """Can check if remote repository is available."""
        if not expected:
            mocker.patch.object(
                GitLabLocalCache, "_project", new_callable=PropertyMock, side_effect=RequestsConnectionError()
            )

        assert fx_gitlab_cache._online == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_project(self, fx_gitlab_cache: GitLabLocalCache):
        """Can get the remote GitLab project object for the store."""
        result = fx_gitlab_cache._project
        assert result.id == 1234

    def test_commits_mapping(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get the generated mapping of file identifiers against Git commits."""
        result = fx_gitlab_cache_pop._commits_mapping
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_head_commit_local(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get ID of the latest commit known to the local cache."""
        result = fx_gitlab_cache_pop._head_commit_local
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_head_commit_remote(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get ID of the latest commit known to the cache."""
        result = fx_gitlab_cache_pop._head_commit_remote
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize(("fixture", "exists"), [("fx_gitlab_cache", False), ("fx_gitlab_cache_pop", True)])
    def test_exists(self, request: pytest.FixtureRequest, fixture: str, exists: bool):
        """Can determine if cache is populated or not."""
        cache = request.getfixturevalue(fixture)
        # noinspection PyTestUnpassedFixture
        assert cache._exists == exists

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("fixture", "current"),
        [("fx_gitlab_cache", False), ("fx_gitlab_cache_pop", True), ("fx_gitlab_cache_pop", False)],
    )
    def test_current(self, request: pytest.FixtureRequest, fixture: str, current: bool):
        """
        Can determine if cache is up-to-date with the remote repository.

        Current condition is controlled by VCR recordings.
        """
        cache = request.getfixturevalue(fixture)
        # noinspection PyTestUnpassedFixture
        result = cache._current
        assert result == current

    def test_load_record_pickle(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can load a pickled RecordRevision record from populated cache."""
        id_ = "a1b2c3"
        record_path = fx_gitlab_cache_pop._records_path / f"{id_}.pickle"

        record = fx_gitlab_cache_pop._load_record_pickle(record_path)
        assert record.file_identifier == id_

    def test_build_cache_create(
        self,
        fx_gitlab_cache: GitLabLocalCache,
        fx_record_config_min: dict,
    ):
        """Can populate an empty cache with record configurations and other required context."""
        commit = "x"
        head_commit = {"x": commit}
        records = [(json.dumps(fx_record_config_min, ensure_ascii=False), commit)]

        fx_gitlab_cache._build_cache(records=records, head_commit=head_commit)

        assert fx_gitlab_cache._exists
        assert len(list(fx_gitlab_cache._records_path.glob("*.pickle"))) == 1

        with fx_gitlab_cache._head_path.open() as f:
            data = json.load(f)
            assert data == head_commit

        with fx_gitlab_cache._hashes_path.open() as f:
            data = json.load(f)
            assert data == {"hashes": {"x": "0705d7272694779f2f4ee812cba66bd53e476f6d"}}

        with fx_gitlab_cache._commits_path.open() as f:
            data = json.load(f)
            assert data == {"commits": head_commit}

    def test_build_cache_update(
        self,
        fx_gitlab_cache_pop: GitLabLocalCache,
        fx_record_config_min: dict,
    ):
        """Can update an existing cache with changed record configurations and other required context."""
        file_identifier = "a1b2c3"
        commit = "y"
        head_commit = {"y": commit}
        fx_record_config_min["file_identifier"] = file_identifier
        fx_record_config_min["identification"]["edition"] = "2"
        records = [(json.dumps(fx_record_config_min, ensure_ascii=False), commit)]

        # get original record to ensure it's replaced
        original_record = fx_gitlab_cache_pop.get()[0]
        assert original_record.file_identifier == file_identifier

        # add additional entries to hashes and commit files to ensure they are not overwritten
        with fx_gitlab_cache_pop._hashes_path.open() as f:
            hashes = json.load(f)["hashes"]
        hashes["nochange"] = "nochange"
        with fx_gitlab_cache_pop._hashes_path.open(mode="w") as f:
            json.dump({"hashes": hashes}, f)
        with fx_gitlab_cache_pop._commits_path.open() as f:
            commits = json.load(f)["commits"]
        commits["nochange"] = "nochange"
        with fx_gitlab_cache_pop._commits_path.open(mode="w") as f:
            json.dump({"commits": commits}, f)

        fx_gitlab_cache_pop._build_cache(records=records, head_commit=head_commit)

        assert fx_gitlab_cache_pop._exists
        assert len(list(fx_gitlab_cache_pop._records_path.glob("*.pickle"))) == 1
        updated_record = fx_gitlab_cache_pop.get()[0]
        assert updated_record.file_identifier == file_identifier
        assert updated_record.file_revision != original_record.file_revision
        assert updated_record.sha1 != original_record.sha1

        with fx_gitlab_cache_pop._head_path.open() as f:
            data = json.load(f)
        assert data == head_commit

        with fx_gitlab_cache_pop._hashes_path.open() as f:
            data = json.load(f)
        assert data["hashes"] == {"a1b2c3": "1bdcf7143d1e3f2294741b733fe679ec776a57e7", "nochange": "nochange"}

        with fx_gitlab_cache_pop._commits_path.open() as f:
            data = json.load(f)
        assert data["commits"] == {"a1b2c3": commit, "nochange": "nochange"}

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_record_commit(self, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """Can fetch latest commit for a file in the remote repository."""
        file_identifier = "a1b2c3"
        commit = "abc123"
        path = "records/a1/b2/a1b2c3.json"
        fx_record_config_min["file_identifier"] = file_identifier
        expected = (json.dumps(fx_record_config_min, ensure_ascii=False), commit)
        results = _fetch_record_commit(project=fx_gitlab_cache._project, path=path, ref=fx_gitlab_cache._ref)
        assert results == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_record_commits(self, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """Can fetch latest commit for a set of files in the remote repository."""
        file_identifier = "a1b2c3"
        commit = "abc123"
        fx_record_config_min["file_identifier"] = file_identifier
        expected = [(json.dumps(fx_record_config_min, ensure_ascii=False), commit)]
        fx_gitlab_cache._parallel_jobs = 1  # disable parallelism to handle HTTP recording

        results = fx_gitlab_cache._fetch_record_commits()
        assert results == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("mode", [None, "renamed", "deleted"])
    def test_fetch_latest_records(
        self, mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict, mode: str | None
    ):
        """Can fetch record configurations for future commits from remote repository."""
        file_identifier = "a1b2c3"
        local_head = "abc123"
        remote_head = "def456"
        mocker.patch.object(
            type(fx_gitlab_cache), "_head_commit_local", new_callable=PropertyMock, return_value=local_head
        )
        mocker.patch.object(
            type(fx_gitlab_cache), "_head_commit_remote", new_callable=PropertyMock, return_value=remote_head
        )
        fx_record_config_min["file_identifier"] = file_identifier
        fx_record_config_min["identification"]["edition"] = "2"
        expected = [(json.dumps(fx_record_config_min, ensure_ascii=False), remote_head)]
        fx_gitlab_cache._parallel_jobs = 1  # disable parallelism to handle HTTP recording

        if mode is not None:
            with pytest.raises(CacheIntegrityError):
                _ = fx_gitlab_cache._fetch_latest_records()
            return

        results = fx_gitlab_cache._fetch_latest_records()

        assert results[0][1] == expected[0][1]
        assert results == expected

    def test_create(self, mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """
        Can fetch and populate cache with records from remote repository.

        This mocks fetching data as `_create()` is a high-level method and fetch methods are tested elsewhere.
        """
        commit = "abc123"

        records = [(json.dumps(fx_record_config_min, ensure_ascii=False), commit)]
        mocker.patch.object(fx_gitlab_cache, "_fetch_record_commits", return_value=records)

        head_commit = {"id": commit}
        mock_project = MagicMock()
        mock_project.commits.get.return_value.attributes = head_commit
        mocker.patch.object(type(fx_gitlab_cache), "_project", new_callable=PropertyMock, return_value=mock_project)

        fx_gitlab_cache._create()

        assert fx_gitlab_cache._exists

    def test_refresh(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict):
        """
        Can fetch and populate existing cache with changed records from remote repository.

        This mocks fetching data as `_refresh()` is a high-level method and fetch methods are tested elsewhere.
        """
        commit = "def456"

        records = [(json.dumps(fx_record_config_min, ensure_ascii=False), commit)]
        mocker.patch.object(fx_gitlab_cache_pop, "_fetch_latest_records", return_value=records)
        original_head = fx_gitlab_cache_pop._head_commit_local

        head_commit = {"id": commit}
        mock_project = MagicMock()
        mock_project.commits.get.return_value.attributes = head_commit
        mocker.patch.object(type(fx_gitlab_cache_pop), "_project", new_callable=PropertyMock, return_value=mock_project)

        fx_gitlab_cache_pop._refresh()

        assert fx_gitlab_cache_pop._exists
        assert fx_gitlab_cache_pop._head_commit_local != original_head

    def test_refresh_integrity(
        self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict
    ):
        """
        Cannot refresh repository if update triggers integrity issues (renamed/removed files in remote).

        This mocks fetching data as `_refresh()` is a high-level method and fetch methods are tested elsewhere.
        """
        mocker.patch.object(fx_gitlab_cache_pop, "_fetch_latest_records", side_effect=CacheIntegrityError())
        mocker.patch.object(fx_gitlab_cache_pop, "_create", return_value=None)

        fx_gitlab_cache_pop._refresh()

        # Verify _create was called due to the integrity error
        fx_gitlab_cache_pop._create.assert_called_once()

    @pytest.mark.parametrize(
        ("online", "cached", "current"),
        [
            (False, False, False),  # remote unavailable, no local cache (abort)
            (True, False, False),  # remote available, no local cache (create)
            (False, True, False),  # remote unavailable, local cache (warn stale)
            (True, True, False),  # remote available, local cache outdated (refresh)
            (True, True, True),  # remote available, local cache current (skip)
        ],
    )
    def test_ensure_exists(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_gitlab_cache_pop: GitLabLocalCache,
        online: bool,
        cached: bool,
        current: bool,
    ):
        """Can make sure an up-to-date local cache of the remote repository exists."""
        mocker.patch.object(type(fx_gitlab_cache_pop), "_online", new_callable=PropertyMock, return_value=online)
        mocker.patch.object(type(fx_gitlab_cache_pop), "_current", new_callable=PropertyMock, return_value=current)
        # `fx_gitlab_cache_pop` mocks `_create()` to copy reference cache so safe to call directly
        mocker.patch.object(type(fx_gitlab_cache_pop), "_refresh", return_value=None)
        if not cached:
            fx_gitlab_cache_pop.purge()
            assert not fx_gitlab_cache_pop._path.exists()

        if not online and not cached:
            with pytest.raises(RemoteStoreUnavailableError):
                fx_gitlab_cache_pop._ensure_exists()
            return

        fx_gitlab_cache_pop._ensure_exists()

        if online and not cached:
            assert "Local cache unavailable, creating from GitLab." in caplog.text

        if not online:
            assert "Cannot check if records cache is current, loading possibly stale records." in caplog.text

        if online and cached and not current:
            assert "Cached records are not up to date, updating from GitLab." in caplog.text

        if online and current:
            assert "Records cache exists and is current, no changes needed." in caplog.text

        assert fx_gitlab_cache_pop._exists

    def test_get(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get records from cache."""
        expected_file_identifier = "a1b2c3"
        expected_file_revision = "abc123"
        results = fx_gitlab_cache_pop.get()
        assert results[0].file_identifier == expected_file_identifier
        assert results[0].file_revision == expected_file_revision

    def test_get_hashes(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get SHA1 hashes of specified records."""
        id_ = "a1b2c3"
        expected = {id_: "740bd24fb6c1add4d71ed3bab3abd5848c22e135"}

        results = fx_gitlab_cache_pop.get_hashes([id_])
        assert results == expected

    def test_purge(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can clear cache contents."""
        mocker.patch.object(fx_gitlab_cache_pop, "_ensure_exists", return_value=None)

        assert fx_gitlab_cache_pop._exists

        fx_gitlab_cache_pop.purge()

        assert not fx_gitlab_cache_pop._exists
        assert not fx_gitlab_cache_pop._records_path.exists()


class TestGitLabStore:
    """
    Test GitLab store.

    Note: Summary and record methods are tested in base store tests and not repeated here.
    """

    def test_init(self, fx_logger: logging.Logger, fx_config: Config):
        """Can initialise store."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"

        GitLabStore(
            logger=fx_logger,
            parallel_jobs=fx_config.PARALLEL_JOBS,
            endpoint="https://gitlab.example.com",
            access_token="x",  # noqa: S106
            project_id="x",
            cache_path=cache_path,
        )

    def test_len(self, fx_gitlab_store_pop: GitLabStore):
        """Can get number of records loaded into store."""
        assert len(fx_gitlab_store_pop) == 1

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_project(self, fx_gitlab_store: GitLabStore):
        """Can get the remote GitLab project object for the store."""
        result = fx_gitlab_store._project
        assert result.id == 1234

    def test_get_remote_hashed_path(self, fx_gitlab_store: GitLabStore):
        """Can get the path to a record within the remote repository."""
        value = "123456.ext"
        expected = f"records/12/34/{value}"

        assert fx_gitlab_store._get_remote_hashed_path(value) == expected

    @pytest.mark.block_network
    @pytest.mark.vcr
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
        fx_revision_model_min: RecordRevision,
        mode: str,
        expected: dict[str, int],
    ):
        """Can create, update or delete one or more records in the remote repository."""
        records = []

        if mode == "add":
            fx_revision_model_min.file_identifier = "d4e5f6"
            records.append(fx_revision_model_min)
        if mode == "update":
            mocker.patch.object(
                type(fx_gitlab_store_cached._cache), "_current", new_callable=PropertyMock, return_value=True
            )
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

    def test_commit_no_changes(
        self, mocker: MockerFixture, caplog: pytest.LogCaptureFixture, fx_gitlab_store_cached: GitLabStore
    ):
        """Does not commit records that haven't changed."""
        mocker.patch.object(
            type(fx_gitlab_store_cached._cache), "_current", new_callable=PropertyMock, return_value=True
        )
        fx_gitlab_store_cached.populate()
        record = fx_gitlab_store_cached.get("a1b2c3")
        # override cached hashes to ensure hashes will match
        with fx_gitlab_store_cached._cache._hashes_path.open("w") as f:
            json.dump({"hashes": {record.file_identifier: record.sha1}}, f)

        fx_gitlab_store_cached._commit(records=[record], title="x", message="x", author=("x", "x@example.com"))

        assert "No actions to perform, skipping" in caplog.text

    def test_populate(self, fx_gitlab_store_cached: GitLabStore):
        """
        Can populate the store with records from the remote repository, via a local cache.

        High level public method.
        """
        assert len(fx_gitlab_store_cached.records) == 0
        fx_gitlab_store_cached.populate()
        assert len(fx_gitlab_store_cached.records) > 0

    @pytest.mark.parametrize("exists", [True, False])
    def test_get(self, fx_gitlab_store_pop: GitLabStore, exists: bool):
        """Can get a record if loaded into the local subset via `populate()`."""
        value = "a1b2c3" if exists else "invalid"

        if not exists:
            with pytest.raises(RecordNotFoundError):
                fx_gitlab_store_pop.get(value)
            return

        result = fx_gitlab_store_pop.get(value)
        assert isinstance(result, RecordRevision)
        assert result.file_identifier == value

    @pytest.mark.vcr
    @pytest.mark.block_network
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
        fx_record_model_min: Record,
        mode: str,
        stats: dict[str, int],
    ):
        """
        Can create, update or delete Records in the remote repository.

        High level public method.

        No-op case for submitted records that don't trigger any changes to remote repo.
        """
        records = [] if mode == "none" else [fx_record_model_min]
        mocker.patch.object(fx_gitlab_store_cached, "_commit", return_value=stats)
        mocker.patch.object(
            type(fx_gitlab_store_cached._cache), "_current", new_callable=PropertyMock, return_value=True
        )
        # ignore repopulating cache after push as we fake commit so cache won't be able to load new records
        mocker.patch.object(fx_gitlab_store_cached, "populate", return_value=None)

        fx_gitlab_store_cached.push(records=records, title="title", message="x", author=("x", "x@example.com"))

        if mode == "none":
            assert "No records to push, skipping" in caplog.text
        elif mode == "noop":
            assert "No records pushed, skipping cache invalidation" in caplog.text
        else:
            assert "Recreating cache to reflect pushed changes" in caplog.text

    @pytest.mark.parametrize("exists", [True, False])
    def test_purge(self, fx_gitlab_store_pop: GitLabStore, exists: bool):
        """Can purge loaded records."""
        if not exists:
            fx_gitlab_store_pop._records = {}

        fx_gitlab_store_pop.purge()

        assert len(fx_gitlab_store_pop.records) == 0
