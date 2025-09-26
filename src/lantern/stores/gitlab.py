from __future__ import annotations

import json
import logging
import pickle
import shutil
from base64 import b64decode
from copy import deepcopy
from functools import cached_property
from pathlib import Path

from gitlab import Gitlab
from gitlab.v4.objects import Project
from joblib import Parallel, delayed
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.log import init as init_logging
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, Store


class RemoteStoreUnavailableError(Exception):
    """Raised when records cannot be loaded from the remote store."""

    pass


class CacheIntegrityError(Exception):
    """Raised when the local cache integrity cannot be guaranteed."""

    pass


class CacheTooOutdatedError(Exception):
    """Raised when the local cache is too out-of-date to make sense refreshing."""

    pass


def _process_record(
    logger: logging.Logger, log_level: int, records_path: Path, record_data: tuple[str, str]
) -> tuple[str, str, str]:
    """
    Create and pickle a record instance from a record configuration data and revision identifier.

    Standalone function for use in parallel processing.
    """
    init_logging(log_level)
    config_str, commit_hash = record_data
    record_config = {"file_revision": commit_hash, **json.loads(config_str)}
    record = RecordRevision.loads(value=record_config, check_supported=True, logger=logger)
    record_path = records_path.joinpath(f"{record.file_identifier}.json")

    with record_path.with_suffix(".pickle").open(mode="wb") as f:
        # noinspection PyTypeChecker
        pickle.dump(record, f, pickle.HIGHEST_PROTOCOL)
    return record.file_identifier, record.sha1, record.file_revision


def _fetch_record_commit(project: Project, path: str, ref: str) -> tuple[str, str]:
    """
    Get a record configuration and its head commit ID from the GitLab project repository.

    Returns a tuple ('record configuration as JSON string', 'record commit string').

    Standalone function for use in parallel processing.
    """
    file_contents = project.files.get(file_path=path, ref=ref)
    return b64decode(file_contents.content).decode("utf-8"), file_contents.last_commit_id


