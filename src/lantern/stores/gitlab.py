import json
import logging
import shutil
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

from assets_tracking_service.lib.bas_data_catalogue.models.record import Record
from assets_tracking_service.lib.bas_data_catalogue.models.record.summary import RecordSummary
from gitlab import Gitlab
from gitlab.v4.objects import Project
from requests.exceptions import ConnectionError as RequestsConnectionError

from lantern.stores.base_store import Store


class RecordsUnavailableError(Exception):
    """Raised when records cannot be loaded from the store."""

    pass


class GitLabStore(Store):
    """
    Basic Repository backed by GitLab project.

    Uses the https://python-gitlab.readthedocs.io/ package to load Records from a GitLab project via a local cache.

    Basic cache-validation is performed by recording comparing the head commit at the time the cache was created against
    the current repository. If stale, the cache is destroyed and recreated.

    When the cache is (re)generated, record config subsets used for RecordSummaries are saved separately to avoid
    needing to load full records when generating summaries.

    A single record target can be specified when loading records to only load a single full Record and RecordSummary,
    plus RecordSummaries of any directly related resources (so that related resources can be included in Items).

    Basic offline support is included using cached Records. This may lead to stale results as cache validation will
    be unavailable.
    """

    # TODO: tests
    # TODO: file revision

    def __init__(
        self, logger: logging.Logger, endpoint: str, access_token: str, project_id: str, cache_path: Path
    ) -> None:
        self._logger = logger

        self._summaries: list[RecordSummary] = []
        self._records: list[Record] = []

        self._endpoint = endpoint
        self._access_token = access_token
        self._project_id = project_id
        self._cache_path = cache_path
        self._cache_head_path = self._cache_path / "head_commit.json"
        self._cache_summaries_path = self._cache_path / "summaries.json"
        self._client = Gitlab(url=self._endpoint, private_token=self._access_token)
        self._online = self._is_online()

    def __len__(self) -> int:
        """Record count."""
        return len(self._records)

    def _is_online(self) -> bool:
        """Check if the GitLab is accessible."""
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
        """Get the head commit ID of the project."""
        return self._project.commits.list(get_all=False)[0].id

    @property
    def summaries(self) -> list[RecordSummary]:
        """All loaded record summaries."""
        return self._summaries

    @property
    def records(self) -> list[Record]:
        """All loaded records."""
        return self._records

    def purge(self) -> None:
        """Clear cache and loaded records."""
        self._summaries = []
        self._records = []
        if self._cache_path.exists():
            shutil.rmtree(self._cache_path)

    @staticmethod
    def _get_related_identifiers(record: Record) -> set[str]:
        """For building a single item with its direct relations."""
        return {
            related.identifier.identifier
            for related in record.identification.aggregations
            if related.identifier.identifier != record.file_identifier
        }

    @staticmethod
    def _make_summary_config(config: dict) -> dict:
        """Subset a Record config into a RecordSummary config."""
        return {
            "file_identifier": config["file_identifier"],
            "hierarchy_level": config["hierarchy_level"],
            "date_stamp": config["metadata"]["date_stamp"],
            "title": config["identification"]["title"]["value"],
            "purpose": config["identification"].get("purpose", None),
            "edition": config["identification"].get("edition", None),
            "creation": config["identification"]["dates"].get("creation", None),
            "revision": config["identification"]["dates"].get("revision", None),
            "publication": config["identification"]["dates"].get("publication", None),
            "graphic_overviews": config["identification"].get("graphic_overviews", []),
            "constraints": config["identification"].get("constraints", []),
            "aggregations": config["identification"].get("aggregations", []),
        }

    def _load_config(self, path: Path) -> dict:
        """Load record config from JSON file and report any unsupported content."""
        with path.open() as file:
            config = json.load(file)
            if not Record.config_supported(config):
                self._logger.warning(
                    f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
                )
            return config

    def _load_record(self, file_identifier: str) -> None:
        """Load record from file path."""
        record_path = self._cache_path.joinpath(f"records/{file_identifier}.json")
        self._logger.debug(f"Loading record '{file_identifier}' from '{record_path.resolve()}'")
        config = self._load_config(record_path)
        record = Record.loads(config)
        self._records.append(record)
        self._summaries.append(RecordSummary.loads(record))

    def _load_summaries(self, file_identifiers: list[str] | None = None) -> None:
        """Load record summaries from file path."""
        file_identifiers = file_identifiers or []
        with self._cache_summaries_path.open() as file:
            summaries = json.load(file)["summaries"]
        for file_identifier in file_identifiers:
            self._logger.debug(f"Loading record summary '{file_identifier}'")
            self._summaries.append(RecordSummary.loads(summaries[file_identifier]))

    def _cache_is_current(self) -> bool:
        """Check cache is current against remote repository."""
        try:
            with self._cache_head_path.open() as f:
                cache_commit = json.load(f)
        except FileNotFoundError:
            return False
        cache_commit_id = cache_commit["id"]

        return cache_commit_id == self._head_commit_id

    def _cache_records(self) -> None:
        """
        Load contents of project repo and cache locally.

        For simplicity, and because the repository is small, records can be fetched from a project repo archive.
        """
        self._cache_path.unlink(missing_ok=True)

        self._logger.info("Caching records from repo export")
        records_path = self._cache_path / "records"
        records_path.mkdir(parents=True, exist_ok=True)
        summaries = []

        with TemporaryDirectory() as tmp_path:
            temp_path = Path(tmp_path)
            export_path = temp_path / "export.tgz"

            with export_path.open(mode="wb") as f:
                self._project.repository_archive(format="tgz", streamed=True, action=f.write)
            with tarfile.open(export_path, "r:gz") as tar:
                tar.extractall(path=temp_path, filter="data")
            for record_path in temp_path.glob("**/records/**/*.json"):
                shutil.copy2(record_path, records_path.joinpath(record_path.name))
                config = self._load_config(record_path)
                summaries.append(self._make_summary_config(config))
        with self._cache_head_path.open(mode="w") as f:
            head_commit = self._project.commits.get(self._head_commit_id)
            json.dump(head_commit.attributes, f, indent=2)
        with self._cache_summaries_path.open(mode="w") as f:
            data = {"summaries": {summary["file_identifier"]: summary for summary in summaries}}
            json.dump(data, f, indent=2)

    def _get_record(self, file_identifier: str) -> Record | None:
        """Intentionally simplistic lookup method."""
        for record in self._records:
            if record.file_identifier == file_identifier:
                return record
        return None

    def _check_cache(self) -> None:
        """Check cache exists or is current."""
        if not self._online and not self._cache_path.exists():
            msg = "Local cache and GitLab unavailable. Cannot load records."
            raise RecordsUnavailableError(msg) from None

        if self._online and not self._cache_path.exists():
            self._cache_records()
            return

        if not self._online:
            self._logger.warning("Cannot check if records cache is current, loading possibly stale records")
            return

        if self._online and not self._cache_is_current():
            self._logger.warning("Cached records are not up to date, reloading from GitLab")
            self.purge()
            self._check_cache()
            return

    def _load_records_cached_all(self) -> None:
        self._logger.info("Loading all records from cache")
        for record_path in self._cache_path.glob("records/*.json"):
            self._load_record(record_path.stem)
        return

    def _load_records_cached_except(self, file_identifiers: list[str]) -> None:
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
            self._load_record(record_path.stem)
        # still load summaries for excluded records in case they are referenced by included records
        self._load_summaries(file_identifiers)

    def _load_records_cached_only(self, file_identifiers: list[str], inc_related: bool) -> None:
        for file_identifier in file_identifiers:
            try:
                self._load_record(file_identifier)
            except FileNotFoundError:
                self._logger.warning(f"Record '{file_identifier}' not found in cache, skipping")
                return

            self._logger.info(f"Record '{file_identifier}' loaded from cache")
            related_identifiers = self._get_related_identifiers(self._get_record(file_identifier))
            self._load_summaries(list(related_identifiers))

        if not inc_related:
            self._logger.info(f"{len(file_identifiers)} selected records loaded from cache without direct relations")
            return

        additional_identifiers = set()
        for file_identifier in file_identifiers:
            # load directly related records as Records (e.g. so all sides of a physical map are built)
            for related_identifier in self._get_related_identifiers(self._get_record(file_identifier)):
                self._load_record(related_identifier)
                additional_identifiers.update(self._get_related_identifiers(self._get_record(related_identifier)))
        # load related records of directly related records as RecordSummaries
        self._load_summaries(list(additional_identifiers))
        self._logger.info(f"Loading single record '{file_identifier}' from cache with direct dependencies")

    def _load_records_cached(self, inc_records: list[str], exc_records: list[str], inc_related: bool) -> None:
        self._check_cache()

        if inc_records and exc_records:
            msg = "Including and excluding records is not supported."
            raise ValueError(msg) from None

        if not inc_records:
            self._load_records_cached_except(exc_records)
            return

        self._load_records_cached_only(inc_records, inc_related)

    def loads(self, inc_records: list[str] | None, exc_records: list[str] | None, inc_related: bool = False) -> None:
        """Load records from cached repository contents."""
        if inc_records is None:
            inc_records = []
        if exc_records is None:
            exc_records = []
        self._load_records_cached(inc_records=inc_records, exc_records=exc_records, inc_related=inc_related)
