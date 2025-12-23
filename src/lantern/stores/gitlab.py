from __future__ import annotations

import json
import logging
import pickle
import shutil
from base64 import b64decode
from copy import deepcopy
from functools import cached_property
from pathlib import Path
from typing import NamedTuple, TypedDict
from urllib.parse import urlparse

from gitlab import Gitlab, GitlabGetError
from gitlab.v4.objects import Project
from joblib import Parallel, delayed
from requests.exceptions import ConnectionError as RequestsConnectionError
from sqlorm import SQL, Engine

from lantern.log import init as init_logging
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.shim import inject_truststore_into_ssl_boto_fix
from lantern.stores.base import RecordNotFoundError, Store


class RemoteStoreUnavailableError(Exception):
    """Raised when records cannot be loaded from the remote store."""

    pass


class CacheIntegrityError(Exception):
    """Raised when the local cache integrity cannot be guaranteed."""

    pass


class CacheNotInitialisedError(Exception):
    """Raised when the local cache has not been initialised yet."""

    pass


class CacheTooOutdatedError(Exception):
    """Raised when the local cache is too out-of-date to make sense refreshing."""

    pass


class RawRecord(NamedTuple):
    """Raw record data from GitLab API."""

    config_str: str
    commit_id: str


class ProcessedRecord:
    """
    Represents a metadata record in raw and processed forms.

    Available representations:
    - record revision configuration dict
    - RecordRevision instance
    - pickled RecordRevision
    """

    def __init__(self, logger: logging.Logger | None, config_str: str, commit_id: str) -> None:
        self._config = {"file_revision": commit_id, **json.loads(config_str)}
        self._record = RecordRevision.loads(value=self.config, check_supported=True, logger=logger)
        self._pickled = pickle.dumps(self.record, pickle.HIGHEST_PROTOCOL)

    @property
    def config(self) -> dict:
        """Record revision config dict."""
        return self._config

    @property
    def record(self) -> RecordRevision:
        """RecordRevision instance."""
        return self._record

    @property
    def pickled(self) -> bytes:
        """Pre-pickled RecordRevision."""
        return self._pickled


class Source(TypedDict):
    """
    Elements of a cache source.

    As currently configured or stored in the cache.
    """

    ref: str
    project: str
    instance: str


def _process_record(logger: logging.Logger, log_level: int, record_data: RawRecord) -> ProcessedRecord:
    """
    Create and pickle a record from a record configuration and revision identifier.

    Standalone function for use in parallel processing.
    """
    init_logging(log_level)
    return ProcessedRecord(logger=logger, config_str=record_data.config_str, commit_id=record_data.commit_id)


def _fetch_record_commit(project: Project, path: str, ref: str) -> RawRecord:
    """
    Get a record configuration and the ID of its head commit from the GitLab project's repository.

    A truststore inject is used to allow the use of local development GitLab instances.

    Standalone function for use in parallel processing.
    """
    inject_truststore_into_ssl_boto_fix()
    file_contents = project.files.get(file_path=path, ref=ref)
    return RawRecord(
        config_str=b64decode(file_contents.content).decode("utf-8"), commit_id=file_contents.last_commit_id
    )


