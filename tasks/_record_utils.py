import json
import logging
import re
import sys
from collections.abc import Generator, Mapping, Sequence
from pathlib import Path

import inquirer
from boto3 import client as S3Client  # noqa: N812
from environs import Env
from jwskate import Jwk

from lantern.config import Config
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
from lantern.log import init as _init_logging
from lantern.models.record.record import Record as CatalogueRecord
from lantern.models.record.record import Record as RecordCatalogue
from lantern.models.record.revision import RecordRevision
from lantern.stores.gitlab import GitLabStore


def init_logging(config: Config) -> logging.Logger:
    """Initialise logging."""
    _init_logging(config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising")
    return logger


def init_store(logger: logging.Logger, config: Config, branch: str | None = None) -> GitLabStore:
    """Initialise store."""
    if branch is None:
        branch = config.STORE_GITLAB_BRANCH
    return GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        branch=branch,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )


def init_s3(config: Config) -> S3Client:  # ty: ignore[invalid-type-form]
    """Initialise S3 client."""
    return S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )


def init_admin_keys(config: Config) -> AdministrationKeys:
    """Initialise administration keys with private signing key for updating administrative metadata."""
    env = Env()  # needed for loading private signing key for admin metadata
    env.read_env()
    return AdministrationKeys(
        encryption_private=config.ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE,
        signing_private=Jwk(env.json("X_ADMIN_METADATA_SIGNING_KEY_PRIVATE")),
        signing_public=config.ADMIN_METADATA_SIGNING_KEY_PUBLIC,
    )


def init() -> tuple[logging.Logger, Config, GitLabStore, S3Client, AdministrationKeys]:  # ty: ignore[invalid-type-form]
    """Initialise common objects."""
    config = Config()
    logger = init_logging(config)
    store = init_store(logger, config)
    s3 = init_s3(config)
    keys = init_admin_keys(config)
    return logger, config, store, s3, keys


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
    validate_catalogue: bool = False,
) -> list[tuple[Record, Path]]:
    """
    Try to create Records from record configurations within a directory.

    Records are validated against base metadata library requirements by default, and optionally against catalogue
    specific requirements if appropriate (some tasks work with records before they'll validate).

    Invalid records are skipped with a warning.
    Valid records are checked for unsupported content but will not be skipped if present.

    Records are returned as a list of (Record, RecordPath) tuples, where 'RecordPath' is the Path to the source file.
    """
    # noinspection PyPep8Naming
    RecordClass = Record if not validate_catalogue else CatalogueRecord  # noqa: N806
    records: list[tuple[Record, Path]] = []

    for config_path in _parse_configs(search_path, glob_pattern=glob_pattern):
        config, config_path = config_path
        try:
            record = RecordClass.loads(config)
            if validate_base or validate_catalogue:
                record.validate()
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


def process_record_selections(logger: logging.Logger, identifiers: list[str]) -> list[str]:
    """
    Process identifiers into record file identifiers.

    Identifiers can be selections of one or more identifiers separated by commas and/or spaces.
    Identifiers within selections that cannot be parsed are skipped with an error.
    """
    file_identifiers = []
    for selection in identifiers:
        # split identifiers by commas and/or spaces
        selections = re.split(r"[\s,]+", selection)
        for identifier in selections:
            try:
                file_identifiers.append(_process_record_selection(identifier))
            except ValueError:
                logger.warning(f"Could not process '{identifier}' as a file identifier, skipping.")
                continue
    return file_identifiers


def get_records(logger: logging.Logger, store: GitLabStore, file_identifiers: list[str]) -> list[RecordRevision]:
    records = []
    store.populate()
    for file_identifier in file_identifiers:
        record = store.get(file_identifier=file_identifier)
        logger.info(
            f"Loaded record: {record.file_identifier} ('{record.identification.title}' {record.hierarchy_level.value})"
        )
        records.append(record)
    return records


def dump_records(logger: logging.Logger, output_path: Path, records: Sequence[Record | RecordRevision]) -> None:
    """Dump records to a path."""
    output_path.mkdir(parents=True, exist_ok=True)
    for record in records:
        record_path = output_path / f"{record.file_identifier}.json"
        logger.debug(f"Writing {record_path.resolve()}")
        with record_path.open(mode="w") as f:
            f.write(record.dumps_json(strip_admin=False))


def clean_configs(
    logger: logging.Logger, records: Mapping[Path, Record | RecordCatalogue], file_identifiers: list[str]
) -> None:
    """Clean up input path."""
    input_files_indexed = {}
    for path, record in records.items():
        input_files_indexed[record.file_identifier] = path

    for file_identifier in file_identifiers:
        input_files_indexed[file_identifier].unlink()
        logger.info(f"Removed processed file: '{input_files_indexed[file_identifier]}'.")


def confirm_branch(logger: logging.Logger, store: GitLabStore, action: str) -> None:
    """Confirm target branch."""
    logger.info(f"{action} branch '{store.branch}'")
    answers = inquirer.prompt([inquirer.Confirm(name="confirm", message="Correct branch?", default=True)])
    if not answers["confirm"]:
        logger.info("Aborting. Set `STORE_GITLAB_BRANCH` in config to change branch")
        sys.exit(1)
