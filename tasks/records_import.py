import json
import logging
import sys
from collections.abc import Generator
from pathlib import Path

import inquirer

from lantern.config import Config
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.stores.gitlab import GitLabStore


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


def _clean_input_path(input_path: Path) -> None:
    """Remove imported files."""
    for json_path in input_path.glob("*.json"):
        json_path.unlink(missing_ok=True)


def _get_args() -> tuple[str, str, str, str]:
    """Get user input."""
    answers = inquirer.prompt(
        [
            inquirer.Text("title", message="Changeset summary"),
            inquirer.Editor("message", message="Changeset detail"),
            inquirer.Text("name", message="Author name", default="Felix Fennell"),
            inquirer.Text("email", message="Author email", default="felnne@bas.ac.uk"),
        ]
    )
    return answers["title"], answers["message"], answers["name"], answers["email"]


def main() -> None:
    """Entrypoint."""
    config = Config()
    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        branch=config.STORE_GITLAB_BRANCH,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )

    input_path = Path("./import")
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    logger.info(f"Committing records to branch: {store._branch}.")
    answers = inquirer.prompt(
        [
            inquirer.Confirm(name="confirm", message="Confirm target branch?", default=True),
        ]
    )
    if not answers["confirm"]:
        logger.info("Cancelled by the user.")
        sys.exit(1)
    title, message, author_name, author_email = _get_args()
    store.populate()
    records = _parse_records(logger=logger, search_path=input_path)
    store.push(records=records, title=title, message=message, author=(author_name, author_email))
    _clean_input_path(input_path=input_path)


if __name__ == "__main__":
    main()
