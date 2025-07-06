from __future__ import annotations

import json
import logging
import shutil
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from gitlab import Gitlab
from gitlab.v4.objects import Project
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.models.record import Record
from lantern.models.record.summary import RecordSummary
from lantern.stores.base_store import RecordNotFoundError, Store

if TYPE_CHECKING:
    # False at run time, only for type checker
    pass


class RemoteStoreUnavailableError(Exception):
    """Raised when records cannot be loaded from the remote store."""

    pass


class GitLabStore(Store):
    """
    Basic Store backed by a GitLab project.

    Uses https://python-gitlab.readthedocs.io/ to interact with the GitLab API, rather than as a generic Git repository.

    For efficiency and basic offline support a local records cache is maintained, from which a local subset of records
    is loaded, optionally filtered by including or excluding a set of record file identifiers, and optionally any
    directly related records (e.g. the sides of a physical map) to this filtered subset.

    Basic cache-validation is performed by comparing the head commit from when the cache was created against the live
    remote repository. If different (meaning the cache is stale), the cache is recreated. When offline, a warning is
    logged that cache may be stale.

    When the cache is (re)created, properties needed to create RecordSummaries are saved to a derived file to avoid
    loading full records.

    For reference there are three sets of records:
    1. all records in the remote GitLab project repository (source of truth)
    2. all records in a (possibly stale) file based local cache
    3. all or a filtered subset of records from the local cache, held in memory
    """

    def __init__(
        self, logger: logging.Logger, endpoint: str, access_token: str, project_id: str, cache_path: Path
    ) -> None:
        self._logger = logger

        self._summaries: dict[str, RecordSummary] = {}
        self._records: dict[str, Record] = {}

        self._endpoint = endpoint
        self._access_token = access_token
        self._project_id = project_id
        self._branch = "main"
        self._records_path_name = "records"
        self._cache_path = cache_path
        self._cache_head_path = self._cache_path / "head_commit.json"
        self._cache_index_path = self._cache_path / "index.json"
        self._cache_summaries_path = self._cache_path / "summaries.json"
        self._client = Gitlab(url=self._endpoint, private_token=self._access_token)
        self._online = self._is_online()

    def __len__(self) -> int:
        """Record count."""
        return len(self._records)

    def _is_online(self) -> bool:
        """Determine if the GitLab API is accessible."""
        try:
            _ = self._project
        except RequestsConnectionError:
            return False
        return True

    @property
    def _project(self) -> Project:
        """GitLab project."""
        return self._client.projects.get(self._project_id)

    @property
    def _head_commit_id(self) -> str:
        """The ID of the current head commit in the remote project repo."""
        return self._project.commits.list(get_all=False)[0].id

    def _load_record(self, record_path: Path) -> Record:
        """Load selected records from a file."""
        self._logger.debug(f"Loading record from '{record_path.resolve()}'")
        with record_path.open() as file:
            config = json.load(file)
        return Record.loads(config, check_supported=True, logger=self._logger)

    def _add_record(self, record: Record) -> None:
        """Include record and its summary in the local subset."""
        self._records[record.file_identifier] = record
        self._summaries[record.file_identifier] = RecordSummary.loads(record)

    def _add_summaries(self, file_identifiers: list[str] | None = None) -> None:
        """Load selected record summaries from cached summaries file."""
        file_identifiers = file_identifiers or []
        with self._cache_summaries_path.open() as file:
            summaries = json.load(file)["summaries"]
        for file_identifier in file_identifiers:
            self._logger.debug(f"Loading record summary '{file_identifier}'")
            self._summaries[file_identifier] = RecordSummary.loads(summaries[file_identifier])

    def _cache_is_current(self) -> bool:
        """
        Determine if cache is current or stale compared to the remote project repo.

        Where the cache does not exist, or a head commit ID isn't available, the cache is considered stale.
        """
        try:
            with self._cache_head_path.open() as f:
                cache_commit = json.load(f)
        except FileNotFoundError:
            return False

        cache_commit_id = cache_commit["id"]
        return cache_commit_id == self._head_commit_id

    def _populate_cache(self, config_paths: list[Path], head_commit: dict) -> None:
        """
        Persist a set of record configuration files to the local cache.

        Steps:
        - copy each record config file to the cache directory
        - parse each record config file as a Record
        - index each Record by file identifier and SHA1 hash of its configuration
        - derive a RecordSummary from each Record
        - save RecordSummary configs to a summaries file
        - save the index of file identifiers and SHA1 hashes to a file
        - save details of the current head commit to a file for cache validation
        """
        records_path = self._cache_path / self._records_path_name
        records_path.mkdir(parents=True, exist_ok=True)
        index = {}
        summaries = []

        for config_path in config_paths:
            shutil.copy2(config_path, records_path.joinpath(config_path.name))
            record = self._load_record(config_path)
            index[record.file_identifier] = record.sha1
            summary = RecordSummary.loads(record)
            summaries.append(summary.dumps())

        with self._cache_head_path.open(mode="w") as f:
            json.dump(head_commit, f, indent=2)

        with self._cache_index_path.open(mode="w") as f:
            data = {"index": index}
            json.dump(data, f, indent=2)

        with self._cache_summaries_path.open(mode="w") as f:
            data = {"summaries": {summary["file_identifier"]: summary for summary in summaries}}
            json.dump(data, f, indent=2)

    def _create_cache(self) -> None:
        """
        Cache records from remote store locally.

        Any existing cache is removed and recreated, regardless of whether it's up-to-date.

        For efficiency, all records are fetched together using a GitLab project repo archive.

        Steps:
        - remove existing cache directory if present
        - create cache directory
        - create a project repo archive via the GitLab API as a tar.gz archive
        - extract the contents of the archive to a temporary directory
        """
        if self._cache_path.exists():
            self._logger.debug(f"Removing existing cache directory '{self._cache_path.resolve()}'")
            shutil.rmtree(self._cache_path)

        self._logger.info("Caching records from repo export")
        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)
            export_path = temp_path / "export.tgz"

            with export_path.open(mode="wb") as f:
                self._project.repository_archive(format="tgz", streamed=True, action=f.write)
            with tarfile.open(export_path, "r:gz") as tar:
                tar.extractall(path=temp_path, filter="data")

            record_paths = list(temp_path.glob(f"**/{self._records_path_name}/**/*.json"))
            head_commit = self._project.commits.get(self._head_commit_id)
            self._populate_cache(config_paths=record_paths, head_commit=head_commit.attributes)

    def _ensure_cache(self) -> None:
        """
        Ensure cache exists and is up-to-date.

        An existing, up-to-date, cache is not modified.
        """
        if not self._online and not self._cache_path.exists():
            msg = "Local cache and GitLab unavailable. Cannot load records."
            raise RemoteStoreUnavailableError(msg) from None

        if self._online and not self._cache_path.exists():
            self._create_cache()
            return

        if not self._online:
            self._logger.warning("Cannot check if records cache is current, loading possibly stale records")
            return

        if self._online and not self._cache_is_current():
            self._logger.warning("Cached records are not up to date, reloading from GitLab")
            self.purge()
            self._ensure_cache()
            return

        self._logger.info("Records cache exists and is current, no changes needed.")

    def _filter_cache_except(self, file_identifiers: list[str]) -> None:
        """Load records from the local cache into memory with specified exceptions."""
        msg = (
            f"Loading all records from cache except {len(file_identifiers)} excluded"
            if file_identifiers
            else "Loading all records from cache"
        )
        self._logger.info(msg)
        for record_path in self._cache_path.glob("records/*.json"):
            if record_path.stem in file_identifiers:
                self._logger.info(f"Record '{record_path.stem}' excluded, skipping")
                continue
            record = self._load_record(record_path)
            self._add_record(record)
        # still load summaries for excluded records in case they are referenced by included records
        self._add_summaries(file_identifiers)

    def _filter_cache_only(self, file_identifiers: list[str], inc_related: bool) -> None:
        """
        Load specific records from the local cache into memory.

        As this method is restrictive but some records are composites (e.g. physical maps with multiple sides), the
        `inc_related` parameter can be used also include directly related records for each selected record.
        """
        for file_identifier in file_identifiers:
            record_path = self._cache_path / self._records_path_name / f"{file_identifier}.json"
            if not record_path.exists():
                self._logger.warning(f"Record '{file_identifier}' not found in cache, skipping")
                return

            record = self._load_record(record_path)
            self._add_record(record)
            self._logger.info(f"Record '{file_identifier}' added from cache")
            related_identifiers = record.identification.aggregations.identifiers(exclude=[record.file_identifier])
            self._add_summaries(list(related_identifiers))

        if not inc_related:
            self._logger.info(f"{len(file_identifiers)} selected records loaded from cache without direct relations")
            return

        additional_identifiers = set()
        for file_identifier in file_identifiers:
            # load directly related records as Records (e.g. so all sides of a physical map are built)
            record = self.get(file_identifier)
            related_identifiers = record.identification.aggregations.identifiers(exclude=[record.file_identifier])
            for related_identifier in related_identifiers:
                record_path = self._cache_path / self._records_path_name / f"{related_identifier}.json"
                related_record = self._load_record(record_path)
                self._add_record(related_record)
                sub_related_identifiers = related_record.identification.aggregations.identifiers(
                    exclude=[related_record.file_identifier]
                )
                additional_identifiers.update(sub_related_identifiers)
        # also load related records of directly related records as additional RecordSummaries
        self._add_summaries(list(additional_identifiers))
        self._logger.info(f"{len(file_identifiers)} selected records loaded from cache with direct relations")

    def _filter_cache(self, inc_records: list[str], exc_records: list[str], inc_related: bool) -> None:
        """
        Load some or all records from the local cache into memory.

        Only records selected here can be accessed from the `records`/`summaries` properties and related methods.

        This method essentially selects which filtering pathway to use.
        """
        self._ensure_cache()

        if inc_records and exc_records:
            msg = "Including and excluding records is not supported."
            raise ValueError(msg) from None

        if not inc_records:
            self._filter_cache_except(exc_records)
            return

        self._filter_cache_only(inc_records, inc_related)

    def _get_remote_hashed_path(self, file_name: str) -> str:
        """
        Get the hashed storage path for a file name.

        A hashed path is used to avoid too many files being in a single directory.

        For `_get_hashed_path(file_name="0be5339c-9d35-44c9-a10f-da4b5356840b.json")`
        return: 'records/0b/e5/0b5339c-9d35-44c9-a10f-da4b5356840b.json'
        """
        return f"{self._records_path_name}/{file_name[:2]}/{file_name[2:4]}/{file_name}"

    def _commit(self, records: list[Record], title: str, message: str, author: tuple[str, str]) -> dict[str, int]:
        with self._cache_index_path.open() as f:
            records_index = json.load(f)["index"]

        actions: list[dict] = []
        changes: dict[str, list[str]] = {"update": [], "create": []}

        data = {
            "branch": self._branch,
            "commit_message": f"{title}\n{message}",
            "author_name": author[0],
            "author_email": author[1],
            "actions": actions,
        }

        for record in records:
            existing_hash = records_index.get(record.file_identifier)
            if record.sha1 == existing_hash:
                self._logger.debug(f"Record '{record.file_identifier}' is unchanged, skipping")
                continue

            action = "update"
            if existing_hash is None:
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

    @property
    def summaries(self) -> list[RecordSummary]:
        """Loaded RecordSummaries."""
        return list(self._summaries.values())

    @property
    def records(self) -> list[Record]:
        """Loaded Records."""
        return list(self._records.values())

    def populate(
        self, inc_records: list[str] | None = None, exc_records: list[str] | None = None, inc_related: bool = False
    ) -> None:
        """
        Load records and summaries from local cache into the local subset, optionally filtered by file identifier.

        Wrapper around `_filter_cached()`.
        """
        if inc_records is None:
            inc_records = []
        if exc_records is None:
            exc_records = []
        self._filter_cache(inc_records=inc_records, exc_records=exc_records, inc_related=inc_related)

    def purge(self) -> None:
        """Clear local cache and in-memory records/summaries."""
        self._summaries = {}
        self._records = {}
        if self._cache_path.exists():
            shutil.rmtree(self._cache_path)

    def get(self, file_identifier: str) -> Record:
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

        self._ensure_cache()
        stats = self._commit(records=records, title=title, message=message, author=author)

        if not any(stats.values()):
            self._logger.info("No records pushed, skipping cache invalidation")
            return

        self._logger.info("Recreating cache to reflect pushed changes")
        self._create_cache()
        self._logger.info("Reloading pushed records into subset.")
        for record in records:
            self._add_record(record)
