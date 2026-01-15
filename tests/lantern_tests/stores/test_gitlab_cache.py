import json
import logging
import pickle
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, PropertyMock

import pytest
from gitlab import Gitlab
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.config import Config
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, StoreFrozenError
from lantern.stores.gitlab import CommitResults, GitLabSource, GitLabStore
from lantern.stores.gitlab_cache import (
    CachedProcessedRecord,
    CacheFrozenError,
    CacheIntegrityError,
    CacheNotInitialisedError,
    CacheTooOutdatedError,
    GitLabCachedStore,
    GitLabLocalCache,
    RawRecord,
    RemoteStoreUnavailableError,
    _fetch_record_commit,
)


@pytest.mark.cov()
class TestCachedProcessedRecord:
    """Test GitLab cached processed record helper class."""

    def test_init(self, fx_logger: logging.Logger, fx_record_config_min: dict):
        """Can initialise processed record."""
        config_str = json.dumps(fx_record_config_min)
        commit_id = "x"
        config_expected = {**fx_record_config_min, "file_revision": commit_id}

        result = CachedProcessedRecord(logger=fx_logger, config_str=config_str, commit_id="x")
        assert isinstance(result.pickled, bytes)
        # assert record.pickled is valid
        unpickled = pickle.loads(result.pickled)  # noqa: S301
        assert unpickled == result.record
        assert result.record.file_identifier == fx_record_config_min["file_identifier"]
        assert result.record.file_revision == config_expected["file_revision"]


