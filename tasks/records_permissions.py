import json
import logging
import sys
from collections.abc import Generator
from pathlib import Path

import inquirer
from environs import Env
from jwskate import Jwk

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.administration import Administration, Permission
from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.utils.admin import (
    AdministrationKeys,
    AdministrativeMetadataSubjectMismatchError,
    get_admin,
    set_admin,
)
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.item.base.enums import AccessLevel


def _parse_configs(search_path: Path) -> Generator[dict, None, None]:
    """
    Try to load any record configurations from JSON files from a directory.

    Subdirectories are NOT searched.
    """
    for json_path in search_path.glob("*.json"):
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
        except RecordInvalidError as e:
            logger.warning(f"Record '{config['file_identifier']}' does not validate, skipping.")
            logger.info(e.validation_error)
            continue
        if not Record._config_supported(config=config, logger=logger):
            logger.warning(
                f"Record '{config['file_identifier']}' contains unsupported content the catalogue will ignore."
            )
        records.append(record)
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _get_args(logger: logging.Logger, records: list[Record]) -> tuple[list[Record], Permission | None]:
    """Get user input."""
    choices = {
        f"{r.file_identifier} ('{r.identification.title}' {r.hierarchy_level.value})": r.file_identifier
        for r in records
    }
    levels = [al.name for al in AccessLevel]
    levels.remove(AccessLevel.NONE.name)
    levels.remove(AccessLevel.UNKNOWN.name)
    logger.debug(f"Choices: {list(choices.keys())}")
    logger.debug(f"Levels: {levels}")

    answers = inquirer.prompt(
        [
            inquirer.Checkbox(
                "selections",
                message="Records",
                choices=list(choices.keys()),
            ),
            inquirer.List("level", message="Access level", choices=levels),
            inquirer.Text("comment", message="Comment (Optional)", default=""),
        ]
    )

    records_ = {r.file_identifier: r for r in records}
    selected_fids = [choices[k] for k in answers["selections"]]
    logger.info(f"Selected records: {selected_fids}")
    selected_records = [records_[fid] for fid in selected_fids]

    permission = None
    if answers["level"] == AccessLevel.PUBLIC.name:
        permission = OPEN_ACCESS
    elif answers["level"] == AccessLevel.BAS_STAFF.name:
        permission = BAS_STAFF
    if permission and answers["comment"] != "":
        permission.comment = answers["comment"]
    logger.info(f"Selected permission: {permission}")

    return selected_records, permission


def _set_permission(
    logger: logging.Logger, keys: AdministrationKeys, records: list[Record], permission: Permission
) -> None:
    """Set single access permission in records, overwriting any possible existing permissions."""
    for record in records:
        admin = None
        try:
            admin = get_admin(keys=keys, record=record)
        except AdministrativeMetadataSubjectMismatchError as e:
            # prompt user whether to ignore mismatch by clearing existing admin metadata
            if inquirer.confirm(
                message=(
                    "Existing administrative metadata references the wrong record. Drop existing metadata (if record is cloned)?"
                ),
                default=False,
            ):
                pass
            else:
                raise e from e
        if admin is None:
            admin = Administration(id=record.file_identifier)
        admin.access_permissions = [permission]
        logger.debug(f"Setting access permissions for '{record.file_identifier}' as: {permission}")
        set_admin(keys=keys, record=record, admin_meta=admin)


def _dump_records(logger: logging.Logger, records: list[Record], output_path: Path) -> None:
    """Dump selected records from the store to a path."""
    output_path.mkdir(parents=True, exist_ok=True)
    for record in records:
        record_path = output_path / f"{record.file_identifier}.json"
        logger.debug(f"Writing {record_path.resolve()}")
        with record_path.open(mode="w") as f:
            f.write(record.dumps_json(strip_admin=False))


def main() -> None:
    """Entrypoint."""
    env = Env()  # needed for loading private signing key for admin metadata
    env.read_env()
    config = Config()

    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    admin_keys = AdministrationKeys(
        encryption_private=config.ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE,
        signing_private=Jwk(env.json("X_ADMIN_METADATA_SIGNING_KEY_PRIVATE")),
        signing_public=config.ADMIN_METADATA_SIGNING_KEY_PUBLIC,
    )

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    records = _parse_records(logger=logger, search_path=input_path)
    selected_records, permission = _get_args(logger=logger, records=records)
    if not permission:
        logger.info("No permission selected, aborting.")
        sys.exit(0)

    _set_permission(logger=logger, keys=admin_keys, records=selected_records, permission=permission)
    _dump_records(logger=logger, records=selected_records, output_path=input_path)


if __name__ == "__main__":
    main()
