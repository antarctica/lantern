import json
import logging
import pickle
import shutil
from base64 import b64decode
from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from gitlab import Gitlab
from gitlab.v4.objects import Project
from joblib import Parallel, delayed
from requests.exceptions import ConnectionError as RequestsConnectionError
from sqlorm import SQL, Engine

from lantern.log import init as init_logging
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, RecordsNotFoundError, StoreFrozenError
from lantern.stores.gitlab import CommitResults, GitLabSource, GitLabStore, ProcessedRecord


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


class CacheFrozenError(Exception):
    """Raised when attempting to refresh/update a frozen cache."""

    pass


@dataclass
class RawRecord:
    """Raw record data from GitLab API."""

    config_str: str
    commit_id: str


class CachedProcessedRecord(ProcessedRecord):
    """Represents a record in raw, model and pickled forms with eager processing."""

    def __init__(self, logger: logging.Logger | None, config_str: str, commit_id: str) -> None:
        super().__init__(logger, config_str, commit_id)
        self._pickled = pickle.dumps(self.record, pickle.HIGHEST_PROTOCOL)

    @property
    def pickled(self) -> bytes:
        """Pre-pickled RecordRevision."""
        return self._pickled


def _process_record(logger: logging.Logger, log_level: int, record_data: RawRecord) -> CachedProcessedRecord:
    """
    Create and pickle a record from a record configuration and revision identifier.

    Standalone function for use in parallel processing.
    """
    init_logging(log_level)
    return CachedProcessedRecord(logger=logger, config_str=record_data.config_str, commit_id=record_data.commit_id)


def _fetch_record_commit(project: Project, path: str, ref: str) -> RawRecord:
    """
    Get a record configuration and the ID of its head commit from the GitLab project's repository.

    Standalone function for use in parallel processing.
    """
    file_contents = project.files.get(file_path=path, ref=ref)
    return RawRecord(
        config_str=b64decode(file_contents.content).decode("utf-8"), commit_id=file_contents.last_commit_id
    )


