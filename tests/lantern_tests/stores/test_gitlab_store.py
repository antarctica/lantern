import json
import logging

import pytest
from gitlab import Gitlab
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, StoreFrozenUnsupportedError
from lantern.stores.gitlab import CommitResults, GitLabSource, GitLabStore, ProcessedRecord
from tests.conftest import _revision_config_min


@pytest.mark.cov()
class TestProcessedRecord:
    """Test GitLab processed record helper class."""

    def test_init(self, fx_logger: logging.Logger, fx_record_config_min: dict):
        """Can initialise processed record."""
        config_str = json.dumps(fx_record_config_min)
        commit_id = "x"
        config_expected = {**fx_record_config_min, "file_revision": commit_id}

        result = ProcessedRecord(logger=fx_logger, config_str=config_str, commit_id="x")
        assert result.config == config_expected
        assert isinstance(result.record, RecordRevision)
        assert result.record.file_revision == commit_id


@pytest.mark.cov()
class TestCommitResults:
    """Test commit results, and implicitly related results stats, classes."""

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

    def test_unstructure(self):
        """Can serialise as JSON."""
        expected = {
            "branch": "x",
            "commit": "x",
            "new_identifiers": ["a", "b", "c"],
            "updated_identifiers": ["d", "e", "f"],
            "stats": {
                "new_records": 3,
                "new_files": 1,
                "updated_records": 3,
                "updated_files": 1,
            },
        }
        base = CommitResults(
            branch=expected["branch"],
            commit=expected["commit"],
            changes={"create": expected["new_identifiers"], "update": expected["updated_identifiers"]},
            actions=[{"action": "create", "...": "..."}, {"action": "update", "...": "..."}],
        )
        result = base.unstructure()
        assert result == expected


class TestGitLabSource:
    """Test GitLab source data class."""

    def test_init(self, fx_config: Config):
        """Can initialise."""
        GitLabSource(
            endpoint=fx_config.STORE_GITLAB_ENDPOINT,
            project=fx_config.STORE_GITLAB_PROJECT_ID,
            ref=fx_config.STORE_GITLAB_BRANCH,
        )

    @pytest.mark.parametrize("valid", [True, False])
    def test_instance(self, fx_config: Config, valid: bool):
        """Can initialise."""
        expected = "gitlab.example.com"
        endpoint = f"https://{expected}" if valid else "x"
        source = GitLabSource(
            endpoint=endpoint,
            project=fx_config.STORE_GITLAB_PROJECT_ID,
            ref=fx_config.STORE_GITLAB_BRANCH,
        )

        if not valid:
            with pytest.raises(ValueError, match=r"Invalid endpoint."):
                _ = source.instance
            return

        assert source.instance == expected