class GitLabLocalCache:
    """
    A simple file based cache for records held in a GitLab project repository.

    Intended for efficiency and basic offline support.

    Loads record configuration files from a GitLab project repository and processes them into:
    - Pickled RecordRevision objects
    - a mapping of record file identifiers to their last known head commit
    - a mapping of record file identifiers to their SHA1 hashes

    The cache will automatically be populated or refreshed when records are accessed using `get()`. To manually
    invalidate the cache, call `purge()`, which will trigger a recreation of the cache on the next request for records.

    Once populated, the cache can be used in a basic offline mode, which may led to stale records being returned,
    indicated via a warning log message.

    Basic cache-validation is performed by comparing the head commit from when the cache was last refreshed, against
    the head commit in the remote project repository.

    Parallel processing is optionally available to improve the performance of:
    - fetching individual record configurations from GitLab
    - processing record configurations into Record instances
    """

    def __init__(
        self, logger: logging.Logger, parallel_jobs: int, path: Path, project_id: str, gitlab_client: Gitlab
    ) -> None:
        """Initialize cache."""
        self._logger = logger
        self._parallel_jobs = parallel_jobs
        self._path = path
        self._project_id = project_id
        self._client = gitlab_client

        self._ref = "main"
        self._records_path = self._path / "records"
        self._commits_path = self._path / "commits.json"
        self._head_path = self._path / "head_commit.json"
        self._hashes_path = self._path / "hashes.json"

    @cached_property
    def _online(self) -> bool:
        """
        Determine if the GitLab API is accessible.

        Cached for lifetime of instance on the assumption they are short-lived.
        """
        try:
            _ = self._project
        except RequestsConnectionError:
            return False
        return True

    @cached_property
    def _project(self) -> Project:
        """
        GitLab project.

        Cached for lifetime of instance as caches are implicitly tied to a single project.
        """
        return self._client.projects.get(self._project_id)

    @cached_property
    def _commits_mapping(self) -> dict[str, str]:
        """
        Load mapping of file identifiers to Git commits.

        Not valid if called before `_create()` is called where cache does not exist.

        Cached for lifetime of instance on the assumption they are short-lived.
        """
        with self._commits_path.open() as f:
            data = json.load(f)
        return data["commits"]

    @property
    def head_commit_local(self) -> str:
        """
        ID of the latest commit in the local cache.

        Not valid if called before `_create()` is called where cache does not exist.
        """
        with self._head_path.open() as f:
            cache_commit = json.load(f)
        return cache_commit["id"]

    @property
    def _head_commit_remote(self) -> str:
        """
        ID of the latest commit in remote project.

        Not valid if called before `_create()` is called where cache does not exist.
        """
        return self._project.commits.list(get_all=False)[0].id

    @property
    def exists(self) -> bool:
        """Determine if the cache exists."""
        return self._records_path.exists()

    @property
    def _current(self) -> bool:
        """
        Determine if cache is current or stale compared to the remote project repo.

        Where the cache does not exist, or a head commit ID isn't available, the cache is considered stale.
        """
        if not self.exists:
            return False

        return self.head_commit_local == self._head_commit_remote

    def _load_record_pickle(self, record_path: Path) -> RecordRevision:
        """Load record from Python pickle file."""
        self._logger.debug(f"Loading record from '{record_path.resolve()}'")
        with record_path.open(mode="rb") as file:
            return pickle.load(file)  # noqa: S301

    def _build_cache(self, records: list[tuple[str, str]], head_commit: dict) -> None:
        """
        Persist a set of record configurations to the local cache.

        Where:
        - `records` is a list of ('record configuration JSON strings', 'Git commit') tuples
        - `head_commit` is the current head commit of the remote project repository

        Steps:
        - parse each record config as a RecordRevision
        - create a mapping of file identifier to SHA1 hash of each record's configuration
        - create a mapping of file identifier to Git commit of each record version
        - pickle each RecordRevision to the cache directory
        - save details of the current head commit to a file for cache validation
        - save the mapping of SHA1 hashes
        - save the mapping of Git commits
        """
        hashes = {}
        commits = {}

        if self._hashes_path.exists():
            with self._hashes_path.open() as f:
                hashes = json.load(f)["hashes"]
        if self._commits_path.exists():
            with self._commits_path.open() as f:
                commits = json.load(f)["commits"]

        records_path = self._records_path
        records_path.mkdir(parents=True, exist_ok=True)

        self._logger.info(f"Processing {len(records)} records")
        results = Parallel(n_jobs=self._parallel_jobs)(
            delayed(_process_record)(self._logger, self._logger.level, records_path, record_data)
            for record_data in records
        )
        # results are list of (file_identifier, sha1, commit) tuples
        for result in results:
            hashes[result[0]] = result[1]
            commits[result[0]] = result[2]

        with self._head_path.open(mode="w") as f:
            json.dump(head_commit, f, indent=2)

        with self._hashes_path.open(mode="w") as f:
            data = {"hashes": hashes}
            json.dump(data, f, indent=2)

        with self._commits_path.open(mode="w") as f:
            data = {"commits": commits}
            json.dump(data, f, indent=2)

    def _fetch_record_commits(self) -> list[tuple[str, str]]:
        """
        Get all record configurations and their head commit IDs from the GitLab project repository.

        Returns a list of tuples ('record configuration as JSON string', 'record commit string').

        This method is annoyingly inefficient as a separate HTTP request is needed per-file to get the commit ID.
        This method won't scale to large numbers of records due to returning all record configurations in memory.
        """
        paths = []

        for item in self._project.repository_tree(path="records", ref=self._ref, recursive=True, iterator=True):
            if item["type"] != "blob" or not item["path"].endswith(".json"):
                continue
            paths.append(item["path"])

        self._logger.info(f"Fetching {len(paths)} records")
        # copy to allow use in parallel processing
        project_ = deepcopy(self._project)
        return Parallel(n_jobs=self._parallel_jobs)(
            delayed(_fetch_record_commit)(project_, path, self._ref) for path in paths
        )
        # results are list of ('record configuration as JSON string', 'record commit string') tuples

    def _fetch_latest_records(self) -> list[tuple[str, str]]:
        """
        Get record configurations and their latest commit IDs from the GitLab project repository from after a commit.

        Steps:
        - get a list of commits since the cache was last updated
        - raise a `CacheTooOutdated` exception if the number of commits is too high (as recreating the cache would be faster)
        - get a list of files changed across any subsequent commits
        - get the contents and head commit ID for any changed files

        Returns a list of tuples ('record configuration as JSON string', 'record commit string').

        This method is inefficient as each file within each commit needs separate HTTP requests. However, providing a
        limited number of commits since the last refresh, and a limited set of records in each commit, this will be more
        efficient than a full purge and create cycle.
        """
        limit = 50
        paths = []

        commit_range = f"{self.head_commit_local}..{self._head_commit_remote}"
        commits = self._project.commits.list(ref_name=commit_range, all=True)

        if len(commits) > limit:
            raise CacheTooOutdatedError() from None

        self._logger.info(f"Fetching commits in range {commit_range}")
        for commit in commits:
            for diff in commit.diff():
                if not diff["new_path"].startswith("records/") or not diff["new_path"].endswith(".json"):
                    continue
                if diff["renamed_file"]:
                    msg = "Renamed file in remote store, skipping. Partial updates do not support renamed files, use purge and recreate to ensure cache integrity."
                    raise CacheIntegrityError(msg)
                if diff["deleted_file"]:
                    msg = "Deleted file in remote store, skipping. Partial updates do not support deleted files, use purge and recreate to ensure cache integrity."
                    raise CacheIntegrityError(msg)
                paths.append(diff["new_path"])

        project_ = deepcopy(self._project)
        return Parallel(n_jobs=self._parallel_jobs)(
            delayed(_fetch_record_commit)(project_, path, self._ref) for path in paths
        )
        # results are list of ('record configuration as JSON string', 'record commit string') tuples

    def _create_refresh(self, records: list[tuple[str, str]]) -> None:
        """Common tasks for creating or refreshing the cache."""
        self._logger.info("Fetching head commit")
        head_commit = self._project.commits.get(self._head_commit_remote)

        self._logger.info("Populating local cache")
        self._build_cache(records=records, head_commit=head_commit.attributes)

    def _create(self) -> None:
        """
        Cache all records from remote store locally.

        Any existing cache is removed and recreated, regardless of whether it's up-to-date. Use `_refresh()` to update
        an existing cache instead.

        Annoyingly, and inefficiently, Git commits for records must be fetched using individual HTTP requests.

        Steps:
        - remove any existing cache directory if present
        - query the GitLab API for the JSON config and commit of all records
        - query the GitLab API for the head commit of the project repo
        - build and populate the local cache
        """
        self.purge()

        self._logger.info("Fetching all records (this will take some time)")
        records = self._fetch_record_commits()
        self._create_refresh(records=records)

    def _refresh(self) -> None:
        """
        Update cache with records that have changed in the remote store.

        The existing cache is preserved, only records changed in subsequent commits to the remote store are updated.
        Use `_create()` to start a new cache instead.

        Annoyingly, and inefficiently, Git commits and each record must be fetched using individual HTTP requests.

        Steps:
        - query the GitLab API for JSON configs and commits of changed records
        - query the GitLab API for the new head commit of the project repo
        - update and partially repopulate the local cache
        """
        pass
        self._logger.info("Fetching changed records (this may take some time)")
        try:
            records = self._fetch_latest_records()
        except CacheIntegrityError:
            self._logger.warning("Cannot refresh cache due to integrity issues, recreating entire cache instead.")
            self._create()
            return
        except CacheTooOutdatedError:
            self._logger.warning("Refreshing the cache would take too long, recreating entire cache instead.")
            self._create()
            return

        self._logger.info(f"{len(records)} records have been updated in remote repository")
        self._create_refresh(records=records)

    def _ensure_exists(self) -> None:
        """
        Ensure cache exists and is up-to-date.

        An existing, up-to-date, cache is not modified.
        """
        if not self._online and not self.exists:
            msg = "Local cache and GitLab unavailable. Cannot load records."
            raise RemoteStoreUnavailableError(msg) from None

        if self._online and not self.exists:
            self._logger.info("Local cache unavailable, creating from GitLab.")
            self._create()
            return

        if not self._online:
            self._logger.warning("Cannot check if records cache is current, loading possibly stale records.")
            return

        if self._online and not self._current:
            self._logger.warning("Cached records are not up to date, updating from GitLab.")
            self._refresh()
            return

        self._logger.info("Records cache exists and is current, no changes needed.")

    def get(self) -> list[RecordRevision]:
        """Load all available records from cache."""
        self._ensure_exists()
        record_paths = list(self._path.glob("records/*.pickle"))
        self._logger.info(f"Loading {len(record_paths)} records from cache")
        return [self._load_record_pickle(record_path) for record_path in record_paths]

    def get_hashes(self, file_identifiers: list[str]) -> dict[str, str]:
        """
        Get SHA1 hashes for a set of records to determine if any have changed compared to the cache.

        Returns a mapping of file identifiers to SHA1 hashes, or `None` if the record isn't in the cache.
        """
        with self._hashes_path.open() as f:
            hashes = json.load(f)["hashes"]

        return {identifier: hashes.get(identifier, None) for identifier in file_identifiers}

    def purge(self) -> None:
        """Clear cache contents."""
        if self._path.exists():
            self._logger.info("Purging cache")
            shutil.rmtree(self._path)


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

    def __init__(self, commit: str | None, changes: dict, actions: list) -> None:
        self.commit = commit
        self.new_identifiers = changes["create"]
        self.updated_identifiers = changes["update"]
        self.stats = CommitResultsStats(changes=changes, actions=actions)

    def __eq__(self, other: CommitResults) -> bool:
        """Equality comparison for tests."""
        return (
            self.commit == other.commit
            and self.new_identifiers == other.new_identifiers
            and self.updated_identifiers == other.updated_identifiers
            and self.stats.new_records == other.stats.new_records
            and self.stats.new_files == other.stats.new_files
            and self.stats.updated_records == other.stats.updated_records
            and self.stats.updated_files == other.stats.updated_files
        )


