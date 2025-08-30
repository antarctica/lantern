from __future__ import annotations

import json
import logging
import pickle
import shutil
import tarfile
from functools import cached_property
from pathlib import Path
from tempfile import TemporaryDirectory

from gitlab import Gitlab
from gitlab.v4.objects import Project
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.models.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.stores.base import RecordNotFoundError, Store


class RemoteStoreUnavailableError(Exception):
    """Raised when records cannot be loaded from the remote store."""

    pass


class GitLabLocalCache:
    """
    A simple file based cache for records held in a GitLab project repository.

    Intended for efficiency and basic offline support.

    Loads record configuration files from a GitLab project repository and processes them into:
    - record configurations (stored as JSON files)
    - RecordRevision objects (stored as Python pickle files for efficiency)
    - a mapping of record file identifiers to their latest commits
    - a mapping of record file identifiers to their SHA1 hashes

    The cache will automatically be populated or refreshed when records are accessed using `get()`. To manually
    invalidate the cache, call `purge()`, which will trigger a recreation of the cache on the next request for records.

    Once populated, the cache can be used in a basic offline mode, which may led to stale records being returned,
    indicated via a warning log message.

    Basic cache-validation is performed by comparing the head commit from when the cache was last refreshed, against
    the head commit in the remote project repository.
    """

    def __init__(self, logger: logging.Logger, path: Path, project_id: str, gitlab_client: Gitlab) -> None:
        """Initialize cache."""
        self._logger = logger
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
    def _head_commit_id(self) -> str:
        """
        ID of the head commit in remote project.

        Not valid if called before `_create()` is called where cache does not exist.
        """
        return self._project.commits.list(get_all=False)[0].id

    @property
    def _exists(self) -> bool:
        """Determine if the cache exists."""
        return self._records_path.exists()

    @property
    def _current(self) -> bool:
        """
        Determine if cache is current or stale compared to the remote project repo.

        Where the cache does not exist, or a head commit ID isn't available, the cache is considered stale.
        """
        if not self._exists:
            return False

        with self._head_path.open() as f:
            cache_commit = json.load(f)
        return cache_commit["id"] == self._head_commit_id

    @staticmethod
    def _load_record_pickle(record_path: Path) -> RecordRevision:
        """Load record from Python pickle file."""
        with record_path.open(mode="rb") as file:
            return pickle.load(file)  # noqa: S301

    def _load_record_json(self, record_path: Path, file_revision: str) -> RecordRevision:
        """Load record revision from JSON file and file revision."""
        with record_path.open() as file:
            record_data = json.load(file)

        record_data["file_revision"] = file_revision

        return RecordRevision.loads(
            value=record_data,
            check_supported=True,
            logger=self._logger,
        )

    def _load_record(self, record_path: Path, file_revision: str | None = None) -> RecordRevision:
        """
        Load record from a file.

        JSON files require a file revision to load as a RecordRevision. Pickle files are RecordRevisions already.
        """
        self._logger.debug(f"Loading record from '{record_path.resolve()}'")
        if record_path.suffix == ".pickle":
            return self._load_record_pickle(record_path)

        return self._load_record_json(record_path, file_revision)

    def _build_cache(self, config_paths: list[Path], config_commits: dict[str, str], head_commit: dict) -> None:
        """
        Persist a set of record configuration files to the local cache.

        Where:
        - `config_paths` is a list of file paths containing record configurations
        - `config_commits` is a mapping of file identifiers to Git commit IDs
        - `head_commit` is the current head commit of the remote project repository

        Note: `config_commits` must include entries for all record configurations defined in `config_paths`.

        Steps:
        - copy each record config file to the cache directory
        - parse each record config file as a RecordRevision
        - create a mapping of each RecordRevision by file identifier and SHA1 hash of its configuration
        - save a pickled version of each RecordRevision to the cache directory
        - save details of the current head commit to a file for cache validation
        - save the mapping of file identifiers to SHA1 hashes for each record config to a file
        - save the mapping of file identifiers to Git commits for each record config to a file
        """
        self._logger.info("Populating local cache")

        hashes = {}

        records_path = self._records_path
        records_path.mkdir(parents=True, exist_ok=True)
        self._logger.info(f"Processing {len(config_paths)} record configurations")
        for config_path in config_paths:
            record_path = records_path / config_path.name
            shutil.copy2(config_path, record_path)
            commit = config_commits[config_path.stem]
            record = self._load_record(config_path, file_revision=commit)
            hashes[record.file_identifier] = record.sha1

            with record_path.with_suffix(".pickle").open(mode="wb") as f:
                # noinspection PyTypeChecker
                pickle.dump(record, f, pickle.HIGHEST_PROTOCOL)

        with self._head_path.open(mode="w") as f:
            json.dump(head_commit, f, indent=2)

        with self._hashes_path.open(mode="w") as f:
            data = {"hashes": hashes}
            json.dump(data, f, indent=2)

        with self._commits_path.open(mode="w") as f:
            data = {"commits": config_commits}
            json.dump(data, f, indent=2)

    def _fetch_file_commits(self, record_paths: list[str]) -> dict[str, str]:
        """
        Get a mapping of file identifiers and commit IDs for a set of record configuration files.

        This method is annoyingly inefficient as a separate HTTP request to the GitLab project repository is needed.
        The returned mapping should therefore be cached for efficiency.
        """
        header = "X-Gitlab-Last-Commit-Id"
        file_commits = {}

        for record_path in record_paths:
            file_identifier = Path(record_path).stem
            file_commits[file_identifier] = self._project.files.head(file_path=record_path, ref=self._ref)[header]

        return file_commits

    def _fetch_project_archive(self, workspace: Path) -> tuple[list[Path], list[str]]:
        """
        Get all record configuration files from the GitLab project repository.

        Uses the project repository archive to efficiently download all records in a single request.

        Returns a tuple of paths:
        - local paths: file system paths to each downloaded record for processing as records into the cache
        - remote paths: URL paths to each record for use with `_get_file_commits()`
        """
        export_path = workspace / "export.tgz"
        with export_path.open(mode="wb") as f:
            self._project.repository_archive(format="tgz", streamed=True, action=f.write)
        with tarfile.open(export_path, "r:gz") as tar:
            tar.extractall(path=workspace, filter="data")

        records_base_path = next(workspace.glob("**/records")).parent
        local_paths = list(workspace.glob("**/records/**/*.json"))
        remote_paths = [str(path.relative_to(records_base_path)) for path in local_paths]
        return local_paths, remote_paths

    def _create(self) -> None:
        """
        Cache records from remote store locally.

        Any existing cache is removed and recreated, regardless of whether it's up-to-date.

        For efficiency, records are fetched together using a GitLab project repo archive.
        Annoyingly, and inefficiently, Git commits for records must be fetched using individual HTTP requests.

        Steps:
        - remove existing cache directory if present
        - create cache directory
        - create a project repo archive via the GitLab API as a tar.gz archive
        - extract the contents of the archive to a temporary directory
        - query the GitLab API for the commit of each record in the archive
        - query the GitLab API for the head commit of the project repo
        - build and populate the local cache
        """
        self.purge()

        self._logger.info("Caching records from repo export")
        tmp_dir = TemporaryDirectory()
        tmp_path = Path(tmp_dir.name)

        self._logger.info("Fetching repo archive")
        config_paths, config_urls = self._fetch_project_archive(tmp_path)

        self._logger.info(f"Fetching file commits for {len(config_urls)} records (this may take some time)")
        commits_mapping = self._fetch_file_commits(config_urls)

        self._logger.info("Fetching head commit")
        head_commit = self._project.commits.get(self._head_commit_id)

        self._build_cache(config_paths=config_paths, config_commits=commits_mapping, head_commit=head_commit.attributes)
        tmp_dir.cleanup()

    def _ensure_exists(self) -> None:
        """
        Ensure cache exists and is up-to-date.

        An existing, up-to-date, cache is not modified.
        """
        if not self._online and not self._exists:
            msg = "Local cache and GitLab unavailable. Cannot load records."
            raise RemoteStoreUnavailableError(msg) from None

        if self._online and not self._exists:
            self._create()
            return

        if not self._online:
            self._logger.warning("Cannot check if records cache is current, loading possibly stale records")
            return

        if self._online and not self._current:
            self._logger.warning("Cached records are not up to date, reloading from GitLab")
            self.purge()
            self._ensure_exists()
            return

        self._logger.info("Records cache exists and is current, no changes needed.")

    def _get_record(self, file_identifier: str, raise_for_missing: bool = True) -> RecordRevision | None:
        """Load a record from the cache."""
        record_path = self._records_path / f"{file_identifier}.pickle"
        try:
            return self._load_record(record_path)
        except FileNotFoundError:
            if not raise_for_missing:
                return None
            raise RecordNotFoundError(file_identifier) from None

    def _get_except(self, file_identifiers: list[str]) -> list[RecordRevision]:
        """Load all records except specified file identifiers."""
        msg = "Loading all records from cache"
        if file_identifiers:
            msg = f"Loading all records from cache except {len(file_identifiers)} excluded"
        self._logger.info(msg)

        record_paths = []
        for record_path in self._path.glob("records/*.pickle"):
            if record_path.stem in file_identifiers:
                self._logger.debug(f"Record '{record_path.stem}' excluded, skipping")
                continue
            record_paths.append(record_path)

        return [self._load_record(record_path) for record_path in record_paths]

    def _include_records(self, file_identifiers: list[str]) -> list[str]:
        """Load records related to specified file identifiers."""
        related = set()
        for file_identifier in file_identifiers:
            try:
                record = self._get_record(file_identifier)
            except RecordNotFoundError:
                self._logger.warning(f"Record '{file_identifier}' not found in cache, skipping")
                continue

            relations = record.identification.aggregations.identifiers(exclude=[record.file_identifier])
            self._logger.info(f"Selecting {len(relations)} records related to '{file_identifier}'.")
            self._logger.debug(f"Related records: {relations}")
            related.update(relations)
        return list(related)

    def _get_only(self, file_identifiers: list[str]) -> list[RecordRevision]:
        """
        Load records only for specified file identifiers.

        Records related to selected records, and records these records relate to, will all be returned [depth=2].

        This is needed to ensure related records are available relations for resources such as collections that are
        comprised of other records, and/or physical maps, which are composites of multiple records.

        For example:
        - selected record A has aggregations to records C [a parent collection]
            - record A is included as it is selected
            - record C is included as it is related to A [depth=1]
            - records D - M are included as they are related to C [depth=2]
        - selected record X has aggregations to records Y and Z [two physical map sides]
            - record X is included as it is selected
            - records Y amd Z are included as they are related to X [depth=1]
            - records C, Q, R, S are included as they related to either Y or Z [depth=2]
        """
        direct_identifiers = self._include_records(file_identifiers)
        self._logger.info(f"Selecting {len(direct_identifiers)} directly related records [depth=1]")

        indirect_identifiers = self._include_records(direct_identifiers)
        self._logger.info(f"Selecting {len(indirect_identifiers)} indirectly related records [depth=2]")

        selected = set(file_identifiers + direct_identifiers + indirect_identifiers)
        self._logger.info(f"Loading {len(selected)} records")
        records = [self._get_record(file_identifier, raise_for_missing=False) for file_identifier in selected]
        # filter any 'None' values for originally selected records that were not found (due to `raise_for_missing=False`)
        return [record for record in records if record is not None]

    def get(self, inc_records: list[str], exc_records: list[str]) -> list[RecordRevision]:
        """
        Load some or all records.

        To select all records set `inc_records` and `exc_records` to any empty list.

        This method is a router for the filtering pathway to use.
        """
        self._ensure_exists()

        if inc_records and exc_records:
            msg = "Including and excluding records is not supported."
            raise ValueError(msg) from None

        if not inc_records:
            return self._get_except(exc_records)

        return self._get_only(inc_records)

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
            shutil.rmtree(self._path)


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
        self, logger: logging.Logger, endpoint: str, access_token: str, project_id: str, cache_path: Path
    ) -> None:
        self._logger = logger

        self._records: dict[str, RecordRevision] = {}

        self._client = Gitlab(url=endpoint, private_token=access_token)
        self._project_id = project_id
        self._branch = "main"

        self._cache_path = cache_path
        self._cache = GitLabLocalCache(
            logger=self._logger, path=self._cache_path, gitlab_client=self._client, project_id=self._project_id
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

    @staticmethod
    def _get_remote_hashed_path(file_name: str) -> str:
        """
        Get the hashed storage path for a file name.

        A hashed path is used to avoid too many files being in a single directory.

        For `_get_hashed_path(file_name="0be5339c-9d35-44c9-a10f-da4b5356840b.json")`
        return: 'records/0b/e5/0b5339c-9d35-44c9-a10f-da4b5356840b.json'
        """
        return f"records/{file_name[:2]}/{file_name[2:4]}/{file_name}"

    def _commit(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> dict[str, int]:
        """
        Generate commit for a set of records.

        Main commit structure is determined by the GitLab API which includes an `action` to distinguish between new and
        updated records by comparing SHA1 hashes against the cache (if included), where:
        - if the SHA1 matches, the record is unchanged and skipped
        - if the SHA1 does not match, the record is classed as an update
        - if where a SHA1 is not found, the record is classed as a new record

        Where a commit is generated, statistics are returned recording the number of new/updated records and underlying
        files (where each record is stored as a JSON and XML file).
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

        # *_total tracks individual files not records so cannot rely on `len(*_id)`
        stats = {
            "additions_ids": len(changes["create"]),
            "additions_total": sum(1 for action in data["actions"] if action["action"] == "create"),
            "updates_ids": len(changes["update"]),
            "updates_total": sum(1 for action in data["actions"] if action["action"] == "update"),
        }

        if not data["actions"]:
            self._logger.info("No actions to perform, skipping")
            return stats

        _additions = (
            f"{stats['additions_ids']} added records across {stats['additions_total']} new files"
            if stats["additions_ids"] >= 1
            else "0 additional records"
        )
        _updates = (
            f"{stats['updates_ids']} updated records across {stats['updates_total']} modified files"
            if stats["updates_ids"] >= 1
            else "0 updated records"
        )
        self._logger.info(f"Committing {_additions}, {_updates}")
        self._project.commits.create(data)
        return stats

    def populate(self, inc_records: list[str] | None = None, exc_records: list[str] | None = None) -> None:
        """
        Load records from local cache into the local subset, optionally filtered by file identifier.

        Existing records are preserved. Call `purge()` to clear before this method to reset the subset.
        """
        inc_records = inc_records or []
        exc_records = exc_records or []
        records = self._cache.get(inc_records=inc_records, exc_records=exc_records)
        self._records = {**self._records, **{record.file_identifier: record for record in records}}

    def purge(self) -> None:
        """
        Clear in-memory records.

        Note this does not purge the underlying local cache.
        """
        self._records = {}

    def get(self, file_identifier: str) -> RecordRevision:
        """
        Get record from local subset if possible.

        Record must exist in selected local subset (via `filter()`) rather than wider local cache.

        Raises RecordNotFoundError exception if not found.
        """
        try:
            return self._records[file_identifier]
        except KeyError:
            raise RecordNotFoundError(file_identifier) from None

    def push(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> None:
        """
        Add or update records in remote GitLab project repo.

        Requires a local cache to determine if records are additions or updates.

        Invalidates the local cache if needed so new/changed records are included.
        """
        if len(records) == 0:
            self._logger.info("No records to push, skipping")
            return

        stats = self._commit(records=records, title=title, message=message, author=author)

        if not any(stats.values()):
            self._logger.info("No records pushed, skipping cache invalidation")
            return

        self._logger.info("Recreating cache to reflect pushed changes")
        self._cache.purge()
        self._logger.info("Reloading pushed records into subset to reflect changes.")
        self.populate(inc_records=[record.file_identifier for record in records])