class TestGitLabLocalCache:
    """Test GitLab local cache."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config):
        """Can initialise cache."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"
        source = GitLabSource(
            endpoint=fx_config.STORE_GITLAB_ENDPOINT,
            project=fx_config.STORE_GITLAB_PROJECT_ID,
            ref=fx_config.STORE_GITLAB_BRANCH,
        )

        cache = GitLabLocalCache(
            logger=fx_logger,
            parallel_jobs=fx_config.PARALLEL_JOBS,
            path=cache_path,
            gitlab_token="x",  # noqa: S106
            gitlab_client=Gitlab(url="x", private_token="x"),  # noqa: S106
            gitlab_source=source,
        )
        assert len(cache._flash) == 0

    def test_pickle(self, fx_gitlab_cache_frozen: GitLabLocalCache):
        """Can pickle and unpickle cache."""
        expected = len(fx_gitlab_cache_frozen.get())
        assert expected > 0
        pickled = pickle.dumps(fx_gitlab_cache_frozen, pickle.HIGHEST_PROTOCOL)
        unpickled: GitLabLocalCache = pickle.loads(pickled)  # noqa: S301
        assert isinstance(unpickled, GitLabLocalCache)
        results = unpickled.get()
        assert len(results) == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("expected", [True, False])
    def test_online(self, mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache, expected: bool):
        """Can check if the remote source is available."""
        if not expected:
            mocker.patch.object(
                GitLabLocalCache, "_project", new_callable=PropertyMock, side_effect=RequestsConnectionError()
            )

        assert fx_gitlab_cache._online == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_project(self, fx_gitlab_cache: GitLabLocalCache):
        """Can get the current remote GitLab project."""
        result = fx_gitlab_cache._project
        assert result.id == 1234

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_head_commit(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get the latest commit ID from the current source."""
        result = fx_gitlab_cache_pop._head_commit
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.block_network
    def test_head_commit_frozen(self, fx_gitlab_cache_frozen: GitLabLocalCache):
        """Cannot get head commit from when cache is frozen."""
        with pytest.raises(CacheFrozenError):
            _ = fx_gitlab_cache_frozen._head_commit

    @pytest.mark.parametrize("cached", [True, False])
    def test_cached_head_commit(self, fx_gitlab_cache_pop: GitLabLocalCache, cached: bool):
        """Can get the latest commit ID known to the cache."""
        if cached is None:
            fx_gitlab_cache_pop.purge()
            with pytest.raises(CacheNotInitialisedError):
                _ = fx_gitlab_cache_pop.cached_head_commit
            return

        result = fx_gitlab_cache_pop.cached_head_commit
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_source(self, fx_config: Config, fx_gitlab_cache: GitLabLocalCache):
        """Can get current remote source."""
        expected = fx_gitlab_cache._source
        assert fx_gitlab_cache._source == expected

    @pytest.mark.parametrize("cached", [True, False])
    def test_cached_source(self, fx_config: Config, fx_gitlab_cache_pop: GitLabLocalCache, cached: bool):
        """Can get source known to cache."""
        expected = fx_gitlab_cache_pop._source
        if not cached:
            fx_gitlab_cache_pop.purge()
            with pytest.raises(CacheNotInitialisedError):
                _ = fx_gitlab_cache_pop._cached_source
            return
        assert fx_gitlab_cache_pop._cached_source == expected

    @pytest.mark.parametrize(("exists", "init"), [(False, False), (True, False), (True, True)])
    def test_exists(self, fx_gitlab_cache_pop: GitLabLocalCache, exists: bool, init: bool):
        """Can determine if cache exists and is initialised."""
        expected = bool(exists and init)
        if not exists:
            fx_gitlab_cache_pop.purge()
        if exists and not init:
            with fx_gitlab_cache_pop._engine as tx:
                tx.execute("""DROP TABLE IF EXISTS record;""")

        assert fx_gitlab_cache_pop.exists == expected

    @pytest.mark.parametrize(
        ("cached", "current", "expected"), [(None, "y", False), ("x", "y", False), ("x", "x", True)]
    )
    def test_applicable(
        self,
        mocker: MockerFixture,
        fx_gitlab_cache_pop: GitLabLocalCache,
        cached: str | None,
        current: str,
        expected: bool,
    ):
        """Can determine whether cache applicable based on current and cached sources."""
        if cached is None:
            fx_gitlab_cache_pop.purge()
        mocker.patch.object(type(fx_gitlab_cache_pop), "_source", new_callable=PropertyMock, return_value=current)
        mocker.patch.object(type(fx_gitlab_cache_pop), "_cached_source", new_callable=PropertyMock, return_value=cached)

        assert fx_gitlab_cache_pop._applicable == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(("cached", "current"), [(False, False), (True, False), (True, True)])
    def test_current(self, fx_gitlab_cache_pop: GitLabLocalCache, cached: bool, current: bool):
        """
        Can determine if cache is up-to-date with the remote repository.

        Current condition is controlled by VCR recordings.
        """
        if not cached:
            fx_gitlab_cache_pop.purge()
        assert fx_gitlab_cache_pop._current == current

    def test_current_frozen(self, fx_gitlab_cache_frozen: GitLabLocalCache):
        """Can determine a frozen cache is always considered current."""
        assert fx_gitlab_cache_frozen._current

    def test_ensure_db(self, fx_gitlab_cache: GitLabLocalCache):
        """Can create and initialise cache backing database."""
        fx_gitlab_cache._ensure_db()
        assert fx_gitlab_cache.exists is True

    def test_build_cache_create(
        self,
        fx_config: Config,
        fx_gitlab_cache: GitLabLocalCache,
        fx_record_config_min: dict,
    ):
        """Can populate an empty cache with records and internal meta key-value information."""
        commit = "x"
        source = fx_gitlab_cache._source
        record = RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)
        record_config_ = {**fx_record_config_min, "file_revision": commit}
        record_ = RecordRevision.loads(record_config_)

        fx_gitlab_cache._build_cache(records=[record], head_commit_id=commit)

        assert fx_gitlab_cache.exists
        with fx_gitlab_cache._engine as tx:
            result = tx.fetchscalar("SELECT COUNT(*) FROM record;")
            assert result == 1

            cached_record = tx.fetchone(
                "SELECT file_identifier, file_revision, sha1, json(record_jsonb) as record_jsonb, record_pickled FROM record LIMIT 1;"
            )
            assert cached_record["file_identifier"] == record_.file_identifier
            assert cached_record["file_revision"] == record_.file_revision
            assert cached_record["sha1"] == record_.sha1
            assert json.loads(cached_record["record_jsonb"]) == record_config_
            assert pickle.loads(cached_record["record_pickled"]) == record_  # noqa: S301

            meta = tx.fetchscalars(
                "SELECT value FROM meta WHERE key in ('source_endpoint', 'source_project', 'source_ref') ORDER BY key;"
            )
            cached_source = GitLabSource(endpoint=meta[0], project=meta[1], ref=meta[2])
            assert cached_source == source

    def test_build_cache_update(
        self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_gitlab_cache_pop: GitLabLocalCache,
        fx_record_config_min: dict,
    ):
        """Can update an existing cache with changed records and internal meta key-value information."""
        mocker.patch.object(fx_gitlab_cache_pop, "_ensure_exists", return_value=None)

        file_identifier = "a1b2c3"
        commit = "y"

        # updated record
        fx_record_config_min["file_identifier"] = file_identifier
        fx_record_config_min["identification"]["edition"] = "2"
        raw_record = RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)
        record_config_ = {**fx_record_config_min, "file_revision": commit}
        record_ = RecordRevision.loads(record_config_)

        # original record (to ensure it's replaced)
        original_record = fx_gitlab_cache_pop.get()[0]
        assert original_record.file_identifier == file_identifier

        fx_gitlab_cache_pop._build_cache(records=[raw_record], head_commit_id=commit)

        assert fx_gitlab_cache_pop.exists
        with fx_gitlab_cache_pop._engine as tx:
            result = tx.fetchscalar("SELECT COUNT(*) FROM record;")
            assert result == 1

            cached_record = tx.fetchone(
                "SELECT file_identifier, file_revision, sha1, json(record_jsonb) as record_jsonb, record_pickled FROM record LIMIT 1;"
            )
            assert cached_record["file_identifier"] == record_.file_identifier
            assert cached_record["file_revision"] == record_.file_revision
            assert cached_record["sha1"] == record_.sha1

            updated_record = pickle.loads(cached_record["record_pickled"])  # noqa: S301
            assert updated_record.file_identifier == file_identifier
            assert updated_record.file_revision != original_record.file_revision
            assert updated_record.sha1 != original_record.sha1

            meta = tx.fetchscalar("SELECT COUNT(*) FROM meta;")
            assert meta == 4
            cached_head = tx.fetchscalar("SELECT value FROM meta WHERE key = 'head_commit';")
            assert cached_head == commit

    @pytest.mark.cov()
    def test_create_refresh(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache):
        """
        Can correctly construct current source and get head commit from project.

        `_create_refresh()` does not return anything itself, so we check the arguments passed to `_build_cache()` and
        the 'flash' cache is reset.
        """
        mocker.patch.object(fx_gitlab_cache_pop, "_build_cache", return_value=None)
        # mock:
        # - fx_gitlab_cache_pop._project.commits.get to return an object with an 'attributes' dict property
        # - fx_gitlab_cache_pop._project.http_url_to_repo to return a URL
        mock_project = MagicMock()
        mock_commit = MagicMock()
        mock_commit.attributes = {"id": "x"}
        mock_project.commits.get.return_value = mock_commit
        mock_project.http_url_to_repo = "https://gitlab.example.com/x.git"
        mocker.patch.object(type(fx_gitlab_cache_pop), "_project", new_callable=PropertyMock, return_value=mock_project)
        # noinspection PyTypeChecker
        fx_gitlab_cache_pop._flash["x"] = "x"  # to verify flash is later cleared

        fx_gitlab_cache_pop._create_refresh(records=[])

        # noinspection PyUnresolvedReferences
        fx_gitlab_cache_pop._build_cache.assert_called_once()  # assert _build_cache called with ref in head commit
        # noinspection PyUnresolvedReferences
        args, kwargs = fx_gitlab_cache_pop._build_cache.call_args

        head_commit = kwargs.get("head_commit_id", args[1] if len(args) > 1 else None)
        assert head_commit == "x"

        assert len(fx_gitlab_cache_pop._flash) == 0

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_record_commit(self, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """Can fetch latest commit for a file in the remote repository."""
        file_identifier = "a1b2c3"
        commit = "abc123"
        path = "records/a1/b2/a1b2c3.json"
        fx_record_config_min["file_identifier"] = file_identifier
        expected = RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)

        results = _fetch_record_commit(project=fx_gitlab_cache._project, path=path, ref=fx_gitlab_cache._source.ref)
        assert isinstance(results, RawRecord)
        assert results == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_record_commits(self, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """Can fetch latest commit for a set of files in the remote repository."""
        file_identifier = "a1b2c3"
        commit = "abc123"
        fx_record_config_min["file_identifier"] = file_identifier
        expected = [RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)]
        fx_gitlab_cache._parallel_jobs = 1  # disable parallelism to handle HTTP recording

        results = fx_gitlab_cache._fetch_record_commits()
        assert all(isinstance(item, RawRecord) for item in results)
        assert results == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("mode", [None, "renamed", "deleted"])
    def test_fetch_latest_records(
        self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict, mode: str | None
    ):
        """Can fetch record configurations for future commits from remote repository."""
        file_identifier = "a1b2c3"
        local_head = "abc123"
        remote_head = "def456"
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "cached_head_commit", new_callable=PropertyMock, return_value=local_head
        )
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "_head_commit", new_callable=PropertyMock, return_value=remote_head
        )
        fx_record_config_min["file_identifier"] = file_identifier
        fx_record_config_min["identification"]["edition"] = "2"
        expected = [RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=remote_head)]
        fx_gitlab_cache_pop._parallel_jobs = 1  # disable parallelism to handle HTTP recording

        if mode is not None:
            with pytest.raises(CacheIntegrityError):
                _ = fx_gitlab_cache_pop._fetch_latest_records()
            return

        results = fx_gitlab_cache_pop._fetch_latest_records()

        assert results[0].commit_id == expected[0].commit_id  # record with 2nd edition
        assert results == expected

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_latest_records_dedupe(
        self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict
    ):
        """
        Can fetch deduplicated record configurations for future commits from remote repository.

        I.e. where a record is updated multiple times in a set of pending commits, only fetch the latest.
        """
        file_identifier = "a1b2c3"
        local_head = "abc123"
        remote_head = "ghi789"
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "cached_head_commit", new_callable=PropertyMock, return_value=local_head
        )
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "_head_commit", new_callable=PropertyMock, return_value=remote_head
        )
        fx_record_config_min["file_identifier"] = file_identifier
        fx_record_config_min["identification"]["edition"] = "3"
        expected = [RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=remote_head)]
        fx_gitlab_cache_pop._parallel_jobs = 1  # disable parallelism to handle HTTP recording

        results = fx_gitlab_cache_pop._fetch_latest_records()
        assert len(results) == 1  # not 2
        assert results[0].commit_id == expected[0].commit_id  # record with 3rd edition (2nd skipped)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_latest_records_excessive(
        self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict
    ):
        """Can fetch record configurations for future commits from remote repository."""
        local_head = "abc123"
        remote_head = "def456"
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "cached_head_commit", new_callable=PropertyMock, return_value=local_head
        )
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "_head_commit", new_callable=PropertyMock, return_value=remote_head
        )
        fx_gitlab_cache_pop._parallel_jobs = 1  # disable parallelism to handle HTTP recording

        with pytest.raises(CacheTooOutdatedError):
            _ = fx_gitlab_cache_pop._fetch_latest_records()

    def test_create(self, mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """
        Can fetch and populate cache with records from remote repository.

        This mocks fetching data as `_create()` is a high-level method and fetch methods are tested elsewhere.
        """
        commit = "abc123"

        records = [RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)]
        mocker.patch.object(fx_gitlab_cache, "_fetch_record_commits", return_value=records)

        head_commit = {"id": commit}
        mock_project = MagicMock()
        mock_project.commits.get.return_value.attributes = head_commit
        mock_project.http_url_to_repo = "https://gitlab.example.com/x.git"
        mocker.patch.object(type(fx_gitlab_cache), "_project", new_callable=PropertyMock, return_value=mock_project)

        fx_gitlab_cache._create()

        assert fx_gitlab_cache.exists

    def test_refresh(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict):
        """
        Can fetch and populate existing cache with changed records from remote repository.

        This mocks fetching data as `_refresh()` is a high-level method and fetch methods are tested elsewhere.
        """
        commit = "def456"
        records = [RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)]
        mocker.patch.object(fx_gitlab_cache_pop, "_fetch_latest_records", return_value=records)
        original_head = fx_gitlab_cache_pop.cached_head_commit

        head_commit = {"id": commit}
        mock_project = MagicMock()
        mock_project.commits.get.return_value.attributes = head_commit
        mock_project.http_url_to_repo = "https://gitlab.example.com/x.git"
        mocker.patch.object(type(fx_gitlab_cache_pop), "_project", new_callable=PropertyMock, return_value=mock_project)

        fx_gitlab_cache_pop._refresh()

        assert fx_gitlab_cache_pop.exists
        assert fx_gitlab_cache_pop.cached_head_commit != original_head

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

        # noinspection PyUnresolvedReferences
        fx_gitlab_cache_pop._create.assert_called_once()  # Verify _create was called due to the integrity error

    def test_refresh_outdated(
        self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache, fx_record_config_min: dict
    ):
        """
        Does not refresh repository if there are to many outstanding commits for that to make sense.

        This mocks fetching data as `_refresh()` is a high-level method and fetch methods are tested elsewhere.
        """
        mocker.patch.object(fx_gitlab_cache_pop, "_fetch_latest_records", side_effect=CacheTooOutdatedError())
        mocker.patch.object(fx_gitlab_cache_pop, "_create", return_value=None)

        fx_gitlab_cache_pop._refresh()

        # noinspection PyUnresolvedReferences
        fx_gitlab_cache_pop._create.assert_called_once()  # Verify _create was called due to the outdated error

    @pytest.mark.parametrize(
        ("online", "cached", "current", "applicable"),
        [
            (False, False, False, False),  # (1, void)
            (True, False, False, False),  # (2, create)
            (False, True, False, False),  # (3, irrelevant)
            (False, True, False, True),  # (4, stale)
            (True, True, True, False),  # (5, recreate)
            (True, True, False, True),  # (6, update)
            (True, True, True, True),  # (7, noop)
        ],
        ids=["void", "create", "irrelevant", "stale", "recreate", "update", "noop"],
        # (1, void      )  remote unavailable,  no local cache         ,  current/applicable irrelevant  (abort)
        # (2, create    )  remote available  ,  no local cache         ,  current/applicable irrelevant  (create)
        # (3, irrelevant)  remote unavailable,     local cache         ,  not applicable                 (abort)
        # (4, stale     )  remote unavailable,     local cache         ,  applicable                     (warn stale)
        # (5, recreate  )  remote available  ,     local cache         ,  not applicable                 (recreate)
        # (6, update    )  remote available  ,     local cache outdated,  applicable                     (refresh)
        # (7, noop      )  remote available  ,     local cache current ,  applicable                     (no-op)
    )
    def test_ensure_exists(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_config: Config,
        fx_gitlab_cache_pop: GitLabLocalCache,
        online: bool,
        cached: bool,
        current: bool,
        applicable: bool,
    ):
        """Can make sure an up-to-date local cache of the remote repository with applicable branch exists."""
        mocker.patch.object(type(fx_gitlab_cache_pop), "_online", new_callable=PropertyMock, return_value=online)
        mocker.patch.object(type(fx_gitlab_cache_pop), "_current", new_callable=PropertyMock, return_value=current)
        # `fx_gitlab_cache_pop` mocks `_create()` to copy reference cache so safe to call directly
        mocker.patch.object(fx_gitlab_cache_pop, "_refresh", return_value=None)

        # set `_cached_source` to control applicability
        applicable_value = fx_gitlab_cache_pop._source
        inapplicable_value = GitLabSource(endpoint="invalid", project="invalid", ref="invalid")
        cached_source = applicable_value if applicable else inapplicable_value
        mocker.patch.object(
            type(fx_gitlab_cache_pop), "_cached_source", new_callable=PropertyMock, return_value=cached_source
        )

        # mock fx_gitlab_cache_pop._project.get to return a Project mock with an 'http_url_to_repo' property
        mock_project = MagicMock()
        mock_project.http_url_to_repo = "https://gitlab.example.com/x.git"
        mocker.patch.object(type(fx_gitlab_cache_pop), "_project", new_callable=PropertyMock, return_value=mock_project)

        if not cached:
            fx_gitlab_cache_pop.purge()
            assert not fx_gitlab_cache_pop._path.exists()

        if not online and not cached:
            # (1, void) remote unavailable, no local cache
            with pytest.raises(RemoteStoreUnavailableError):
                fx_gitlab_cache_pop._ensure_exists()
            return

        if not online and not applicable:
            # (3, irrelevant) remote unavailable, local cache, not applicable
            with pytest.raises(RemoteStoreUnavailableError):
                fx_gitlab_cache_pop._ensure_exists()
            return

        fx_gitlab_cache_pop._ensure_exists()

        if online and not cached:
            # (2, create) remote available, no local cache
            assert "Local cache not ready, creating from GitLab" in caplog.text

        if not online:
            # (4, stale) remote unavailable, local cache, applicable
            assert "Cannot check if records cache is current, loading possibly stale records" in caplog.text

        if online and cached and not applicable:
            # (5, recreate) remote available, local cache, not applicable
            assert (
                f"Cached source '{fx_gitlab_cache_pop._cached_source}' does not match current instance and branch '{fx_gitlab_cache_pop._source}', recreating cache"
                in caplog.text
            )
            return

        if online and cached and not current:
            # (6, update) remote available, local cache outdated, applicable
            assert "Cached records are not up to date, updating from GitLab" in caplog.text

        if online and current:
            # (7, noop) remote available, local cache current, applicable
            assert "Records cache exists and is current, no changes needed" in caplog.text

        assert fx_gitlab_cache_pop.exists

    @pytest.mark.parametrize(
        ("exists", "initialised", "applicable", "msg", "log"),
        [
            (False, False, True, r"Local cache unavailable and is frozen. Cannot load records.", None),
            (
                True,
                True,
                False,
                r"Cached source '.*' does not match current instance and branch '.*' but is frozen. Will not load records.",
                None,
            ),
            (True, False, True, r"Local cache not setup and is frozen. Cannot load records.", None),
            (True, True, True, None, "Cache exists and is frozen"),
        ],
        ids=["empty", "inapplicable", "incomplete", "noop"],
    )
    def test_ensure_exists_frozen(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_config: Config,
        fx_gitlab_cache_frozen: GitLabLocalCache,
        exists: bool,
        initialised: bool,
        applicable: bool,
        msg: str | None,
        log: str | None,
    ):
        """Cannot use a mis-configured frozen cache."""
        mocker.patch.object(type(fx_gitlab_cache_frozen), "_online", new_callable=PropertyMock, return_value=True)
        mocker.patch.object(type(fx_gitlab_cache_frozen), "_source", new_callable=PropertyMock, return_value=None)
        mocker.patch.object(
            type(fx_gitlab_cache_frozen), "_applicable", new_callable=PropertyMock, return_value=applicable
        )
        if not initialised:
            mocker.patch.object(
                type(fx_gitlab_cache_frozen),
                "_applicable",
                new_callable=PropertyMock,
                side_effect=CacheNotInitialisedError(),
            )
        if not exists:
            fx_gitlab_cache_frozen.purge()

        if msg is not None:
            expected = re.compile(msg)
            with pytest.raises(CacheFrozenError) as excinfo:
                fx_gitlab_cache_frozen._ensure_exists()
            assert expected.fullmatch(str(excinfo.value))
            return

        if log is not None:
            fx_gitlab_cache_frozen._ensure_exists()
            assert log in caplog.text

    @pytest.mark.cov()
    def test_ensure_exists_cached_no_source(
        self, caplog: pytest.LogCaptureFixture, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache
    ):
        """Recreates cache if cached source is missing."""
        mocker.patch.object(type(fx_gitlab_cache_pop), "_online", new_callable=PropertyMock, return_value=True)
        mocker.patch.object(type(fx_gitlab_cache_pop), "exists", new_callable=PropertyMock, return_value=True)
        with fx_gitlab_cache_pop._engine as tx:
            tx.execute("DELETE FROM meta WHERE key LIKE 'source_%';")
        # `fx_gitlab_cache_pop` mocks `_create()` to copy reference cache so safe to call directly

        fx_gitlab_cache_pop._ensure_exists()
        assert fx_gitlab_cache_pop.exists
        assert "Local cache not setup, recreating from GitLab" in caplog.text

    @pytest.mark.parametrize("selected", [None, {}, {"x"}, {"x", "y"}, {"invalid"}, {"x", "invalid"}])
    def test_get(
        self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_gitlab_cache: GitLabLocalCache,
        fx_record_config_min: dict,
        selected: set[str] | None,
    ):
        """Can get selected or all records from cache."""
        commit = "x"
        records = [
            RawRecord(
                config_str=json.dumps({**fx_record_config_min, "file_identifier": "x"}, ensure_ascii=False),
                commit_id=commit,
            ),
            RawRecord(
                config_str=json.dumps({**fx_record_config_min, "file_identifier": "y"}, ensure_ascii=False),
                commit_id=commit,
            ),
        ]
        fx_gitlab_cache._build_cache(records=records, head_commit_id=commit)
        mocker.patch.object(fx_gitlab_cache, "_ensure_exists", return_value=None)
        expected_len = len(records) if not selected else len(selected)
        if selected and "invalid" in selected:
            expected_len -= 1

        results = fx_gitlab_cache.get(file_identifiers=selected)
        assert len(results) == expected_len
        assert all(isinstance(item, RecordRevision) for item in results)
        if expected_len > 0:
            assert len(fx_gitlab_cache._flash) > 0

    def test_get_flash(
        self, mocker: MockerFixture, fx_config: Config, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict
    ):
        """Can get selected or all records from flash cache."""
        commit = "x"
        records = [
            RawRecord(
                config_str=json.dumps({**fx_record_config_min, "file_identifier": "x"}, ensure_ascii=False),
                commit_id=commit,
            ),
            RawRecord(
                config_str=json.dumps({**fx_record_config_min, "file_identifier": "y"}, ensure_ascii=False),
                commit_id=commit,
            ),
        ]
        fx_gitlab_cache._build_cache(records=records, head_commit_id=commit)
        mocker.patch.object(fx_gitlab_cache, "_ensure_exists", return_value=None)
        selected = {"x", "y"}
        expected_len = len(selected)
        _ = fx_gitlab_cache.get(file_identifiers=selected)  # preload flash

        results = fx_gitlab_cache.get(file_identifiers=selected)
        assert len(results) == expected_len

    @pytest.mark.parametrize("selected", [{"x"}, {"x", "y"}, {"invalid"}])
    def test_get_hashes(
        self,
        mocker: MockerFixture,
        fx_config: Config,
        fx_gitlab_cache: GitLabLocalCache,
        fx_record_config_min: dict,
        selected: set[str],
    ):
        """Can get SHA1 hashes of specified records."""
        commit = "x"
        records = [
            RawRecord(
                config_str=json.dumps({**fx_record_config_min, "file_identifier": "x"}, ensure_ascii=False),
                commit_id=commit,
            ),
            RawRecord(
                config_str=json.dumps({**fx_record_config_min, "file_identifier": "y"}, ensure_ascii=False),
                commit_id=commit,
            ),
        ]
        fx_gitlab_cache._build_cache(records=records, head_commit_id=commit)
        mocker.patch.object(fx_gitlab_cache, "_ensure_exists", return_value=None)

        hashes = {
            p.record.file_identifier: p.record.sha1
            for p in [
                CachedProcessedRecord(logger=None, config_str=r.config_str, commit_id=r.commit_id) for r in records
            ]
        }
        expected = {k: v for k, v in hashes.items() if k in selected}
        if selected == {"invalid"}:
            expected = {"invalid": None}

        results = fx_gitlab_cache.get_hashes(selected)
        assert results == expected

    def test_get_count(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get cached record count."""
        mocker.patch.object(fx_gitlab_cache_pop, "_ensure_exists", return_value=None)

        result = fx_gitlab_cache_pop.get_count()
        assert result == 1

    def test_purge(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can clear cache contents."""
        mocker.patch.object(fx_gitlab_cache_pop, "_ensure_exists", return_value=None)

        assert fx_gitlab_cache_pop.exists

        fx_gitlab_cache_pop.purge()

        assert not fx_gitlab_cache_pop.exists
        assert not fx_gitlab_cache_pop._cache_path.exists()


class TestGitLabCachedStore:
    """Test GitLab local cache store."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config, fx_gitlab_source: GitLabSource):
        """Can initialise store."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"

        GitLabCachedStore(
            logger=fx_logger,
            source=fx_gitlab_source,
            access_token="x",  # noqa: S106
            parallel_jobs=fx_config.PARALLEL_JOBS,
            cache_dir=cache_path,
        )

    def test_len(self, fx_gitlab_cached_store_pop: GitLabCachedStore):
        """Can get count of records in store."""
        assert len(fx_gitlab_cached_store_pop) > 0

    @pytest.mark.cov()
    @pytest.mark.parametrize("frozen", [False, True])
    def test_frozen(self, fx_gitlab_cached_store: GitLabCachedStore, frozen: bool):
        """Can get whether store is frozen."""
        fx_gitlab_cached_store._frozen = frozen
        assert fx_gitlab_cached_store.frozen is frozen

    @pytest.mark.cov()
    def test_project(self, mocker: MockerFixture, fx_gitlab_cached_store: GitLabCachedStore):
        """Can get remote GitLab project."""
        expected = "x"
        mocker.patch.object(GitLabStore, "_project", new_callable=PropertyMock, return_value=expected)
        assert fx_gitlab_cached_store._project == expected

    @pytest.mark.parametrize("cached", [False, True])
    def test_head_commit(self, fx_gitlab_cached_store_pop: GitLabCachedStore, cached: bool):
        """Can get ID of the latest commit known to the local cache."""
        if not cached:
            fx_gitlab_cached_store_pop.purge()
        expected = "abc123" if cached else None
        assert fx_gitlab_cached_store_pop.head_commit == expected

    @pytest.mark.cov()
    def test_ensure_branch(self, mocker: MockerFixture, fx_gitlab_cached_store: GitLabCachedStore):
        """Cannot create branches when store is frozen."""
        mocker.patch.object(GitLabStore, "_ensure_branch", return_value=None)
        fx_gitlab_cached_store._ensure_branch("x")

    @pytest.mark.cov()
    def test_ensure_branch_frozen(self, fx_gitlab_cached_store_frozen: GitLabCachedStore):
        """Cannot create branches when store is frozen."""
        with pytest.raises(StoreFrozenError):
            fx_gitlab_cached_store_frozen._ensure_branch("x")

    def test_select(self, fx_gitlab_cached_store_pop: GitLabCachedStore):
        """Can get any records that exist in the cache."""
        result = fx_gitlab_cached_store_pop.select()
        assert len(result) > 0
        assert all(isinstance(item, RecordRevision) for item in result)

    @pytest.mark.parametrize("all_exists", [True, False])
    def test_select_filter(self, fx_gitlab_cached_store_pop: GitLabCachedStore, all_exists: bool):
        """Can get selected records only if they _all_ exist in the cache."""
        values = {"a1b2c3"} if all_exists else {"a1b2c3", "invalid"}

        if not all_exists:
            with pytest.raises(RecordsNotFoundError):
                fx_gitlab_cached_store_pop.select(file_identifiers=values)
            return

        result = fx_gitlab_cached_store_pop.select(file_identifiers=values)
        assert len(result) == len(values)
        assert all(isinstance(item, RecordRevision) for item in result)

    @pytest.mark.parametrize("exists", [True, False])
    def test_select_one(self, fx_gitlab_cached_store_pop: GitLabCachedStore, exists: bool):
        """Can get a record if in the cache."""
        value = "a1b2c3" if exists else "invalid"

        if not exists:
            with pytest.raises(RecordNotFoundError):
                fx_gitlab_cached_store_pop.select_one(value)
            return

        result = fx_gitlab_cached_store_pop.select_one(value)
        assert isinstance(result, RecordRevision)
        assert result.file_identifier == value

    @pytest.mark.parametrize("changes", [True, False])
    def test_push_refresh(self, mocker: MockerFixture, fx_gitlab_cached_store: GitLabCachedStore, changes: bool):
        """Can refresh cache after modifying the remote repository."""
        results_change = CommitResults(
            branch="main", commit="def456", changes={"create": ["d4e5f6"], "update": []}, actions=[{"action": "create"}]
        )
        results_empty = CommitResults(branch="main", commit=None, changes={"create": [], "update": []}, actions=[])
        results = results_change if changes else results_empty
        mocker.patch.object(GitLabStore, "push", return_value=results)
        ensure_mock = mocker.patch.object(fx_gitlab_cached_store._cache, "_ensure_exists", return_value=None)

        # though records is empty here, mock ensures a result that should trigger a refresh
        fx_gitlab_cached_store.push(records=[], title="title", message="x", author=("x", "x@example.com"))
        if changes:
            ensure_mock.assert_called_once()

    def test_push_frozen(self, fx_gitlab_cached_store_frozen: GitLabCachedStore):
        """Cannot push changes when store is frozen."""
        with pytest.raises(StoreFrozenError):
            fx_gitlab_cached_store_frozen.push(records=[], title="x", message="x", author=("x", "x@example.com"))

    @pytest.mark.parametrize("exists", [True, False])
    def test_purge(self, fx_gitlab_cached_store_pop: GitLabCachedStore, exists: bool):
        """Can purge cached records."""
        if not exists:
            fx_gitlab_cached_store_pop._cache.purge()
            assert not fx_gitlab_cached_store_pop._cache.exists
        else:
            assert len(fx_gitlab_cached_store_pop.select()) > 0

        fx_gitlab_cached_store_pop.purge()
        assert not fx_gitlab_cached_store_pop._cache.exists

    def test_purge_frozen(self, fx_gitlab_cached_store_frozen: GitLabCachedStore):
        """Cannot purge store is frozen."""
        with pytest.raises(StoreFrozenError):
            fx_gitlab_cached_store_frozen.purge()
