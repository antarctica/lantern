import logging
import re
from pathlib import Path

import inquirer

from lantern.config import Config
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.stores.base import Store
from lantern.stores.gitlab import GitLabStore


def _get_args() -> list[str]:
    """Get user input for multiple file identifiers."""
    file_identifiers = []

    print("File identifiers can be URLs, file names, or bare identifiers.")
    print("Examples:")
    print("- https://example.com/items/123/index.html#tab-info")
    print("- https://example.com/items/123/index.html")
    print("- https://example.com/items/123/")
    print("- https://example.com/items/123")
    print("- 123.json")
    print("- 123")

    while True:
        answers = inquirer.prompt(
            [
                inquirer.Text("record", message="File Identifier"),
                inquirer.Confirm("continue", message="Add another?", default=False),
            ]
        )
        file_identifiers.append(answers["record"])
        if not answers["continue"]:
            break
    return file_identifiers


def _process_selections(file_identifiers: list[str]) -> None:
    """
    Process file identifiers into bare identifiers.

    Handles common references such as URLs or file names for convenience.
    """
    for i, fid in enumerate(file_identifiers):
        fid = fid.strip()
        if "https://" in fid:
            # for 'https://example.com/items/123' or 'https://example.com/items/123/' or
            # 'https://example.com/items/123/index.html' or 'https://example.com/items/123/index.html#tab-foo'  as '123'
            fid_clean = re.sub(r"(index\.html.*|[#?].*)$", "", fid)
            file_identifiers[i] = fid_clean.rstrip("/").split("/")[-1]
        if ".json" in fid:
            # for '123.json' use '123'
            file_identifiers[i] = fid.replace(".json", "")


def _confirm_selection(file_identifiers: list[str]) -> bool:
    """Confirm the selected file identifiers with the user."""
    print("Selected records:")
    for file_identifier in file_identifiers:
        print(f"- {file_identifier}")

    answers = inquirer.prompt(
        [
            inquirer.Confirm("confirm", message="Confirm selection?", default=True),
        ]
    )
    return answers["confirm"]


def _dump_records(logger: logging.Logger, file_identifiers: list[str], store: Store, output_path: Path) -> None:
    """Dump selected records from the store to a path."""
    output_path.mkdir(parents=True, exist_ok=True)
    for file_identifier in file_identifiers:
        record_path = output_path / f"{file_identifier}.json"
        record = store.get(file_identifier)
        logger.debug(f"Writing {record_path.resolve()}")
        with record_path.open(mode="w") as f:
            f.write(record.dumps_json())


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
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )

    file_identifiers = _get_args()
    _process_selections(file_identifiers)
    if not _confirm_selection(file_identifiers):
        logger.info("Selection rejected by user.")
        return

    import_path = Path("./import")
    logger.info("Loading records from Store")
    store.populate()

    logger.info(f"Dumping {len(file_identifiers)} selected records from Store")
    _dump_records(logger, file_identifiers, store, import_path)
    logger.info(f"{len(file_identifiers)} records in {import_path.resolve()} for editing.")


if __name__ == "__main__":
    main()