class GitLabLocalCache:
    """
    Cache of records from a GitLab project repository using a SQLite backing database and in-memory 'flash' layer.

    Stores:
    - record configurations as pre-pickled RecordRevision objects (for efficiency)
    - the last known commit for each record (the head commit for each record file when cached)
    - the SHA1 hash for each record (for refreshing the cache)
    - the configured GitLab instance, project ID, branch/ref and head commit from the last cache refresh

    The cache is automatically populated and/or refreshed when records are accessed using `get()`. The cache can be
    manually invalidated using `purge()` - which will trigger cache recreation on the next `get()` call.

    Unpickled records are added to an additional, in-memory, 'flash' caching layer when loaded from the backing database.
    This layer is cleared whenever the cache is modified (e.g. during an update) and specific to each cache instance.

    If needed, and once populated, the cache can be used:
    - in a basic offline mode, possibly leading to stale records (for resilience during network issues)
    - in a 'frozen' mode, where staleness checks are skipped (for efficient access to a fixed state during exports)

    Parallel processing is optionally available to improve the performance of:
    - fetching record configurations from GitLab
    - processing and pre-pickling record instances
    """

    def __init__(
        self,
        logger: logging.Logger,
        parallel_jobs: int,
        path: Path,
        gitlab_client: Gitlab,
        gitlab_token: str,
        gitlab_source: GitLabSource,
        frozen: bool = False,
    ) -> None:
        """Initialize cache."""
        self._logger = logger
        self._parallel_jobs = parallel_jobs
        self._path = path
        self._client = gitlab_client
        self._token = gitlab_token
        self._source_ = gitlab_source
        self._frozen = frozen

        self._cache_path = path / "cache.db"
        self._flash: dict[str, RecordRevision] = {}

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
        return self._client.projects.get(self._source.project)

    @property
    def _head_commit(self) -> str:
        """ID of the latest commit in the source GitLab project repository."""
        if self._frozen:
            msg = "Cannot get remote head commit of a frozen cache."
            raise CacheFrozenError(msg) from None
        return self._project.commits.list(ref_name=self._source.ref, get_all=False)[0].id

    @property
    def cached_head_commit(self) -> str:
        """ID of the latest commit known to the local cache."""
        if not self.exists:
            msg = "Head commit unavailable, cache not initialised."
            raise CacheNotInitialisedError(msg) from None
        with self._engine as tx:
            return tx.fetchscalar("SELECT value FROM meta WHERE key = 'head_commit'")

    @property
    def _source(self) -> GitLabSource:
        """
        Remote repository information, not including head commit.

        For checking whether cache is applicable to the current/future configuration.
        """
        return self._source_

    @property
    def _cached_source(self) -> GitLabSource:
        """
        Cached remote repository information.

        For checking whether cache is applicable to the current/future configuration.
        """
        if not self.exists:
            msg = 'Source unavailable, cache not initialised."'
            raise CacheNotInitialisedError(msg) from None
        with self._engine as tx:
            results = tx.fetchscalars(
                "SELECT value FROM meta WHERE key in ('source_endpoint', 'source_project', 'source_ref') ORDER BY key;"
            )
        if len(results) != 3:
            msg = 'Source incomplete, cache not initialised."'
            raise CacheNotInitialisedError(msg) from None
        return GitLabSource(endpoint=results[0], project=results[1], ref=results[2])

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

        Where the cache is frozen, the cache is always considered current.
        Where the cache does not exist, or a head commit ID isn't available, the cache is considered stale.
        """
        try:
            cached_head = self.cached_head_commit
        except CacheNotInitialisedError:
            return False
        try:
            head = self._head_commit
        except CacheFrozenError:
            self._logger.debug("Frozen cache, ignoring current state")
            return True

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
    def _record_upsert(record: CachedProcessedRecord) -> SQL:
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

    def _build_cache(self, records: list[RawRecord], head_commit_id: str) -> None:
        """
        Persist a set of records and metadata to the cache.

        Steps:
        - setting up required database structure
        - pre-processing records (as record configurations, (pickled) record instance and SHA1 hashes)
        - upserting processed records and source metadata in the backing database (in a single transaction)
        """
        self._ensure_db()

        self._logger.info(f"Processing {len(records)} records")
        results: list[CachedProcessedRecord] = Parallel(n_jobs=self._parallel_jobs)(
            delayed(_process_record)(self._logger, self._logger.level, record_data) for record_data in records
        )

        with self._engine as tx:
            self._logger.info("Storing records")
            for record in results:
                tx.execute(self._record_upsert(record))
            self._logger.info(f"Stored {len(records)} records")
            self._logger.info("Storing source and head commit metadata")
            tx.execute(self._meta_upsert(key="source_endpoint", value=self._source.endpoint))
            tx.execute(self._meta_upsert(key="source_project", value=self._source.project))
            tx.execute(self._meta_upsert(key="source_ref", value=self._source.ref))
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

        for item in self._project.repository_tree(path="records", ref=self._source.ref, recursive=True, iterator=True):
            if item["type"] != "blob" or not item["path"].endswith(".json"):
                continue
            paths.append(item["path"])

        self._logger.info(f"Fetching {len(paths)} records")
        project_ = deepcopy(self._project)  # copy to allow use in parallel processing
        return Parallel(n_jobs=self._parallel_jobs)(
            delayed(_fetch_record_commit)(project_, path, self._source.ref) for path in paths
        )

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
            delayed(_fetch_record_commit)(project_, path, self._source.ref) for path in paths
        )

    def _create_refresh(self, records: list[RawRecord]) -> None:
        """Common tasks for creating or refreshing the cache."""
        self._logger.info("Fetching head commit")
        head_commit = self._project.commits.get(self._head_commit).attributes

        self._logger.info("Populating local cache")
        self._build_cache(records=records, head_commit_id=head_commit["id"])

        self._logger.info("Clearing flash")
        self._flash.clear()

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

    def _ensure_exists(self) -> None:  # noqa: C901
        """
        Ensure cache exists and is up-to-date.

        An existing, up-to-date, cache is not modified.
        """
        if not self._online and not self.exists:
            msg = "Local cache and GitLab unavailable. Cannot load records."
            raise RemoteStoreUnavailableError(msg) from None

        if self._online and not self.exists:
            if self._frozen:
                msg = "Local cache unavailable and is frozen. Cannot load records."
                raise CacheFrozenError(msg) from None
            self._logger.info("Local cache not ready, creating from GitLab")
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
                if self._frozen:
                    msg = f"Cached source '{self._cached_source}' does not match current instance and branch '{self._source}' but is frozen. Will not load records."
                    raise CacheFrozenError(msg) from None
                self._logger.warning(
                    f"Cached source '{self._cached_source}' does not match current instance and branch '{self._source}', recreating cache"
                )
                self._create()
                return
        except CacheNotInitialisedError:
            if self._frozen:
                msg = "Local cache not setup and is frozen. Cannot load records."
                raise CacheFrozenError(msg) from None
            self._logger.info("Local cache not setup, recreating from GitLab")
            self._create()
            return

        if self._frozen:
            self._logger.debug("Cache exists and is frozen")
            return

        if self._online and not self._current:
            self._logger.warning("Cached records are not up to date, updating from GitLab")
            self._refresh()
            return

        self._logger.info("Records cache exists and is current, no changes needed")

    def get(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """
        Load all or selected cached records.

        Returns a list of RecordRevision instances where they exist in the cache (i.e. unknown records are omitted).
        """
        self._ensure_exists()  # cache entrypoint and possibly initial interaction

        if (
            file_identifiers is not None
            and len(file_identifiers) > 0
            and all(fid in self._flash for fid in file_identifiers)
        ):
            self._logger.info(f"Loading {len(file_identifiers)} records from flash")
            return [self._flash[fid] for fid in file_identifiers]

        query = SQL("SELECT record_pickled FROM record")
        params = ()
        if file_identifiers:
            query += SQL(f"WHERE file_identifier IN ({('?,' * len(file_identifiers))[:-1]})")
            params = tuple(file_identifiers)
        with self._engine as tx:
            pickled_records = tx.fetchscalars(query, params)

        self._logger.info(f"Loading {len(pickled_records)} pickled records from cache")
        records = [pickle.loads(record) for record in pickled_records]  # noqa: S301
        self._flash.update({record.file_identifier: record for record in records})
        return records

    def get_hashes(self, file_identifiers: set[str]) -> dict[str, str | None]:
        """
        Get SHA1 hashes for selected cached records.

        For determining records that have changed when refreshing the cache.

        Returns a mapping of file identifiers to SHA1 hashes, or `None` if a record isn't in the cache.
        """
        self._ensure_exists()  # cache entrypoint and possibly initial interaction

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


class GitLabCachedStore(GitLabStore):
    """
    GitLab store accessed through a local SQLite based cache for performance and offline support.

    Supports freezing.

    The local cache is refreshed on record access or update. It can be fully reset if needed using `purge()`.

    The contents of the given `cache_dir` directory MUST be assumed to be exclusively managed by this class.
    """

    def __init__(
        self,
        logger: logging.Logger,
        source: GitLabSource,
        access_token: str,
        parallel_jobs: int,
        cache_dir: Path,
        frozen: bool = False,
    ) -> None:
        super().__init__(logger=logger, source=source, access_token=access_token, frozen=False)
        self._frozen = frozen

        self._cache = GitLabLocalCache(
            logger=self._logger,
            parallel_jobs=parallel_jobs,
            path=cache_dir,
            gitlab_client=self._client,
            gitlab_token=self._access_token,
            gitlab_source=source,
            frozen=self._frozen,
        )
        self._get_hashes_callable = self._cache.get_hashes

    @property
    def frozen(self) -> bool:
        """Whether store can be modified/updated."""
        return self._frozen

    @cached_property
    def _project(self) -> Project:
        """
        GitLab project.

        Cached as cache is tied to a single project.
        """
        return super()._project

    @property
    def head_commit(self) -> str | None:
        """Cached head commit reference, if available."""
        return self._cache.cached_head_commit if self._cache.exists else None

    def select(self, file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """
        Get some or all records filtered by file identifier.

        Raises a `RecordsNotFoundError` exception if any selected records aren't found (i.e. all or nothing).
        """
        results = self._cache.get(file_identifiers=file_identifiers)
        if not file_identifiers or len(results) == len(file_identifiers):
            return results

        missing_fids = file_identifiers - {record.file_identifier for record in results}
        raise RecordsNotFoundError(missing_fids) from None

    def select_one(self, file_identifier: str) -> RecordRevision:
        """
        Get specific record by file identifier.

        Raises a `RecordNotFoundError` exception if not found.
        """
        try:
            return self.select(file_identifiers={file_identifier})[0]
        except RecordsNotFoundError as e:
            raise RecordNotFoundError(file_identifier) from e

    def _ensure_branch(self, branch: str) -> None:
        if self._frozen:
            msg = f"Branch '{branch}' does not exist and store is frozen. Cannot create."
            raise StoreFrozenError(msg) from None
        super()._ensure_branch(branch)

    def push(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> CommitResults:
        """
        Add or update records in the GitLab repository.

        Requires a local cache to determine if records are additions or updates.

        Refreshes the local cache if needed so new/changed records are included.

        Returns commit results including resulting commit for further optional processing.
        """
        if self._frozen:
            msg = "Store is frozen. Cannot push records."
            raise StoreFrozenError(msg) from None

        results = super().push(records, title, message, author)
        if results.commit:
            self._cache._ensure_exists()
        return results

    def purge(self) -> None:
        """Clear underlying cache."""
        if self._frozen:
            msg = "Store is frozen. Cannot purge cache."
            raise StoreFrozenError(msg) from None
        self._cache.purge()