class GitLabStore(Store):
    """
    Basic read-write store backed by a remote GitLab project.

    Uses:
    - `GitLabLocalCache` class to access records from the remote repository for efficiency and offline support
    - https://python-gitlab.readthedocs.io/ to interact with the GitLab API, rather than use the generic Git protocol

    The store is initially empty, with records loaded from the local cache using `populate()`. This can be called
    multiple times to append additional records, or emptied using `purge()`.

    Records can be added or updated using `push()`, which commits the changes to the remote GitLab project repository.
    """

    def __init__(
        self,
        logger: logging.Logger,
        parallel_jobs: int,
        endpoint: str,
        access_token: str,
        project_id: str,
        cache_path: Path,
    ) -> None:
        self._logger = logger
        self._records: dict[str, RecordRevision] = {}
        self._client = Gitlab(url=endpoint, private_token=access_token)
        self._project_id = project_id
        self._branch = "main"

        self._cache_path = cache_path
        self._cache = GitLabLocalCache(
            logger=self._logger,
            parallel_jobs=parallel_jobs,
            path=self._cache_path,
            gitlab_client=self._client,
            project_id=self._project_id,
        )

    @cached_property
    def _project(self) -> Project:
        """
        GitLab project.

        Cached for lifetime of instance as caches are implicitly tied to a single project.
        """
        return self._client.projects.get(self._project_id)

    @property
    def records(self) -> list[RecordRevision]:
        """Loaded Records."""
        return list(self._records.values())

    @property
    def head_commit(self) -> str | None:
        """Local head commit reference if available."""
        return self._cache.head_commit_local if self._cache.exists else None

    @staticmethod
    def _get_remote_hashed_path(file_name: str) -> str:
        """
        Get the hashed storage path for a file name.

        A hashed path is used to avoid too many files being in a single directory.

        For `_get_hashed_path(file_name="0be5339c-9d35-44c9-a10f-da4b5356840b.json")`
        return: 'records/0b/e5/0b5339c-9d35-44c9-a10f-da4b5356840b.json'
        """
        return f"records/{file_name[:2]}/{file_name[2:4]}/{file_name}"

    def _commit(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> CommitResults:
        """
        Generate commit for a set of records.

        Main commit structure is determined by the GitLab API which includes an `action` to distinguish between new and
        updated records by comparing SHA1 hashes against the cache (if included), where:
        - if the SHA1 matches, the record is unchanged and skipped
        - if the SHA1 does not match, the record is classed as an update
        - if where a SHA1 is not found, the record is classed as a new record

        Where a commit is generated, file identifiers are returned for new and/or updated records, and statistics on
        the number of underlying files changed (where each record is stored as a JSON and XML file).
        """
        actions: list[dict] = []
        changes: dict[str, list[str]] = {"update": [], "create": []}
        data = {
            "branch": self._branch,
            "commit_message": f"{title}\n{message}",
            "author_name": author[0],
            "author_email": author[1],
            "actions": actions,
        }

        existing_hashes = self._cache.get_hashes(file_identifiers=[record.file_identifier for record in records])
        for record in records:
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
                        "content": record.dumps_json(),
                    },
                    {
                        "action": action,
                        "file_path": self._get_remote_hashed_path(f"{record.file_identifier}.xml"),
                        "content": record.dumps_xml(),
                    },
                ]
            )
        results = CommitResults(commit=None, changes=changes, actions=data["actions"])

        if not data["actions"]:
            self._logger.info("No actions to perform, aborting.")
            return results

        self._logger.info(f"Committing {results.stats.new_msg}, {results.stats.updated_msg}.")
        commit = self._project.commits.create(data)
        results.commit = commit.id
        return results

    def populate(self) -> None:
        """
        Load records from local cache into the local subset.

        Existing records are preserved. Call `purge()` to clear before this method to reset the subset.
        """
        self._records = {**self._records, **{record.file_identifier: record for record in self._cache.get()}}

    def purge(self) -> None:
        """
        Clear in-memory records.

        Note this does not purge the underlying local cache.
        """
        self._records = {}

    def get(self, file_identifier: str) -> RecordRevision:
        """
        Get record by file identifier.

        Raises RecordNotFoundError exception if not found.
        """
        try:
            return self._records[file_identifier]
        except KeyError:
            raise RecordNotFoundError(file_identifier) from None

    def push(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> CommitResults:
        """
        Add or update records in remote GitLab project repo.

        Requires a local cache to determine if records are additions or updates.

        Refreshes the local cache if needed so new/changed records are included.

        Returns commit results including resulting commit for further optional processing.
        """
        empty_results = CommitResults(commit=None, changes={"create": [], "update": []}, actions=[])
        if len(records) == 0:
            self._logger.info("No records to push, skipping.")
            return empty_results

        results = self._commit(records=records, title=title, message=message, author=author)

        if results.commit is None:
            self._logger.info("No records pushed, skipping cache invalidation.")
            return empty_results

        self._logger.info(f"Push successful as commit '{results.commit}'.")

        # calling `.populate()` will call `._cache.get()` which will refresh the cache
        self._logger.info("Refreshing cache and reloading records into store to reflect pushed changes.")
        self.populate()

        return results
