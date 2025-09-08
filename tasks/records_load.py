import json
import logging
import shutil
from collections.abc import Generator
from pathlib import Path

import inquirer
from environs import Env

from lantern.config import Config
from lantern.lib.metadata_library.models.record import RecordInvalidError
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.record import Record
from lantern.stores.base import Store
from lantern.stores.gitlab import GitLabStore


def _parse_configs(search_path: Path) -> Generator[dict, None, None]:
    """
    Try to load any record configurations from JSON files from a directory.

    Subdirectories ARE searched.
    """
    for json_path in search_path.glob("**/*.json"):
        with json_path.open("r") as f:
            yield json.load(f)


def _parse_records(logger: logging.Logger, search_path: Path) -> list[Record]:
    """
    Try to create Records from record configurations within a directory.

    Records must validate.
    """
    records = []
    configs = list(_parse_configs(search_path))
    for config in configs:
        try:
            record = Record.loads(config)
            record.validate()
        except RecordInvalidError:
            logger.warning(f"Record '{config['file_identifier']}' does not validate, skipping.")
            continue
        if not Record._config_supported(config):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append(record)
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _copy_records(logger: logging.Logger, records: list[Path], path: Path) -> None:
    """Copy list of record configurations to a directory."""
    path.mkdir(parents=True, exist_ok=True)
    for path in records:
        record_path = path / path.name
        logger.debug(f"Copying to {record_path.resolve()}")
        shutil.copy(path, record_path)


def _filter_records(logger: logging.Logger, working_copy: Path, store: Store) -> list[Path]:
    """
    Filter new and/or modified records from a directory of record configurations.

    Requires a catalogue Store to determine existing records and a hash of their contents.
    Candidate records are compared a Catalogue store to determine:
    - if the record already exists (if not, include)
    - if the hash of the record contents is the same as an existing record (if not, include)

    Calculating the hash of the record is slightly expensive as it needs to be loaded as Record for an accurate
    comparison with the Store (i.e. we can't just hash the record configuration).

    Returns a list paths for new/modified record configs.
    """
    existing_hashes = {record.file_identifier: record.sha1 for record in store.records}
    candidate_hashes = {record.file_identifier: record.sha1 for record in _parse_records(logger, working_copy)}
    file_identifiers = [
        file_identifier
        for file_identifier, sha1 in candidate_hashes.items()
        if file_identifier not in existing_hashes or existing_hashes[file_identifier] != sha1
    ]
    return [next(working_copy.glob(f"**/{fid}.json")) for fid in file_identifiers]


def _get_args(default_path: str | None) -> Path:
    """Get user input."""
    answers = inquirer.prompt(
        [
            inquirer.Path(
                "working_copy",
                message="Path to records directory.",
                default=default_path,
                exists=True,
                path_type=inquirer.Path.DIRECTORY,
            )
        ]
    )
    return Path(answers["working_copy"])


def main() -> None:
    """Entrypoint."""
    config = Config()
    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    env = Env()
    env.read_env()
    default_path = env.str("LANTERN_TASK_RECORDS_LOAD_FROM")

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )
    logger.info("Loading records from Store")
    store.populate()

    working_copy = _get_args(default_path)
    import_path = Path("./import")

    logger.info(f"Loading changed/new records from '{working_copy.resolve()}'")
    record_paths = _filter_records(logger, working_copy, store)

    _copy_records(logger, record_paths, import_path)
    logger.info(f"Dumped {len(record_paths)} changed records in {import_path.resolve()} for editing.")


if __name__ == "__main__":
    main()
