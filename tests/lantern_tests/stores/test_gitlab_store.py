import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, PropertyMock

import pytest
from gitlab import Gitlab
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.lib.metadata_library.models.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import GitLabLocalCache, GitLabStore, RemoteStoreUnavailableError
from tests.resources.stores.fake_records_store import FakeRecordsStore


class TestGitLabLocalCache:
    """Test GitLab local cache."""

    def test_init(self, fx_logger: logging.Logger):
        """Can initialise store."""
        with TemporaryDirectory() as tmp_path:
            cache_path = Path(tmp_path) / ".cache"

        GitLabLocalCache(
            logger=fx_logger,
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

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_head_commit_id(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can get ID of the latest commit known to the cache."""
        result = fx_gitlab_cache_pop._head_commit_id
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

    def test_load_record_json(self, fx_gitlab_cache: GitLabLocalCache, fx_record_config_minimal_item: dict):
        """Can load a record from a JSON record config and file identifier."""
        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)

            config_path = temp_path / f"{fx_record_config_minimal_item['file_identifier']}.json"
            with config_path.open("w") as f:
                json.dump(fx_record_config_minimal_item, f, indent=2)

            record = fx_gitlab_cache._load_record(config_path, file_revision="x")
            assert isinstance(record, RecordRevision)

    def test_load_record_pickle(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Can load a pickled RecordRevision record from populated cache."""
        id_ = "a1b2c3"
        record_path = fx_gitlab_cache_pop._records_path / f"{id_}.pickle"

        record = fx_gitlab_cache_pop._load_record(record_path)
        assert record.file_identifier == id_

    def test_build_cache(
        self,
        fx_gitlab_cache: GitLabLocalCache,
        fx_record_config_minimal_item: dict,
    ):
        """
        Can populate cache with record configurations and other required context.

        `fx_record_config_minimal_item` needed to include `file_identifier` in test record.
        """
        head_commit = {"x": "x"}
        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)

            config_path = temp_path / f"{fx_record_config_minimal_item['file_identifier']}.json"
            with config_path.open("w") as f:
                json.dump(fx_record_config_minimal_item, f, indent=2)

            config_paths = [config_path]
            commits = {fx_record_config_minimal_item["file_identifier"]: "x"}

            fx_gitlab_cache._build_cache(config_paths=config_paths, config_commits=commits, head_commit=head_commit)

        assert fx_gitlab_cache._exists
        assert len(list(fx_gitlab_cache._records_path.glob("*.json"))) == 1
        assert len(list(fx_gitlab_cache._records_path.glob("*.pickle"))) == 1

        with fx_gitlab_cache._head_path.open() as f:
            data = json.load(f)
            assert data == head_commit

        with fx_gitlab_cache._hashes_path.open() as f:
            data = json.load(f)
            assert data == {"hashes": {"x": "e9dc256d287ce17eb8feeddc4cb34e53da61d459"}}

        with fx_gitlab_cache._commits_path.open() as f:
            data = json.load(f)
            assert data == {"commits": {"x": "x"}}

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_file_commits(self, fx_gitlab_cache: GitLabLocalCache):
        """Can fetch latest commit for a set of files in the remote repository."""
        expected = {"a1b2c3": "abc123"}
        paths = ["records/a1/b2/a1b2c3.json"]

        results = fx_gitlab_cache._fetch_file_commits(record_paths=paths)
        assert results == expected

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_project_archive(self, fx_gitlab_cache: GitLabLocalCache):
        """Can fetch and extract an archive all record files in the remote repository."""
        expected = "a1b2c3"

        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)

            local_paths, remote_paths = fx_gitlab_cache._fetch_project_archive(workspace=temp_path)

        assert f"{expected}.json" in [path.name for path in local_paths]
        assert f"records/{expected[:2]}/{expected[2:4]}/{expected}.json" in remote_paths

    def test_create(
        self, mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache, fx_record_config_minimal_item: dict
    ):
        """
        Can fetch and populate cache with records from remote repository.

        This mocks fetching data as `_create()` is a high-level method and fetch methods are tested elsewhere.
        """
        fid = "a1b2c3"
        commit = "abc123"

        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)

            fx_record_config_minimal_item["file_identifier"] = fid
            config_path = temp_path / f"{fx_record_config_minimal_item['file_identifier']}.json"
            with config_path.open("w") as f:
                json.dump(fx_record_config_minimal_item, f, indent=2)
            config_paths = [config_path]
            config_urls = [f"records/{fid[:2]}/{fid[2:4]}/{fid}.json"]
            mocker.patch.object(fx_gitlab_cache, "_fetch_project_archive", return_value=(config_paths, config_urls))

            commit_mapping = {fid: commit}
            mocker.patch.object(fx_gitlab_cache, "_fetch_file_commits", return_value=commit_mapping)

            head_commit = {"id": commit}
            mock_project = MagicMock()
            mock_project.commits.get.return_value.attributes = head_commit
            mocker.patch.object(type(fx_gitlab_cache), "_project", new_callable=PropertyMock, return_value=mock_project)

            fx_gitlab_cache._create()

        assert fx_gitlab_cache._exists

    @pytest.mark.parametrize(
        ("online", "cached", "current"),
        [(False, False, False), (True, False, False), (False, True, False), (True, True, False), (True, True, True)],
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

        if not cached:
            fx_gitlab_cache_pop.purge()
            assert not fx_gitlab_cache_pop._path.exists()
        if online and not cached:
            # in `fx_gitlab_cache_pop`, `_create()` is mocked to copy reference cache so safe
            fx_gitlab_cache_pop._create()

        if not online and not cached:
            with pytest.raises(RemoteStoreUnavailableError):
                fx_gitlab_cache_pop._ensure_exists()
            return

        fx_gitlab_cache_pop._ensure_exists()

        if not online:
            assert "Cannot check if records cache is current, loading possibly stale records" in caplog.text

        if online and not current:
            assert "Cached records are not up to date, reloading from GitLab" in caplog.text

        if online and current:
            assert "Records cache exists and is current, no changes needed." in caplog.text

        assert fx_gitlab_cache_pop._exists

    @pytest.mark.parametrize("exists", [True, False])
    def test_get_record(self, fx_gitlab_cache_pop: GitLabLocalCache, exists: bool):
        """Can get specific record from cache if it exists."""
        expected = "a1b2c3" if exists else "invalid"

        if not exists:
            with pytest.raises(RecordNotFoundError):
                fx_gitlab_cache_pop._get_record(expected)
            return

        record = fx_gitlab_cache_pop._get_record(expected)
        assert record.file_identifier == expected

    @pytest.mark.parametrize(
        ("include", "exclude", "expected_records"),
        [
            (
                [],
                [],
                ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea", "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"],
            ),
            (
                ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea"],
                [],
                ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea"],
            ),
            (
                ["53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"],
                [],
                [
                    "e30ac1c0-ed6a-49bd-8ca3-205610bf91bf",
                    "dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
                    "bcacfe16-52da-4b26-94db-8a567e4292db",
                    "4ba929ac-ca32-4932-a15f-38c1640c0b0f",
                    "e0df252c-fb8b-49ff-9711-f91831b66ea2",
                    "5ab58461-5ba7-404d-a904-2b4efcb7556e",
                    "57327327-4623-4247-af86-77fb43b7f45b",
                    "f90013f6-2893-4c72-953a-a1a6bc1919d7",
                    "09dbc743-cc96-46ff-8449-1709930b73ad",
                    "8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
                    "589408f0-f46b-4609-b537-2f90a2f61243",
                    "30825673-6276-4e5a-8a97-f97f2094cd25",
                    "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",
                    "c993ea2b-d44e-4ca0-9007-9a972f7dd117",
                    "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",
                ],
            ),
            (
                [],
                ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea"],
                ["53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"],
            ),
            (
                ["unknown"],
                [],
                [],
            ),
        ],
    )
    def test_get(
        self,
        fx_gitlab_cache: GitLabLocalCache,
        include: list[str],
        exclude: list[str],
        expected_records: list[str],
    ):
        """
        Can get records and summaries from cache by including or excluding certain records.

        Cache is populated with records from the FakeRecordsStore to give a pool of records to filter.

        - 8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea is a single standalone record
        - 53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2 is a record with two related records
        """
        fake_store = FakeRecordsStore(logger=fx_gitlab_cache._logger)
        _inc_records = ["8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea", "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2"]
        _related_records = [
            "e30ac1c0-ed6a-49bd-8ca3-205610bf91bf",
            "dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            "bcacfe16-52da-4b26-94db-8a567e4292db",
            "4ba929ac-ca32-4932-a15f-38c1640c0b0f",
            "e0df252c-fb8b-49ff-9711-f91831b66ea2",
            "5ab58461-5ba7-404d-a904-2b4efcb7556e",
            "57327327-4623-4247-af86-77fb43b7f45b",
            "f90013f6-2893-4c72-953a-a1a6bc1919d7",
            "09dbc743-cc96-46ff-8449-1709930b73ad",
            "8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
            "bcacfe16-52da-4b26-94db-8a567e4292db",
            "589408f0-f46b-4609-b537-2f90a2f61243",
            "30825673-6276-4e5a-8a97-f97f2094cd25",
            "e30ac1c0-ed6a-49bd-8ca3-205610bf91bf",
            "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",
            "c993ea2b-d44e-4ca0-9007-9a972f7dd117",
            "dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",
        ]
        if include:
            # when only including certain records, related records will also be returned
            _inc_records = [*_inc_records, *_related_records]

        fake_store.populate(inc_records=_inc_records)

        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)
            for record in fake_store.records:
                config_path = temp_path / f"{record.file_identifier}.json"
                with config_path.open("w") as f:
                    json.dump(record.dumps(), f, indent=2)
            config_paths = list(temp_path.glob("*.json"))
            commits = {record.file_identifier: "x" for record in fake_store.records}
            fx_gitlab_cache._build_cache(config_paths=config_paths, config_commits=commits, head_commit={"x": "x"})

            results = fx_gitlab_cache.get(inc_records=include, exc_records=exclude)
            records = [r.file_identifier for r in results]
            assert sorted(expected_records) == sorted(records)

    def test_get_invalid(self, fx_gitlab_cache_pop: GitLabLocalCache):
        """Cannot get records where both include and exclude parameters are set."""
        with pytest.raises(ValueError, match="Including and excluding records is not supported."):
            fx_gitlab_cache_pop.get(inc_records=["x"], exc_records=["x"])

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
        fx_record_revision_minimal_iso: RecordRevision,
        mode: str,
        expected: dict[str, int],
    ):
        """Can create, update or delete one or more records in the remote repository."""
        records = []

        if mode == "add":
            fx_record_revision_minimal_iso.file_identifier = "d4e5f6"
            records.append(fx_record_revision_minimal_iso)
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

    @pytest.mark.parametrize(("inc_records", "exc_records"), [(None, None), ([], [])])
    def test_populate(self, fx_gitlab_store_cached: GitLabStore, inc_records: list | None, exc_records: list | None):
        """
        Can populate the store with records from the remote repository, via a local cache.

        High level public method.
        """
        assert len(fx_gitlab_store_cached.records) == 0
        fx_gitlab_store_cached.populate(inc_records=inc_records, exc_records=exc_records)
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
        fx_record_minimal_item: Record,
        mode: str,
        stats: dict[str, int],
    ):
        """
        Can create, update or delete Records in the remote repository.

        High level public method.

        No-op case for submitted records that don't trigger any changes to remote repo.
        """
        records = [] if mode == "none" else [fx_record_minimal_item]
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
