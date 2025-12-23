import json
import logging
import pickle
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, PropertyMock
from urllib.parse import urlparse

import pytest
from gitlab import Gitlab
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.config import Config
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import (
    CacheIntegrityError,
    CacheNotInitialisedError,
    CacheTooOutdatedError,
    CommitResults,
    GitLabLocalCache,
    GitLabStore,
    ProcessedRecord,
    RawRecord,
    RemoteStoreUnavailableError,
    Source,
    _fetch_record_commit,
)


class TestProcessedRecord:
    """Test GitLab local cache processed record helper class."""

    def test_init(self, fx_logger: logging.Logger, fx_record_config_min: dict):
        """Can initialise processed record."""
        config_str = json.dumps(fx_record_config_min)
        commit_id = "x"
        config_expected = {**fx_record_config_min, "file_revision": commit_id}

        result = ProcessedRecord(logger=fx_logger, config_str=config_str, commit_id="x")
        assert result.config == config_expected
        assert isinstance(result.record, RecordRevision)
        assert result.record.file_revision == commit_id
        assert isinstance(result.pickled, bytes)
        # assert record.pickled is a valid pickle
        unpickled = pickle.loads(result.pickled)  # noqa: S301
        assert unpickled == result.record


class TestGitLabLocalCache:
    """Test GitLab local cache."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config):
        """Can initialise cache."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"

        GitLabLocalCache(
            logger=fx_logger,
            parallel_jobs=fx_config.PARALLEL_JOBS,
            path=cache_path,
            project_id="x",
            ref="x",
            gitlab_token="x",  # noqa: S106
            gitlab_client=Gitlab(url="x", private_token="x"),  # noqa: S106
        )

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
    def test_instance(self, fx_gitlab_cache: GitLabLocalCache):
        """Can get the current remote GitLab instance (hostname)."""
        assert fx_gitlab_cache._instance == "gitlab.example.com"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_head_commit(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get the latest commit ID from the current source."""
        result = fx_gitlab_cache_pop._head_commit
        assert isinstance(result, str)
        assert len(result) > 0

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
        expected = Source(
            instance=urlparse(fx_config.STORE_GITLAB_ENDPOINT).hostname,
            project=fx_gitlab_cache._project_id,
            ref=fx_gitlab_cache._ref,
        )
        assert fx_gitlab_cache._source == expected

    @pytest.mark.parametrize("cached", [True, False])
    def test_cached_source(self, fx_config: Config, fx_gitlab_cache_pop: GitLabLocalCache, cached: bool):
        """Can get source known to cache."""
        expected = Source(
            instance=urlparse(fx_config.STORE_GITLAB_ENDPOINT).hostname,
            project=fx_gitlab_cache_pop._project_id,
            ref=fx_gitlab_cache_pop._ref,
        )

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
        source = Source(
            instance=urlparse(fx_config.STORE_GITLAB_ENDPOINT).hostname,
            project=fx_gitlab_cache._project_id,
            ref=fx_gitlab_cache._ref,
        )
        record = RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)
        record_config_ = {**fx_record_config_min, "file_revision": commit}
        record_ = RecordRevision.loads(record_config_)

        fx_gitlab_cache._build_cache(records=[record], source=source, head_commit_id=commit)

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
                "SELECT value FROM meta WHERE key in ('source_instance', 'source_project', 'source_ref') ORDER BY key;"
            )
            cached_source = Source(instance=meta[0], project=meta[1], ref=meta[2])
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
        source = Source(
            instance=urlparse(fx_config.STORE_GITLAB_ENDPOINT).hostname,
            project=fx_gitlab_cache_pop._project_id,
            ref=fx_gitlab_cache_pop._ref,
        )

        # updated record
        fx_record_config_min["file_identifier"] = file_identifier
        fx_record_config_min["identification"]["edition"] = "2"
        raw_record = RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)
        record_config_ = {**fx_record_config_min, "file_revision": commit}
        record_ = RecordRevision.loads(record_config_)

        # original record (to ensure it's replaced)
        original_record = fx_gitlab_cache_pop.get()[0]
        assert original_record.file_identifier == file_identifier

        fx_gitlab_cache_pop._build_cache(records=[raw_record], source=source, head_commit_id=commit)

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

        `_create_refresh()` does not return anything itself, so we check the arguments passed to `_build_cache()`.
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

        fx_gitlab_cache_pop._create_refresh(records=[])

        # noinspection PyUnresolvedReferences
        fx_gitlab_cache_pop._build_cache.assert_called_once()  # assert _build_cache called with ref in head commit
        # noinspection PyUnresolvedReferences
        args, kwargs = fx_gitlab_cache_pop._build_cache.call_args

        source = kwargs.get("source", args[1] if len(args) > 1 else {})
        assert "instance" in source
        assert source["instance"] == "gitlab.example.com"
        assert "project" in source
        assert source["project"] == fx_gitlab_cache_pop._project_id
        assert "ref" in source
        assert source["ref"] == fx_gitlab_cache_pop._ref

        head_commit = kwargs.get("head_commit_id", args[1] if len(args) > 1 else None)
        assert head_commit == "x"

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_record_commit(self, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict):
        """Can fetch latest commit for a file in the remote repository."""
        file_identifier = "a1b2c3"
        commit = "abc123"
        path = "records/a1/b2/a1b2c3.json"
        fx_record_config_min["file_identifier"] = file_identifier
        expected = RawRecord(config_str=json.dumps(fx_record_config_min, ensure_ascii=False), commit_id=commit)

        results = _fetch_record_commit(project=fx_gitlab_cache._project, path=path, ref=fx_gitlab_cache._ref)
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

        assert results[0][1] == expected[0][1]  # record with 2nd edition
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
        assert results[0][1] == expected[0][1]  # record with 3rd edition (2nd skipped)

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
        applicable_value = Source(
            instance=urlparse(fx_config.STORE_GITLAB_ENDPOINT).hostname,
            project=fx_gitlab_cache_pop._project_id,
            ref=fx_gitlab_cache_pop._ref,
        )
        inapplicable_value = Source(instance="invalid", project="invalid", ref="invalid")
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
            assert "Local cache unavailable, creating from GitLab" in caplog.text

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
        assert "Local cache source unavailable, recreating from GitLab" in caplog.text

    def test_get(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get records from cache."""
        mocker.patch.object(fx_gitlab_cache_pop, "_ensure_exists", return_value=None)
        expected_file_identifier = "a1b2c3"
        expected_file_revision = "abc123"

        results = fx_gitlab_cache_pop.get()
        assert results[0].file_identifier == expected_file_identifier
        assert results[0].file_revision == expected_file_revision

    @pytest.mark.parametrize("selected", [{"x"}, {"x", "y"}, {"invalid"}])
    def test_get_hashes(
        self, fx_config: Config, fx_gitlab_cache: GitLabLocalCache, fx_record_config_min: dict, selected: set[str]
    ):
        """Can get SHA1 hashes of specified records."""
        commit = "x"
        source = Source(
            instance=urlparse(fx_config.STORE_GITLAB_ENDPOINT).hostname,
            project=fx_gitlab_cache._project_id,
            ref=fx_gitlab_cache._ref,
        )
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
        fx_gitlab_cache._build_cache(records=records, source=source, head_commit_id=commit)

        hashes = {
            p.record.file_identifier: p.record.sha1
            for p in [ProcessedRecord(logger=None, config_str=r.config_str, commit_id=r.commit_id) for r in records]
        }
        expected = {k: v for k, v in hashes.items() if k in selected}
        if selected == {"invalid"}:
            expected = {"invalid": None}

        results = fx_gitlab_cache.get_hashes(selected)
        assert results == expected

    def test_purge(self, mocker: MockerFixture, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can clear cache contents."""
        mocker.patch.object(fx_gitlab_cache_pop, "_ensure_exists", return_value=None)

        assert fx_gitlab_cache_pop.exists

        fx_gitlab_cache_pop.purge()

        assert not fx_gitlab_cache_pop.exists
        assert not fx_gitlab_cache_pop._cache_path.exists()


class TestCommitResults:
    """Test commit results data class."""

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("other", "expected"),
        [
            (CommitResults(branch="x", commit="x", changes={"create": [], "update": []}, actions=[]), True),
            (CommitResults(branch="x", commit="y", changes={"create": [], "update": []}, actions=[]), False),
            (1, False),
        ],
    )
    def test_eq(self, other: object, expected: bool):
        """Can compare instances."""
        base = CommitResults(branch="x", commit="x", changes={"create": [], "update": []}, actions=[])

        assert (base == other) is expected


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
            branch="x",
            cache_path=cache_path,
        )

    def test_len(self, fx_gitlab_store_pop: GitLabStore):
        """Can get number of records loaded into store."""
        assert len(fx_gitlab_store_pop) == 1

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_project(self, fx_gitlab_store: GitLabStore):
        """Can get the remote GitLab project object for the store."""
        result = fx_gitlab_store.project
        assert result.id == 1234

    def test_branch(self, fx_gitlab_store_pop: GitLabStore):
        """Can get selected branch."""
        assert fx_gitlab_store_pop.branch == fx_gitlab_store_pop._branch

    def test_head_commit(self, fx_gitlab_store_cached: GitLabStore):
        """Can get ID of the latest commit known to the local cache."""
        result = fx_gitlab_store_cached.head_commit
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.cov()
    def test_head_commit_no_cache(self, fx_gitlab_store: GitLabStore):
        """Can get ID of the latest commit known to the local cache."""
        result = fx_gitlab_store.head_commit
        assert result is None

    def test_get_remote_hashed_path(self, fx_gitlab_store: GitLabStore):
        """Can get the path to a record within the remote repository."""
        value = "123456.ext"
        expected = f"records/12/34/{value}"

        assert fx_gitlab_store._get_remote_hashed_path(value) == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("exists", [False, True])
    def test_ensure_branch(self, fx_gitlab_store: GitLabStore, exists: bool):
        """Can get the path to a record within the remote repository."""
        value = "existing" if exists else "new"

        fx_gitlab_store._ensure_branch(value)
        result = fx_gitlab_store.project.branches.list()
        assert any(branch.name == value for branch in result)

    @staticmethod
    def _make_commit_results(
        additions_ids: int, additions_total: int, updates_ids: int, updates_total: int
    ) -> CommitResults:
        """Helper to create expected CommitResults."""
        branch = "main"
        commit = "def456" if (additions_total + updates_total) > 0 else None
        changes = {
            "create": ["d4e5f6" for _ in range(0, additions_ids)],
            "update": ["a1b2c3" for _ in range(0, updates_ids)],
        }
        actions = [
            *[{"action": "create"} for _ in range(0, additions_total)],
            *[{"action": "update"} for _ in range(0, updates_total)],
        ]
        return CommitResults(branch=branch, commit=commit, changes=changes, actions=actions)

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            ("none", _make_commit_results(additions_ids=0, additions_total=0, updates_ids=0, updates_total=0)),
            ("add", _make_commit_results(additions_ids=1, additions_total=2, updates_ids=0, updates_total=0)),
            ("update", _make_commit_results(additions_ids=0, additions_total=0, updates_ids=1, updates_total=2)),
        ],
    )
    def test_commit(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        fx_gitlab_store_cached: GitLabStore,
        fx_revision_model_min: RecordRevision,
        mode: str,
        expected: CommitResults,
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
            assert "No actions to perform, aborting" in caplog.text
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
        with fx_gitlab_store_cached._cache._engine as tx:
            tx.execute(
                """UPDATE record SET sha1 = ? WHERE file_identifier = ?;""", (record.sha1, record.file_identifier)
            )

        fx_gitlab_store_cached._commit(records=[record], title="x", message="x", author=("x", "x@example.com"))

        assert "No actions to perform, aborting" in caplog.text

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
        ("mode", "expected"),
        [
            ("none", _make_commit_results(additions_ids=0, additions_total=0, updates_ids=0, updates_total=0)),
            ("noop", _make_commit_results(additions_ids=0, additions_total=0, updates_ids=0, updates_total=0)),
            ("add", _make_commit_results(additions_ids=1, additions_total=2, updates_ids=0, updates_total=0)),
            ("update", _make_commit_results(additions_ids=0, additions_total=0, updates_ids=1, updates_total=2)),
        ],
    )
    def test_push(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        fx_gitlab_store_cached: GitLabStore,
        fx_record_model_min: Record,
        mode: str,
        expected: CommitResults,
    ):
        """
        Can create, update or delete Records in the remote repository.

        High level public method.

        No-op case for submitted records that don't trigger any changes to remote repo.
        """
        records = [] if mode == "none" else [fx_record_model_min]
        mocker.patch.object(fx_gitlab_store_cached, "_commit", return_value=expected)
        mocker.patch.object(
            type(fx_gitlab_store_cached._cache), "_current", new_callable=PropertyMock, return_value=True
        )
        # ignore repopulating cache after push as we fake commit so cache won't be able to load new records
        mocker.patch.object(fx_gitlab_store_cached, "populate", return_value=None)

        results = fx_gitlab_store_cached.push(
            records=records, title="title", message="x", author=("x", "x@example.com")
        )

        assert results == expected
        if mode == "none":
            assert "No records to push, skipping" in caplog.text
        elif mode == "noop":
            assert "No records pushed, skipping cache invalidation" in caplog.text
        else:
            assert "Refreshing cache and reloading records into store to reflect pushed changes" in caplog.text

    @pytest.mark.parametrize("exists", [True, False])
    def test_purge(self, fx_gitlab_store_pop: GitLabStore, exists: bool):
        """Can purge loaded records."""
        if not exists:
            fx_gitlab_store_pop._records = {}

        fx_gitlab_store_pop.purge()

        assert len(fx_gitlab_store_pop.records) == 0