class TestGitLabStore:
    """Test GitLab store."""

    @staticmethod
    def _fetch_record_head_commit(file_identifier: str) -> RecordRevision | None:
        """Mock `_fetch_record_head_commit`."""
        if file_identifier == "invalid":
            return None
        result = {**_revision_config_min(), "file_identifier": file_identifier}
        return ProcessedRecord(
            config_str=json.dumps(result), commit_id=result["file_revision"], logger=logging.getLogger()
        ).record

    def _fetch_all_records_head_commit(self) -> list[RecordRevision]:
        """Mock `_fetch_all_records_head_commit`."""
        return [self._fetch_record_head_commit(fid) for fid in ["a1b2c3", "d4e5f6"]]

    def test_init(self, fx_logger: logging.Logger, fx_config: Config, fx_gitlab_source: GitLabSource):
        """Can initialise store."""
        GitLabStore(logger=fx_logger, source=fx_gitlab_source, access_token=fx_config.STORE_GITLAB_TOKEN)

    def test_init_frozen(self, fx_logger: logging.Logger, fx_config: Config, fx_gitlab_source: GitLabSource):
        """Cannot initialise frozen store."""
        with pytest.raises(StoreFrozenUnsupportedError):
            GitLabStore(
                logger=fx_logger, source=fx_gitlab_source, access_token=fx_config.STORE_GITLAB_TOKEN, frozen=True
            )

    def test_get_remote_hashed_path(self, fx_gitlab_store: GitLabStore):
        """Can get the path to a record within the remote repository."""
        value = "123456.ext"
        expected = f"records/12/34/{value}"

        assert fx_gitlab_store._get_remote_hashed_path(value) == expected

    def test_len(self, mocker: MockerFixture, fx_gitlab_store: GitLabStore):
        """Can get count of records in store."""
        mocker.patch.object(fx_gitlab_store, "_fetch_record_head_commit", side_effect=self._fetch_record_head_commit)
        mocker.patch.object(
            fx_gitlab_store, "_fetch_all_records_head_commit", side_effect=self._fetch_all_records_head_commit
        )

        assert len(fx_gitlab_store) > 0

    @pytest.mark.cov()
    def test_frozen(self, fx_gitlab_store: GitLabStore):
        """Can get whether store is frozen."""
        assert fx_gitlab_store.frozen is False

    @pytest.mark.cov()
    def test_source(self, fx_gitlab_store: GitLabStore, fx_gitlab_source: GitLabSource):
        """Can get source."""
        assert isinstance(fx_gitlab_store.source, GitLabSource)
        assert fx_gitlab_store.source == fx_gitlab_source

    @pytest.mark.cov()
    @pytest.mark.block_network
    def test_client(self, fx_gitlab_store: GitLabStore):
        """Can get GitLab client."""
        assert isinstance(fx_gitlab_store._client, Gitlab)

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_project(self, fx_gitlab_store: GitLabStore):
        """Can get remote GitLab project."""
        result = fx_gitlab_store._project
        assert result.id == 1234

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_head_commit(self, fx_gitlab_store: GitLabStore):
        """Can get ID of the latest remote commit."""
        result = fx_gitlab_store.head_commit
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("exists", [True, False])
    def test_fetch_record_head_commit(self, exists: bool, fx_gitlab_store: GitLabStore):
        """Can get a record and its head commit if in the remote repository."""
        file_identifier = "a1b2c3" if exists else "invalid"
        file_revision = "abc123"

        result = fx_gitlab_store._fetch_record_head_commit(file_identifier=file_identifier)
        if exists:
            assert isinstance(result, RecordRevision)
            assert result.file_identifier == file_identifier
            assert result.file_revision == file_revision
        else:
            assert result is None

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_fetch_all_records_head_commit(self, mocker: MockerFixture, fx_gitlab_store: GitLabStore):
        """Can get all records and their head commits in the remote repository."""
        mocker.patch.object(fx_gitlab_store, "_fetch_record_head_commit", side_effect=self._fetch_record_head_commit)

        results = fx_gitlab_store._fetch_all_records_head_commit()
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, RecordRevision) for r in results)

    @pytest.mark.parametrize("selected", [None, set(), {"a1b2c3"}, {"a1b2c3", "invalid"}])
    def test_select(self, mocker: MockerFixture, fx_gitlab_store: GitLabStore, selected: set[str] | None):
        """Can get selected records that exist."""
        mocker.patch.object(fx_gitlab_store, "_fetch_record_head_commit", side_effect=self._fetch_record_head_commit)
        mocker.patch.object(
            fx_gitlab_store, "_fetch_all_records_head_commit", side_effect=self._fetch_all_records_head_commit
        )
        expected_length = len(selected) if selected else 2  # local arbitrary value

        if selected is not None and "invalid" in selected:
            with pytest.raises(RecordsNotFoundError) as exc_info:
                fx_gitlab_store.select(file_identifiers=selected)
            assert exc_info.value.file_identifiers == {"invalid"}
            return

        result = fx_gitlab_store.select(file_identifiers=selected)
        assert len(result) == expected_length
        assert all(isinstance(r, RecordRevision) for r in result)

    @pytest.mark.parametrize("selected", ["a1b2c3", "invalid"])
    def test_select_one(self, mocker: MockerFixture, fx_gitlab_store: GitLabStore, selected: str):
        """Can get a record that exists."""
        mocker.patch.object(fx_gitlab_store, "_fetch_record_head_commit", side_effect=self._fetch_record_head_commit)

        if selected == "invalid":
            with pytest.raises(RecordNotFoundError):
                fx_gitlab_store.select_one(file_identifier=selected)
            return

        result = fx_gitlab_store.select_one(file_identifier=selected)
        assert isinstance(result, RecordRevision)
        assert result.file_identifier == selected

    @pytest.mark.block_network
    @pytest.mark.parametrize("selection", [set(), {"a1b2c3"}, {"a1b2c3", "invalid"}])
    def test_get_hashes(self, mocker: MockerFixture, fx_gitlab_store: GitLabStore, selection: set[str]):
        """Can get record hashes for selected records that exist."""
        mocker.patch.object(fx_gitlab_store, "_fetch_record_head_commit", side_effect=self._fetch_record_head_commit)

        result = fx_gitlab_store._get_hashes(file_identifiers=selection)
        assert len(result) == len(selection)
        for fid in selection:
            assert fid in result
            if fid == "invalid":
                assert result[fid] is None
                continue
            assert result[fid] == fx_gitlab_store._fetch_record_head_commit(file_identifier=fid).sha1

    @pytest.mark.vcr
    @pytest.mark.block_network
    @pytest.mark.parametrize("exists", [False, True])
    def test_ensure_branch(self, fx_gitlab_store: GitLabStore, exists: bool):
        """Can get the path to a record within the remote repository."""
        value = "existing" if exists else "new"

        fx_gitlab_store._ensure_branch(value)
        result = fx_gitlab_store._project.branches.list()
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

    @pytest.mark.cov()
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
        caplog: pytest.LogCaptureFixture,
        fx_gitlab_store: GitLabStore,
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
            record = fx_gitlab_store.select_one("a1b2c3")
            record.identification.edition = str(1)
            records.append(record)

        results = fx_gitlab_store._commit(records=records, title="x", message="x", author=("x", "x@example.com"))
        assert results == expected
        if mode == "none":
            assert "No actions to perform, aborting" in caplog.text
            return
        if mode == "add":
            assert "Committing 1 added records across 2 new files, 0 updated records" in caplog.text
        if mode == "update":
            assert "Committing 0 additional records, 1 updated records across 2 modified files" in caplog.text

    @pytest.mark.cov()
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_commit_no_changes(self, caplog: pytest.LogCaptureFixture, fx_gitlab_store: GitLabStore):
        """Does not commit records that haven't changed."""
        record = self._fetch_record_head_commit("a1b2c3")

        fx_gitlab_store._commit(records=[record], title="x", message="x", author=("x", "x@example.com"))
        assert "No actions to perform, aborting" in caplog.text

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
        fx_gitlab_store: GitLabStore,
        fx_record_model_min: Record,
        mode: str,
        expected: CommitResults,
    ):
        """
        Can create, update or delete Records in the remote repository.

        High level public method.

        No-op case for submitted records that don't trigger any changes to remote repo.
        """
        mocker.patch.object(fx_gitlab_store, "_commit", return_value=expected)
        records = [] if mode == "none" else [fx_record_model_min]

        results = fx_gitlab_store.push(records=records, title="title", message="x", author=("x", "x@example.com"))

        assert results == expected
        if mode == "none":
            assert "No records to push, skipping" in caplog.text
        elif mode == "noop":
            assert "No records pushed, skipping cache invalidation" in caplog.text
        else:
            assert "Push successful as commit" in caplog.text
