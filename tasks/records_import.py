import logging
from pathlib import Path

import inquirer
from tasks._record_utils import clean_configs, confirm_source, init, parse_records

from lantern.config import Config
from lantern.models.record.record import Record
from lantern.stores.gitlab import CommitResults
from lantern.stores.gitlab_cache import GitLabCachedStore


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


def load(logger: logging.Logger, input_path: Path) -> dict[Path, Record]:
    """
    Load valid records from input path.

    Records must pass catalogue validation.

    Returned as a dict of {RecordPath: Record} to allow targeted clean-up later.
    """
    logger.info(f"Loading records from: '{input_path.resolve()}'")
    records: list[tuple[Record, Path]] = parse_records(logger=logger, search_path=input_path, validate_catalogue=True)  # ty:ignore[invalid-assignment]
    logger.info(f"Loaded {len(records)} valid records from '{input_path.resolve()}'.")
    return {path: record for record, path in records}


def push(logger: logging.Logger, config: Config, store: GitLabCachedStore, records: list[Record]) -> CommitResults:
    """
    Prepare and apply a commit.

    Higher-level tasks SHOULD call this method to incorporate importing records.
    """
    confirm_source(logger=logger, store=store, action="Committing records to")
    title, message, author_name, author_email = _get_args()
    store._cache._ensure_exists()  # to ensure cache is populated and check if any files are updates
    results = store.push(records=records, title=title, message=message, author=(author_name, author_email))
    if results.commit is None:
        return results

    logger.info(f"{len(results.new_identifiers) + len(results.updated_identifiers)} records imported")
    logger.info(f"Commit: {config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{results.commit}")
    return results


def clean(logger: logging.Logger, records: dict[Path, Record], commit: CommitResults) -> None:
    """Clean up input path."""
    clean_configs(logger=logger, records=records, file_identifiers=commit.new_identifiers + commit.updated_identifiers)


def main() -> None:
    """Entrypoint."""
    logger, config, store, _s3 = init()
    input_path = Path("./import")

    records = load(logger=logger, input_path=input_path)
    commit = push(logger=logger, config=config, store=store, records=list(records.values()))
    clean(logger=logger, records=records, commit=commit)


if __name__ == "__main__":
    main()