class GitLabLocalCache:
    """
    Cache of records from a GitLab project repository using a SQLite backing database.

    Stores:
    - record configurations as pre-pickled RecordRevision objects (for efficiency)
    - the last known commit for each record (the head commit for each record file when cached)
    - the SHA1 hash for each record (for refreshing the cache)
    - the configured GitLab instance, project ID, branch/ref and head commit from the last cache refresh

    The cache is automatically populated and/or refreshed when records are accessed using `get()`. The cache can be
    manually invalidated using `purge()` - which will trigger cache recreation on the next `get()` call.

    If needed, and once populated, the cache can be used in a basic offline mode - which may led to stale records.

    Parallel processing is optionally available to improve the performance of:
    - fetching record configurations from GitLab
    - processing and pre-pickling record instances
    """

    def __init__(
        self,
        logger: logging.Logger,
        parallel_jobs: int,
        path: Path,
        project_id: str,
        ref: str,
        gitlab_token: str,
        gitlab_client: Gitlab,
    ) -> None:
        """Initialize cache."""
        self._logger = logger
        self._parallel_jobs = parallel_jobs
        self._path = path
        self._project_id = project_id
        self._token = gitlab_token
        self._ref = ref
        self._client = gitlab_client
        self._cache_path = path / "cache.db"

    @cached_property
    def _engine(self) -> Engine:
        """Engine for backing database."""
        self._logger.info(f"Connecting to SQLite database at: '{self._cache_path.resolve()}'")
        return Engine.from_uri(f"sqlite://{self._cache_path.resolve()}")

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
    def _instance(self) -> str:
        """GitLab instance."""
        return urlparse(self._project.http_url_to_repo).hostname

    @property
    def _head_commit(self) -> str:
        """ID of the latest commit in the source GitLab project repository."""
        return self._project.commits.list(ref_name=self._ref, get_all=False)[0].id

    @property
    def cached_head_commit(self) -> str:
        """ID of the latest commit known to the local cache."""
        if not self.exists:
            msg = "Head commit unavailable, cache not initialised."
            raise CacheNotInitialisedError(msg) from None
        with self._engine as tx:
            return tx.fetchscalar("SELECT value FROM meta WHERE key = 'head_commit'")

    @property
    def _source(self) -> Source:
        """
        Remote repository information, not including head commit.

        For checking whether cache is applicable to the current/future configuration.
        """
        return Source(ref=self._ref, project=self._project_id, instance=self._instance)

    @property
    def _cached_source(self) -> Source:
        """
        Cached remote repository information.

        For checking whether cache is applicable to the current/future configuration.
        """
        if not self.exists:
            msg = 'Source unavailable, cache not initialised."'
            raise CacheNotInitialisedError(msg) from None
        with self._engine as tx:
            results = tx.fetchscalars(
                "SELECT value FROM meta WHERE key in ('source_instance', 'source_project', 'source_ref') ORDER BY key;"
            )
        if len(results) != 3:
            msg = 'Source incomplete, cache not initialised."'
            raise CacheNotInitialisedError(msg) from None
        return Source(ref=results[2], project=results[1], instance=results[0])

    @property
    def exists(self) -> bool:
        """Determine if the cache exists."""
        if not self._cache_path.exists():
            return False
        with self._engine as tx:
            result = tx.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='record';")
            if result is None:
                return False
        return True

    @property
    def _applicable(self) -> bool:
        """Ensure cache is applicable to the current GitLab instance and branch/ref."""
        try:
            cached_source = self._cached_source
        except CacheNotInitialisedError:
            return False

        current_source = self._source
        self._logger.debug(f"Cached: '{cached_source}' ?= Current: '{current_source}'")
        return cached_source == current_source

    @property
    def _current(self) -> bool:
        """
        Determine if cache is current or stale compared to the remote project repo.

        Where the cache does not exist, or a head commit ID isn't available, the cache is considered stale.
        """
        try:
            cached_head = self.cached_head_commit
        except CacheNotInitialisedError:
            return False

        head = self._head_commit
        self._logger.debug(f"Cached {cached_head} ?= Current: {head}")
        return cached_head == head

    @staticmethod
    def _init_db(engine: Engine) -> None:
        """
        Initialise backing database with required structure.

        Simplistic implementation which does not support structure alterations once initialised.
        Static method for cherry-picking in tests.
        """
        with engine as tx:
            tx.execute(
                """
                -- noinspection SqlSignature @ routine/"jsonb_extract"
                CREATE TABLE IF NOT EXISTS record
                (
                    record_pickled  BLOB NOT NULL,
                    record_jsonb    BLOB NOT NULL,
                    sha1            TEXT PRIMARY KEY,
                    file_identifier TEXT GENERATED ALWAYS AS (jsonb_extract(record_jsonb, '$.file_identifier')) STORED UNIQUE,
                    file_revision   TEXT GENERATED ALWAYS AS (jsonb_extract(record_jsonb, '$.file_revision')) STORED
                );
                """
            )
            tx.execute(
                """
                CREATE TABLE IF NOT EXISTS meta
               (
                    key    TEXT PRIMARY KEY
                   ,value  TEXT NOT NULL
               );
                """
            )

    @staticmethod
    def _record_upsert(record: ProcessedRecord) -> SQL:
        """Generates SQL for upserting a record."""
        insert = SQL.insert(
            table="record",
            values={
                "record_pickled": record.pickled,
                "record_jsonb": SQL.funcs.jsonb(json.dumps(record.config)),  # ty:ignore[unresolved-attribute]
                "sha1": record.record.sha1,
            },
        )
        upsert = SQL(
            """
            ON CONFLICT(file_identifier)
            DO UPDATE
            SET
                 record_pickled = excluded.record_pickled
                ,record_jsonb   = excluded.record_jsonb
                ,sha1           = excluded.sha1
            """
        )
        return insert + upsert

    @staticmethod
    def _meta_upsert(key: str, value: str) -> SQL:
        """Generates SQL for upserting a meta key-value."""
        insert = SQL.insert(table="meta", values={"key": key, "value": value})
        upsert = SQL("ON CONFLICT(key) DO UPDATE SET value = excluded.value")
        return insert + upsert

    def _ensure_db(self) -> None:
        """Ensure backing database exists."""
        self._logger.info("Ensuring DB path")
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

        self._logger.info("Ensuring DB structure")
        self._init_db(engine=self._engine)

    def _build_cache(self, records: list[RawRecord], source: Source, head_commit_id: str) -> None:
        """
        Persist a set of records and metadata to the cache.

        Steps:
        - setting up required database structure
        - pre-processing records (as record configurations, (pickled) record instance and SHA1 hashes)
        - upserting processed records and source metadata in the backing database (in a single transaction)
        """
        self._ensure_db()

        self._logger.info(f"Processing {len(records)} records")
        results: list[ProcessedRecord] = Parallel(n_jobs=self._parallel_jobs)(
            delayed(_process_record)(self._logger, self._logger.level, record_data) for record_data in records
        )

        with self._engine as tx:
            self._logger.info("Storing records")
            for record in results:
                tx.execute(self._record_upsert(record))
            self._logger.info(f"Stored {len(records)} records")
            self._logger.info("Storing source and head commit metadata")
            for key, value in source.items():
                tx.execute(self._meta_upsert(key=f"source_{key}", value=value))  # ty:ignore[invalid-argument-type]
            tx.execute(self._meta_upsert(key="head_commit", value=head_commit_id))
            self._logger.info("Stored cache metadata")

    def _fetch_record_commits(self) -> list[RawRecord]:
        """
        Get all record configurations and their head commit IDs from the GitLab project repository.

        Returns a list of tuples ('record configuration as JSON string', 'record commit string').

        This method will fail with a '404 Tree Not Found' error where the requested branch/ref does not exist.

        This method is annoyingly inefficient as a separate HTTP request is needed per-file to get the commit ID.
        This method won't scale to large numbers of records due to returning all record configurations in memory.
        """
        paths = []

        for item in self._project.repository_tree(path="records", ref=self._ref, recursive=True, iterator=True):
            if item["type"] != "blob" or not item["path"].endswith(".json"):
                continue
            paths.append(item["path"])

        self._logger.info(f"Fetching {len(paths)} records")
        project_ = deepcopy(self._project)  # copy to allow use in parallel processing
        return Parallel(n_jobs=self._parallel_jobs)(
            delayed(_fetch_record_commit)(project_, path, self._ref) for path in paths
        )
        # results are list of RawRecord tuples

    def _fetch_latest_records(self) -> list[RawRecord]:
        """
        Get record configurations and their latest commit IDs from the GitLab project repository from after a commit.

        Steps:
        - check branch/ref has not changed since last cache update
        - get a list of commits since the cache was last updated
        - raise a `CacheTooOutdated` exception if the number of commits is too high (as recreating the cache would be faster)
        - get a list of files changed across any subsequent commits
        - get the contents and head commit ID for any changed files

        Returns a list of tuples ('record configuration as JSON string', 'record commit string').

        This method is inefficient as each file within each commit needs separate HTTP requests,
        however where a record has been updated multiple times, only the latest version is fetched.

        Past a given (and arbitrary) number of commits, updating is aborted as it's faster to recreate the cache.
        """
        limit = 50
        paths = []

        commit_range = f"{self.cached_head_commit}..{self._head_commit}"
        commits = self._project.commits.list(ref_name=commit_range, all=True)

        if len(commits) > limit:
            raise CacheTooOutdatedError() from None

        self._logger.info(f"Fetching commits in range {commit_range}")
        for commit in commits:
            for diff in commit.diff(get_all=True):
                if not diff["new_path"].startswith("records/") or not diff["new_path"].endswith(".json"):
                    continue
                if diff["renamed_file"]:
                    msg = "Renamed file in remote store, skipping. Partial updates do not support renamed files, use purge and recreate to ensure cache integrity."
                    raise CacheIntegrityError(msg)
                if diff["deleted_file"]:
                    msg = "Deleted file in remote store, skipping. Partial updates do not support deleted files, use purge and recreate to ensure cache integrity."
                    raise CacheIntegrityError(msg)
                paths.append(diff["new_path"])
        paths = set(paths)

        self._logger.info(f"Fetching {len(paths)} changed records")
        project_ = deepcopy(self._project)
        return Parallel(n_jobs=self._parallel_jobs)(
            delayed(_fetch_record_commit)(project_, path, self._ref) for path in paths
        )
        # results are a list of RawRecord tuples

    def _create_refresh(self, records: list[RawRecord]) -> None:
        """Common tasks for creating or refreshing the cache."""
        self._logger.info("Fetching head commit")
        head_commit = self._project.commits.get(self._head_commit).attributes

        self._logger.info("Populating local cache")
        source = Source(ref=self._ref, project=self._project_id, instance=self._instance)
        self._build_cache(records=records, source=source, head_commit_id=head_commit["id"])

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
        self._logger.info("Fetching changed records (this may take some time)")
        try:
            records = self._fetch_latest_records()
        except CacheIntegrityError:
            self._logger.warning("Cannot refresh cache due to integrity issues, recreating entire cache instead")
            self._create()
            return
        except CacheTooOutdatedError:
            self._logger.warning("Refreshing the cache would take too long, recreating entire cache instead")
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
            self._logger.info("Local cache unavailable, creating from GitLab")
            self._create()
            return

        if not self._online:
            if not self._applicable:
                msg = "Local cache source does not match remote and cannot access GitLab to recreate."
                raise RemoteStoreUnavailableError(msg) from None
            self._logger.warning("Cannot check if records cache is current, loading possibly stale records")
            return

        try:
            if not self._applicable:
                self._logger.warning(
                    f"Cached source '{self._cached_source}' does not match current instance and branch '{self._source}', recreating cache"
                )
                self._create()
                return
        except CacheNotInitialisedError:
            self._logger.info("Local cache source unavailable, recreating from GitLab")
            self._create()
            return

        if self._online and not self._current:
            self._logger.warning("Cached records are not up to date, updating from GitLab")
            self._refresh()
            return

        self._logger.info("Records cache exists and is current, no changes needed")

    def get(self) -> list[RecordRevision]:
        """Load all cached records."""
        self._ensure_exists()
        with self._engine as tx:
            records = tx.fetchscalars("SELECT record_pickled FROM record")

        self._logger.info(f"Loading {len(records)} records from cache")
        return [pickle.loads(record) for record in records]  # noqa: S301

    def get_hashes(self, file_identifiers: set[str]) -> dict[str, str | None]:
        """
        Get SHA1 hashes for a set of records.

        For determining records that have changed when refreshing the cache.

        Returns a mapping of file identifiers to SHA1 hashes, or `None` if a record isn't in the cache.
        """
        with self._engine as tx:
            results = tx.fetchall(
                f"""
                SELECT file_identifier, sha1
                FROM record
                WHERE file_identifier IN ({("?," * len(file_identifiers))[:-1]});
                """,  # noqa: S608
                tuple(file_identifiers),
            )
        hashes = {result["file_identifier"]: result["sha1"] for result in results}
        return {file_id: hashes.get(file_id) for file_id in file_identifiers}

    def purge(self) -> None:
        """Clear cache contents."""
        if self._path.exists():
            self._logger.info("Purging cache")
            shutil.rmtree(self._path)


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

    def __eq__(self, other: CommitResults | object) -> bool:
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


