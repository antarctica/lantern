import functools
import json
import logging
import re
import subprocess
import sys
import time
from collections.abc import Callable, Generator, Mapping, Sequence
from pathlib import Path
from typing import Literal

import inquirer
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import (
    AdministrationKeys,
    AdministrationMetadataSubjectMismatchError,
)
from boto3 import client as S3Client  # noqa: N812
from tasks._config import ExtraConfig

from lantern.config import Config
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.utils.admin import get_admin
from lantern.log import init as _init_logging
from lantern.models.record.record import Record as CatalogueRecord
from lantern.models.record.record import Record as RecordCatalogue
from lantern.models.record.revision import RecordRevision
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import init_gitlab_store

TargetEnvironment = Literal["local", "remote"]


def init_logging(config: Config) -> logging.Logger:
    """Initialise logging."""
    _init_logging(config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising")
    return logger


def init_store(
    logger: logging.Logger,
    config: Config,
    path: Path | None = None,
    branch: str | None = None,
    cached: bool = False,
    frozen: bool = False,
) -> GitLabStore | GitLabCachedStore:
    """Initialise store."""
    return init_gitlab_store(logger=logger, config=config, path=path, branch=branch, cached=cached, frozen=frozen)


def init_s3(config: Config) -> S3Client:  # ty: ignore[invalid-type-form]
    """Initialise S3 client."""
    return S3Client(
        "s3",
        aws_access_key_id=config.SITE_UNTRUSTED_S3_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_S3_ACCESS_SECRET,
        region_name="eu-west-1",
    )


def init(
    cached_store: bool = False, frozen_store: bool = False
) -> tuple[logging.Logger, ExtraConfig, GitLabStore | GitLabCachedStore]:
    """
    Initialise common objects.

    Store is not cached by default to allow switching between branches efficiently.
    Store is not frozen by default to allow fetching changes before processing.
    """
    config = ExtraConfig()
    logger = init_logging(config)
    store = init_store(logger, config, cached=cached_store, frozen=frozen_store)
    return logger, config, store


def _parse_configs(search_path: Path, glob_pattern: str | None = None) -> Generator[tuple[dict, Path], None, None]:
    """
    Try to load any record configurations from JSON files from a directory.

    By default, subdirectories are NOT searched.

    Yields tuples of (config dict, Path to source file).
    """
    if glob_pattern is None:
        glob_pattern = "*.json"

    for json_path in search_path.glob(glob_pattern):
        with json_path.open("r") as f:
            yield json.load(f), json_path


def parse_records(
    logger: logging.Logger,
    search_path: Path,
    glob_pattern: str | None = None,
    validate_base: bool = True,
    validate_profiles: bool = True,
    validate_catalogue: bool = False,
) -> list[tuple[Record | CatalogueRecord, Path]]:
    """
    Try to create Records from record configurations within a directory.

    Records are validated against base metadata library requirements by default (including profiles), and optionally
    against catalogue specific requirements if appropriate (some tasks work with records before they'll validate).

    If needed, profiles validation can be disabled. Invalid records are skipped with a warning.

    Valid records are checked for unsupported content but will not be skipped if present.

    Records are returned as a list of (Record, RecordPath) tuples, where 'RecordPath' is the Path to the source file.
    """
    # noinspection PyPep8Naming
    RecordClass = Record if not validate_catalogue else CatalogueRecord  # noqa: N806
    records: list[tuple[Record | CatalogueRecord, Path]] = []

    for config_path in _parse_configs(search_path, glob_pattern=glob_pattern):
        config, config_path = config_path
        try:
            record = RecordClass.loads(config)
            if validate_base or validate_catalogue:
                record.validate(use_profiles=validate_profiles)
        except RecordInvalidError as e:
            logger.warning(f"Record '{config['file_identifier']}' does not validate, skipping.")
            logger.info(e.validation_error)
            continue
        # noinspection PyProtectedMember
        if not Record._config_supported(config=config, logger=logger):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append((record, config_path))
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _process_record_selection(identifier: str) -> str:
    """
    Process identifier into record file identifier.

    Handles common references such as URLs or file names for convenience.
    """
    # for:
    # -> '- https://example.com/items/123' or
    # -> '* 123.json' or
    # -> ' 123 '
    # as:
    # -> 'https://example.com/items/123'
    # -> '123.json'
    # -> '123'
    identifier = re.sub(r"^[-*]\s+", "", identifier.strip())

    if "https://" in identifier:
        # for:
        # -> 'https://example.com/items/123' or
        # -> 'https://example.com/items/123/' or
        # -> 'https://example.com/items/123/index.html' or
        # -> 'https://example.com/items/123/index.html#tab-foo'
        # as '123'
        fid_clean = re.sub(r"(index\.html.*|[#?].*)$", "", identifier)
        return fid_clean.rstrip("/").split("/")[-1]

    if ".json" in identifier:
        # for '123.json' as '123'
        return identifier.replace(".json", "")

    # for a UUIDv4 string
    if re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        identifier,
    ):
        return identifier

    msg = f"Cannot parse identifier '{identifier}'"
    raise ValueError(msg) from None


