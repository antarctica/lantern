import json
import logging
from base64 import b64decode
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol, TypedDict
from urllib.parse import urlparse

from gitlab import Gitlab, GitlabGetError
from gitlab.v4.objects import Project

from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.shims import inject_truststore_into_ssl_boto_fix
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, Store, StoreFrozenUnsupportedError

inject_truststore_into_ssl_boto_fix()


@dataclass
class GitLabSource:
    """
    Elements of a GitLab remote repository.

    E.g. https://gitlab.data.bas.ac.uk/foo/bar/.../main (where 'foo/bar' is a project with ID '123'), gives:
    - endpoint: 'https://gitlab.data.bas.ac.uk'
    - instance: 'gitlab.data.bas.ac.uk'
    - project: '123'
    - ref: 'main'
    """

    endpoint: str
    project: str
    ref: str

    @property
    def instance(self) -> str:
        """GitLab instance hostname."""
        _host = urlparse(self.endpoint).hostname
        if _host:
            return _host
        msg = "Invalid endpoint."
        raise ValueError(msg) from None


class ProcessedRecord:
    """
    Represents a record in raw and model forms with eager processing.

    Available representations:
    - record revision configuration dict
    - RecordRevision instance
    """

    def __init__(self, logger: logging.Logger | None, config_str: str, commit_id: str) -> None:
        self._config = {"file_revision": commit_id, **json.loads(config_str)}
        self._record = RecordRevision.loads(value=self.config, check_supported=True, logger=logger)

    @property
    def config(self) -> dict:
        """Record revision config dict."""
        return self._config

    @property
    def record(self) -> RecordRevision:
        """RecordRevision instance."""
        return self._record


class CommitData(TypedDict):
    """GitLab API commit structure."""

    branch: str
    commit_message: str
    author_name: str
    author_email: str
    actions: list[dict]


class CommitResultsStats:
    """Statistics for a commit transaction."""

    def __init__(self, changes: dict, actions: list) -> None:
        # *_total tracks individual files not records so cannot rely on `len(*_id)`
        self.new_records = len(changes["create"])
        self.new_files = sum(1 for action in actions if action["action"] == "create")
        self.updated_records = len(changes["update"])
        self.updated_files = sum(1 for action in actions if action["action"] == "update")

    @property
    def new_msg(self) -> str:
        """Log message for new records."""
        return (
            f"{self.new_records} added records across {self.new_files} new files"
            if self.new_records >= 1
            else "0 additional records"
        )

    @property
    def updated_msg(self) -> str:
        """Log message for updated records."""
        return (
            f"{self.updated_records} updated records across {self.updated_files} modified files"
            if self.updated_records >= 1
            else "0 updated records"
        )


class CommitResults:
    """Results from a commit transaction."""

    def __init__(self, branch: str, commit: str | None, changes: dict, actions: list) -> None:
        self.branch = branch
        self.commit = commit
        self.new_identifiers = changes["create"]
        self.updated_identifiers = changes["update"]
        self.stats = CommitResultsStats(changes=changes, actions=actions)

    def __eq__(self, other: object) -> bool:
        """Equality comparison for tests."""
        if not isinstance(other, CommitResults):
            return False
        return (
            self.branch == other.branch
            and self.commit == other.commit
            and self.new_identifiers == other.new_identifiers
            and self.updated_identifiers == other.updated_identifiers
            and self.stats.new_records == other.stats.new_records
            and self.stats.new_files == other.stats.new_files
            and self.stats.updated_records == other.stats.updated_records
            and self.stats.updated_files == other.stats.updated_files
        )


class GetHashesProtocol(Protocol):
    """Callable protocol for selecting record hashes from Store."""

    def __call__(  # pragma: no branch  # noqa: D102
        self, file_identifiers: set[str]
    ) -> dict[str, str | None]: ...