class GitLabStore(Store):
    """
    Basic read-write store backed by a remote GitLab project.

    Uses:
    - `GitLabLocalCache` class to cache records from the remote repository for efficiency and offline support
    - https://python-gitlab.readthedocs.io/ to interact with the GitLab API, rather than use the generic Git protocol

    The store is initially empty, with records loaded from the local cache using `populate()`. This can be called
    multiple times to append additional records, or emptied using `purge()` (this does not clear the underlying cache).

    Records can be added or updated using `push()`, which commits changes to the remote GitLab project repository.

    A truststore inject is used to allow the use of local development GitLab instances.
    """

    def __init__(
        self,
        logger: logging.Logger,
        parallel_jobs: int,
        endpoint: str,
        access_token: str,
        project_id: str,
        branch: str,
        cache_path: Path,
    ) -> None:
        self._logger = logger
        self._records: dict[str, RecordRevision] = {}
        self._project_id = project_id
        self._branch = branch
        self._cache_path = cache_path
        self._access_token = access_token

        inject_truststore_into_ssl_boto_fix()
        self._client = Gitlab(url=endpoint, private_token=self._access_token)

        self._cache = GitLabLocalCache(
            logger=self._logger,
            parallel_jobs=parallel_jobs,
            path=self._cache_path,
            gitlab_client=self._client,
            project_id=self._project_id,
            gitlab_token=self._access_token,
            ref=self._branch,
        )

    @cached_property
    def project(self) -> Project:
        """
        GitLab project.

        Cached for lifetime of instance as caches are implicitly tied to a single project.
        """
        return self._client.projects.get(self._project_id)

    @property
    def branch(self) -> str:
        """Selected branch."""
        return self._branch

    @property
    def records(self) -> list[RecordRevision]:
        """Loaded Records."""
        return list(self._records.values())

    @property
    def head_commit(self) -> str | None:
        """Local head commit reference if available."""
        return self._cache.cached_head_commit if self._cache.exists else None

    @staticmethod
    def _get_remote_hashed_path(file_name: str) -> str:
        """
        Get the hashed storage path for a file name.

        A hashed path is used to avoid too many files being in a single directory.

        For `_get_hashed_path(file_name="0be5339c-9d35-44c9-a10f-da4b5356840b.json")`
        return: 'records/0b/e5/0b5339c-9d35-44c9-a10f-da4b5356840b.json'
        """
        return f"records/{file_name[:2]}/{file_name[2:4]}/{file_name}"

    def _ensure_branch(self, branch: str) -> None:
        """
        Ensure branch exists in remote project.

        New branches are always created from `main`.
        """
        try:
            _ = self.project.branches.get(branch)
        except GitlabGetError:
            self._logger.info(f"Branch '{branch}' does not exist, creating")
            self.project.branches.create({"branch": branch, "ref": "main"})

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
        changes: dict[str, list[str]] = {"update": [], "create": []}
        data: CommitData = {
            "branch": self._branch,
            "commit_message": f"{title}\n{message}",
            "author_name": author[0],
            "author_email": author[1],
            "actions": [],
        }

        existing_hashes = self._cache.get_hashes(file_identifiers={record.file_identifier for record in records})
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
        results = CommitResults(branch=self._branch, commit=None, changes=changes, actions=data["actions"])

        if not data["actions"]:
            self._logger.info("No actions to perform, aborting")
            return results

        self._logger.debug(f"Ensuring target branch {self._branch} exists")
        self._ensure_branch(branch=self._branch)

        self._logger.info(f"Committing {results.stats.new_msg}, {results.stats.updated_msg}")
        # noinspection PyTypeChecker
        commit = self.project.commits.create(data)
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
        empty_results = CommitResults(
            branch=self._branch, commit=None, changes={"create": [], "update": []}, actions=[]
        )
        if len(records) == 0:
            self._logger.info("No records to push, skipping")
            return empty_results

        results = self._commit(records=records, title=title, message=message, author=author)

        if results.commit is None:
            self._logger.info("No records pushed, skipping cache invalidation")
            return empty_results

        self._logger.info(f"Push successful as commit '{results.commit}'")

        # calling `.populate()` will call `._cache.get()` which will refresh the cache
        self._logger.info("Refreshing cache and reloading records into store to reflect pushed changes")
        self.populate()

        return results