def process_record_selections(logger: logging.Logger, identifiers: list[str]) -> set[str]:
    """
    Process identifiers into record file identifiers.

    Identifiers can be selections of one or more identifiers separated by commas and/or spaces.
    Identifiers within selections that cannot be parsed are skipped with an error.
    """
    file_identifiers = set()
    for selection in identifiers:
        # split identifiers by commas and/or spaces
        selections = re.split(r"[\s,]+", selection)
        for identifier in selections:
            try:
                file_identifiers.add(_process_record_selection(identifier))
            except ValueError:
                logger.warning(f"Could not process '{identifier}' as a file identifier, skipping.")
                continue
    return file_identifiers


def dump_records(logger: logging.Logger, output_path: Path, records: Sequence[Record | RecordRevision]) -> None:
    """Dump records to a path."""
    output_path.mkdir(parents=True, exist_ok=True)
    for record in records:
        record_path = output_path / f"{record.file_identifier}.json"
        logger.debug(f"Writing {record_path.resolve()}")
        with record_path.open(mode="w") as f:
            f.write(record.dumps_json(strip_admin=False))


def clean_record_configs(
    logger: logging.Logger, records: Mapping[Path, Record | RecordCatalogue], file_identifiers: list[str]
) -> None:
    """Clean up input path."""
    input_files_indexed = {}
    for path, record in records.items():
        input_files_indexed[record.file_identifier] = path

    for file_identifier in file_identifiers:
        input_files_indexed[file_identifier].unlink()
        logger.info(f"Removed processed file: '{input_files_indexed[file_identifier]}'.")


def confirm_source(logger: logging.Logger, store: GitLabStore, action: str) -> None:
    """Confirm store source."""
    logger.info(f"{action} branch '{store._source.ref}' on '{store._project.http_url_to_repo}'")
    if not inquirer.confirm(message="Correct source?", default=True):
        logger.info("Aborting. Set `STORE_GITLAB_*` in config to change source.")
        sys.exit(1)


def pick_records(logger: logging.Logger, records: list[Record]) -> list[Record]:
    """Pick records from a list."""
    choices = {
        f"{r.file_identifier} ('{r.identification.title}' {r.hierarchy_level.value})": r.file_identifier
        for r in records
    }
    logger.debug(f"Choices: {list(choices.keys())}")

    selections = inquirer.checkbox(message="Records", choices=list(choices.keys()))

    records_ = {r.file_identifier: r for r in records}
    selected_fids = [choices[k] for k in selections]
    logger.info(f"Selected records: {selected_fids}")
    return [records_[fid] for fid in selected_fids]


def get_record(logger: logging.Logger, store: GitLabStore, identifier: str | None = None) -> Record:
    """Get record from store using flexible, and optionally preset, identifier."""
    if identifier is None:
        identifier = inquirer.text(message="Record identifier")
    file_identifier = next(iter(process_record_selections(logger=logger, identifiers=[identifier])))
    return store.select_one(file_identifier=file_identifier)


def load_record(logger: logging.Logger, ref: tuple[str | None, Path | None], store: GitLabStore) -> Record:
    """Load a record from a store by its identifier or from a local file path."""
    if ref[1] is not None:
        with ref[1].open(mode="r") as f:
            return Record.loads(json.load(f))
    return get_record(logger=logger, store=store, identifier=ref[0])


def ping_host(host: str) -> None:
    try:
        subprocess.run(  # noqa: S603
            ["ssh", host, "echo x"],  # noqa: S607
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        msg = f"Host unreachable: {host}"
        raise RuntimeError(msg) from e


def confirm(logger: logging.Logger, message: str) -> None:
    """Confirm user wants to proceed."""
    if not inquirer.confirm(message=message, default=True):
        logger.info("Cancelled by the user.")
        sys.exit(1)


def ensure_admin(logger: logging.Logger, record: Record, keys: AdministrationKeys) -> AdministrationMetadata:
    """Ensure record has valid, minimal, admin metadata."""
    admin = None
    if record.file_identifier is None:
        msg = "File identifier required."
        raise ValueError(msg) from None
    try:
        admin = get_admin(keys=keys, record=record)
    except AdministrationMetadataSubjectMismatchError as e:
        # prompt user whether to ignore mismatch by clearing existing admin metadata
        if inquirer.confirm(
            message=(
                "Existing administration metadata references the wrong record. Drop existing metadata (if record is cloned)?"
            ),
            default=False,
        ):
            pass
        else:
            raise e from e
    if admin is None:
        logger.warning("No or unsupported administration metadata found, creating new instance.")
        if not inquirer.confirm(
            message="Existing administration metadata missing or unsupported, reset?",
            default=False,
        ):
            logger.info("Aborting.")
            sys.exit(1)
        admin = AdministrationMetadata(id=record.file_identifier)
    return admin


def time_task(label: str) -> Callable:
    """
    Time a task and log duration.

    Uses a temporary app logger.

    Used in workflow dev tasks.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            start = time.monotonic()
            result = func(*args, **kwargs)
            logger = logging.getLogger("app")
            logger.setLevel(logging.INFO)
            logger.info(f"{label} took {round(time.monotonic() - start)} seconds")
            return result

        return wrapper

    return decorator