class GitLabStore(Store):
    """
    Basic read-write store backed by a remote GitLab repository.

    Uses https://python-gitlab.readthedocs.io/ and the GitLab API, rather than the generic Git protocol.

    Does not support freezing or deleting or renaming/moving records.

    Records can be added or updated using `push()`, which commits changes to the remote GitLab project repository.
    """

    def __init__(self, logger: logging.Logger, source: GitLabSource, access_token: str, frozen: bool = False) -> None:
        """Initialise."""
        if frozen:
            msg = "GitLab stores cannot be frozen."
            raise StoreFrozenUnsupportedError(msg) from None

        self._logger = logger
        self._source = source
        self._access_token = access_token
        self._get_hashes_callable: GetHashesProtocol = self._get_hashes

    @staticmethod
    def _get_remote_hashed_path(file_name: str) -> str:
        """
        Get the hashed storage path for a file name.

        A hashed path is used to avoid too many files being in a single directory.

        For `_get_hashed_path(file_name="0be5339c-9d35-44c9-a10f-da4b5356840b.json")`
        return: 'records/0b/e5/0b5339c-9d35-44c9-a10f-da4b5356840b.json'
        """
        return f"records/{file_name[:2]}/{file_name[2:4]}/{file_name}"

    def __len__(self) -> int:
        """
        Count of records in store.

        Deliberately simplistic as this method is not expected to be used for this store.
        """
        return len(self.select())

    @property
    def frozen(self) -> bool:
        """Static value, as GitLab stores cannot be frozen."""
        return False

    @property
    def source(self) -> GitLabSource:
        """GitLab repository information."""
        return self._source

    @cached_property
    def _client(self) -> Gitlab:
        """GitLab API client."""
        return Gitlab(url=self._source.endpoint, private_token=self._access_token)

    @property
    def _project(self) -> Project:
        """GitLab project."""
        return self._client.projects.get(self._source.project)

    @property
    def head_commit(self) -> str:
        """ID of the latest commit in the GitLab repository."""
        return self._project.commits.list(ref_name=self._source.ref, get_all=False)[0].id

    def _fetch_record_head_commit(self, file_identifier: str) -> RecordRevision | None:
        """
        Get specific record from the GitLab repository.

        Fetches record configuration and the ID of its head commit.
        """
        file_path = self._get_remote_hashed_path(f"{file_identifier}.json")
        self._logger.info(f"Fetching remote record '{file_path}'")
        try:
            file_contents = self._project.files.get(file_path=file_path, ref=self._source.ref)
        except GitlabGetError:
            return None
        return ProcessedRecord(
            logger=self._logger,
            config_str=b64decode(file_contents.content).decode("utf-8"),
            commit_id=file_contents.last_commit_id,
        ).record

    def _fetch_all_records_head_commit(self) -> list[RecordRevision]:
        """
        Get all records from the GitLab repository.

        Fetches record configurations and head commit IDs.
        """
        records = []
        self._logger.info("Fetching all remote records.")
        for item in self._project.repository_tree(path="records", ref=self._source.ref, recursive=True, iterator=True):
            if item["type"] == "blob" and item["path"].endswith(".json"):
                file_identifier = item["path"].split("/")[-1].removesuffix(".json")
                records.append(self._fetch_record_head_commit(file_identifier=file_identifier))
        return records

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """
        Get some or all records filtered by file identifier.

        Raises a `RecordsNotFoundError` exception if any selected records aren't found (i.e. all or nothing).
        """
        file_identifiers = file_identifiers or set()
        selected: list[RecordRevision] = []
        missing_fids = set()

        if len(file_identifiers) == 0:
            self._logger.info("Selecting all records.")
            return self._fetch_all_records_head_commit()
        self._logger.info(f"Selecting {len(file_identifiers)} records.")
        for file_identifier in file_identifiers:
            result = self._fetch_record_head_commit(file_identifier)
            if result is None:
                missing_fids.add(file_identifier)
                continue
            selected.append(result)
        if len(missing_fids) > 0:
            raise RecordsNotFoundError(missing_fids) from None

        return selected

    def select_one(self, file_identifier: str) -> RecordRevision:
        """
        Get specific record by file identifier.

        Raises a `RecordNotFoundError` exception if not found.
        """
        self._logger.info(f"Selecting record '{file_identifier}'.")
        result = self._fetch_record_head_commit(file_identifier)
        if result is None:
            raise RecordNotFoundError(file_identifier) from None
        return result

    def _ensure_branch(self, branch: str) -> None:
        """
        Ensure branch exists in the GitLab repository.

        New branches are always created from `main`.
        """
        try:
            _ = self._project.branches.get(branch)
        except GitlabGetError:
            self._logger.info(f"Branch '{branch}' does not exist, creating")
            self._project.branches.create({"branch": branch, "ref": "main"})

    def _get_hashes(self, file_identifiers: set[str]) -> dict[str, str | None]:
        """
        Get SHA1 hashes for selected records.

        For determining records that have changed committing.

        Returns a mapping of file identifiers to SHA1 hashes, or `None` if a record isn't found.
        """
        hashes = {}
        self._logger.info(f"Getting hashes for {len(file_identifiers)} selected records.")
        for file_identifier in file_identifiers:
            record = self._fetch_record_head_commit(file_identifier)
            hashes[file_identifier] = record.sha1 if record else None
        return hashes

    def _commit(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> CommitResults:
        """
        Commit records to the GitLab repository.

        New/updated actions are determined by trying to compare SHA1 hashes, where:
        - available and matching = the record exists in the remote and is unchanged = skipped
        - available and not matching = the record exists in the remote but is different = update
        - unavailable = the record does not exist in the remote = a new record

        Where a commit is generated, file identifiers are returned for new and/or updated records, and statistics on
        the number of underlying files changed (where each record is stored as a JSON and XML file).
        """
        changes: dict[str, list[str]] = {"update": [], "create": []}
        data: CommitData = {
            "branch": self._source.ref,
            "commit_message": f"{title}\n{message}",
            "author_name": author[0],
            "author_email": author[1],
            "actions": [],
        }

        existing_hashes = self._get_hashes_callable(file_identifiers={record.file_identifier for record in records})
        for record in records:
            self._logger.debug(f"Existing: '{existing_hashes[record.file_identifier]}', New: '{record.sha1}'")
            if record.sha1 == existing_hashes[record.file_identifier]:
                self._logger.debug(f"Record '{record.file_identifier}' is unchanged, skipping")
                continue

            action = "update"
            if existing_hashes[record.file_identifier] is None:
                action = "create"
                self._logger.debug(f"Record '{record.file_identifier}' is new, action set to create")

            changes[action].append(record.file_identifier)
            data["actions"].extend(
                [
                    {
                        "action": action,
                        "file_path": self._get_remote_hashed_path(f"{record.file_identifier}.json"),
                        "content": record.dumps_json(strip_admin=False),
                    },
                    {
                        "action": action,
                        "file_path": self._get_remote_hashed_path(f"{record.file_identifier}.xml"),
                        "content": record.dumps_xml(strip_admin=False),
                    },
                ]
            )
        results = CommitResults(branch=self._source.ref, commit=None, changes=changes, actions=data["actions"])

        if not data["actions"]:
            self._logger.info("No actions to perform, aborting")
            return results

        self._logger.debug(f"Ensuring target branch {self._source.ref} exists")
        self._ensure_branch(branch=self._source.ref)

        self._logger.info(f"Committing {results.stats.new_msg}, {results.stats.updated_msg}")
        # noinspection PyTypeChecker
        commit = self._project.commits.create(data)
        results.commit = commit.id
        return results

    def push(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> CommitResults:
        """
        Add or update records in the GitLab repository.

        Returns commit results including resulting commit for further optional processing.
        """
        empty_results = CommitResults(
            branch=self._source.ref, commit=None, changes={"create": [], "update": []}, actions=[]
        )
        if len(records) == 0:
            self._logger.info("No records to push, skipping")
            return empty_results

        results = self._commit(records=records, title=title, message=message, author=author)

        if results.commit is None:
            self._logger.info("No records pushed, skipping cache invalidation")
            return empty_results

        self._logger.info(f"Push successful as commit '{results.commit}'")

        return results
