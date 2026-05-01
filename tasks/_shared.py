import functools
import json
import logging
import re
import subprocess
import sys
import time
from collections.abc import Callable, Collection, Generator, Mapping, Sequence
from pathlib import Path
from typing import Literal, cast, overload

import inquirer
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import (
    AdministrationKeys,
    AdministrationMetadataSubjectMismatchError,
)
from boto3 import client as S3Client  # noqa: N812
from tasks._config import ExtraConfig

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.utils.admin import get_admin
from lantern.log import init as _init_logging
from lantern.models.record.record import Record as RecordCatalogue
from lantern.models.record.revision import RecordRevision

ExportTarget = Literal["local", "remote"]


def init_logging(config: Config) -> logging.Logger:
    """Initialise logging."""
    _init_logging(config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising")
    return logger


def init_s3(config: Config) -> S3Client:  # ty: ignore[invalid-type-form]
    """Initialise S3 client."""
    return S3Client(
        "s3",
        aws_access_key_id=config.SITE_UNTRUSTED_S3_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_S3_ACCESS_SECRET,
        region_name="eu-west-1",
    )


def init_cat(logger: logging.Logger) -> BasCatalogue:
    """
    Initialise BAS Catalogue.

    Store is not cached by default to allow switching between branches efficiently.
    Store is not frozen by default to allow fetching changes before processing.
    """
    config = ExtraConfig()
    s3 = init_s3(config)
    return BasCatalogue(logger=logger, config=config, s3=s3)


def init() -> tuple[logging.Logger, ExtraConfig, BasCatalogue]:
    """Initialise common dev task objects."""
    config = ExtraConfig()
    logger = init_logging(config)
    return logger, config, init_cat(logger)


def confirm(logger: logging.Logger, message: str, abort_msg: str | None = None) -> None:
    """Confirm user wants to proceed."""
    abort_msg = abort_msg if abort_msg else "Aborting. Cancelled by the user."
    if not inquirer.confirm(message=message, default=True):
        logger.info(abort_msg)
        sys.exit(1)


def get_gitlab_source(logger: logging.Logger, cat: BasCatalogue, action: str) -> str:
    """Confirm GitLab store source."""
    default = cat.repo.gitlab_default_branch
    branch = inquirer.text(message="GitLab branch", default=default)
    logger.info(f"{action} branch '{branch}' on '{cat.repo.gitlab_project_url}'")
    return branch


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


@overload
def parse_records(
    logger: logging.Logger,
    search_path: Path,
    glob_pattern: str | None = None,
    validate_base: bool = True,
    validate_profiles: bool = True,
    validate_catalogue: Literal[False] = False,
) -> list[tuple[Record, Path]]: ...


@overload
def parse_records(
    logger: logging.Logger,
    search_path: Path,
    glob_pattern: str | None = None,
    validate_base: bool = True,
    validate_profiles: bool = True,
    validate_catalogue: Literal[True] = True,
) -> list[tuple[RecordCatalogue, Path]]: ...


def parse_records(
    logger: logging.Logger,
    search_path: Path,
    glob_pattern: str | None = None,
    validate_base: bool = True,
    validate_profiles: bool = True,
    validate_catalogue: bool = False,
) -> list[tuple[Record | RecordCatalogue, Path]]:
    """
    Try to create Records from record configurations within a directory.

    Records are validated against base metadata library requirements by default (including profiles), and optionally
    against catalogue specific requirements if appropriate (as some tasks work with records before they'll validate).

    If needed, profiles validation can be disabled. Invalid records are skipped with a warning.

    Valid records are checked for unsupported content but will not be skipped if present.

    Records are returned as a list of (RecordClass, Path) tuples, where 'Path' is the Path to the source file.
    """
    RecordClass = RecordCatalogue if validate_base else Record  # noqa: N806
    records: list[tuple[Record, Path]] = []

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

        if not Record._config_supported(config=config, logger=logger):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append((record, config_path))

    logger.info(f"Discovered {len(records)} valid records")
    if validate_catalogue:
        return cast(list[tuple[RecordCatalogue, Path]], records)  # ty:ignore[invalid-return-type]
    return records


def _parse_record_reference(reference: str) -> str:
    """
    Try to parse flexible reference into a record file identifier.

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
    reference = re.sub(r"^[-*]\s+", "", reference.strip())

    if "https://" in reference:
        # for:
        # -> 'https://example.com/items/123' or
        # -> 'https://example.com/items/123/' or
        # -> 'https://example.com/items/123/index.html' or
        # -> 'https://example.com/items/123/index.html#tab-foo'
        # as '123'
        fid_clean = re.sub(r"(index\.html.*|[#?].*)$", "", reference)
        return fid_clean.rstrip("/").split("/")[-1]

    if ".json" in reference:
        # for '123.json' as '123'
        return reference.replace(".json", "")

    # for a UUIDv4 string
    if re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        reference,
    ):
        return reference

    msg = f"Cannot parse reference '{reference}'"
    raise ValueError(msg) from None


def process_record_references(logger: logging.Logger, references: Collection[str]) -> set[str]:
    """
    Process multiple record references into record file identifiers.

    Values can be made up of one or more references separated by commas and/or spaces.
    References within selections that cannot be parsed are skipped with an error.
    """
    file_identifiers = set()
    for selection in references:
        # split identifiers by commas and/or spaces
        selections = re.split(r"[\s,]+", selection)
        for reference in selections:
            try:
                file_identifiers.add(_parse_record_reference(reference))
            except ValueError:
                logger.warning(f"Could not process '{reference}' as a file identifier, skipping.")
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


def pick_local_records(logger: logging.Logger, records: list[Record]) -> list[Record]:
    """Pick one or more local records from a list."""
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


def pick_local_record(logger: logging.Logger, records: list[Record]) -> Record:
    """Pick a local record from a list."""
    choices = {
        f"{r.file_identifier} ('{r.identification.title}' {r.hierarchy_level.value})": r.file_identifier
        for r in records
    }
    logger.debug(f"Choices: {list(choices.keys())}")

    selection = inquirer.list_input(message="Records", choices=list(choices.keys()))
    logger.debug(f"Selected: {selection}")

    for r in records:
        if r.file_identifier in selection:
            logger.info(f"Selected record: {r.file_identifier}")
            return r
    raise KeyError() from None


def get_record(logger: logging.Logger, cat: BasCatalogue, reference: str, branch: str | None = None) -> Record:
    """Get record from catalogue repo using flexible reference."""
    file_identifier = next(iter(process_record_references(logger=logger, references=[reference])))
    return cat.repo.select_one(file_identifier=file_identifier, branch=branch, cached=False)


def load_record(
    logger: logging.Logger, ref: tuple[str, Path | None], cat: BasCatalogue, branch: str | None = None
) -> Record:
    """Load a record from a store by its identifier or from a local file path."""
    if isinstance(ref[1], Path):
        with ref[1].open(mode="r") as f:
            return Record.loads(json.load(f))
    return get_record(logger=logger, cat=cat, reference=ref[0], branch=branch)


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
