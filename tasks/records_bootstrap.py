import logging
import sys
from itertools import chain
from pathlib import Path

import inquirer
from tasks._record_utils import init, init_store
from tasks.records_zap import magic_collection_ids

from lantern.config import Config
from lantern.stores.base import Store

max_stage = 3


def _dump_records(logger: logging.Logger, file_identifiers: list[str], store: Store, output_path: Path) -> None:
    """Dump selected records from the store to a path as JSON and XML."""
    output_path.mkdir(parents=True, exist_ok=True)
    for file_identifier in file_identifiers:
        record = store.get(file_identifier)

        record_path_json = output_path / f"{file_identifier}.json"
        logger.debug(f"Writing {record_path_json.resolve()}")
        with record_path_json.open(mode="w") as f:
            f.write(record.dumps_json(strip_admin=False))

        record_path_xml = output_path / f"{file_identifier}.xml"
        logger.debug(f"Writing {record_path_xml.resolve()}")
        with record_path_xml.open(mode="w") as f:
            f.write(record.dumps_xml(strip_admin=False))


def _confirm(logger: logging.Logger) -> None:
    """Confirm user wants to proceed."""
    answers = inquirer.prompt(
        [
            inquirer.Confirm(name="confirm", message="Ready?", default=True),
        ]
    )
    if not answers["confirm"]:
        logger.info("Cancelled by the user.")
        sys.exit(1)


def _stage0(logger: logging.Logger, config: Config, working_path: Path) -> None:
    """Save required records from existing store."""
    stage = 0
    print(f"This is stage {stage} [{stage + 1}/{max_stage}].")
    print("Records for MAGIC collections used during record import need stashing from a working remote.")
    print(
        "ACTION: Set `LANTERN_STORE_GITLAB_ENDPOINT`, `LANTERN_STORE_GITLAB_TOKEN` and `LANTERN_STORE_GITLAB_PROJECT_ID` in `.env` to a working remote."
    )
    print(
        f"Confirm this GitLab project ID is an existing/working project: {config.STORE_GITLAB_PROJECT_ID} ({config.STORE_GITLAB_ENDPOINT})"
    )
    _confirm(logger)

    store = init_store(logger=logger, config=config)
    store.populate()

    logger.info("Dumping required collection records from existing store")
    _dump_records(logger, magic_collection_ids, store, working_path)
    logger.info(f"{len(magic_collection_ids)} records stashed in {working_path.resolve()}.")

    print(f"Stage {stage} complete.")
    print(
        "ACTION: Set `LANTERN_STORE_GITLAB_ENDPOINT`, `LANTERN_STORE_GITLAB_TOKEN` and `LANTERN_STORE_GITLAB_PROJECT_ID` in `.env` to the new remote."
    )
    _confirm(logger)

    print(f"ACTION: Re-run this script and select Stage {stage + 1}.")
    sys.exit(0)


def _stage1(logger: logging.Logger, config: Config, working_path: Path) -> None:
    """Load required records into new store."""
    stage = 1
    print(f"This is stage {stage} [{stage + 1}/{max_stage}].")
    print("Confirm you have completed previous stages.")
    _confirm(logger)

    print(
        f"Confirm this GitLab project ID is the new project: {config.STORE_GITLAB_PROJECT_ID}  ({config.STORE_GITLAB_ENDPOINT})"
    )
    _confirm(logger)

    print("Confirm this stage is NOT idempotent and will fail if re-run.")
    _confirm(logger)

    answers = inquirer.prompt(
        [
            inquirer.Text(name="author_name", message="Committer name"),
            inquirer.Text(name="author_email", message="Committer email"),
        ]
    )

    store = init_store(logger=logger, config=config)

    data = {
        "branch": "main",
        "commit_message": "Initialising records repository.",
        "author_name": answers["author_name"],
        "author_email": answers["author_email"],
        "actions": [],
    }

    for record_path in chain(working_path.glob("*.json"), working_path.glob("*.xml")):
        with record_path.open(mode="r") as f:
            content = f.read()
        data["actions"].append(  # ty: ignore[possibly-missing-attribute]
            {
                "action": "create",
                "file_path": store._get_remote_hashed_path(record_path.name),
                "content": content,
            }
        )

    logger.info(f"Committing {len(data['actions'])} records.")
    store.project.commits.create(data)

    for record_path in chain(working_path.glob("*.json"), working_path.glob("*.xml")):
        if record_path.exists():
            record_path.unlink()

    print(f"Stage {stage} complete.")
    print(f"ACTION: Re-run this script and select Stage {stage + 1}.")
    sys.exit(0)


# noinspection PyProtectedMember
def _stage2(logger: logging.Logger, config: Config) -> None:
    """Create local cache from new remote project."""
    stage = 2
    print(f"This is stage {stage} [{stage + 1}/{max_stage}].")
    print("Confirm you have completed previous stages.")
    _confirm(logger)

    if config.STORE_GITLAB_BRANCH != "main":
        print("Selected branch is not 'main', this is unusual.")
        _confirm(logger)

    store = init_store(logger=logger, config=config)
    if store._cache.exists:
        print(f"Local cache path {config.STORE_GITLAB_CACHE_PATH.resolve()} exists and needs purging.")
        store._cache.purge()
    store.populate()

    print(f"Stage {stage} complete.")
    print("All stages complete.")
    sys.exit(0)


def main() -> None:
    """Entrypoint."""
    logger, config, _store, _s3, _keys = init()

    print("This script is for bootstrapping new GitLab stores.")
    print("It requires an existing/working remote to copy required records from and a new, empty, remote to copy to.")
    print(f"It has {max_stage} stages.\n")

    import_path = Path("./import")
    answers = inquirer.prompt(
        [
            inquirer.List(
                name="stage",
                message="Select stage",
                choices=[
                    ("Stage 0 - Stash records from existing store.", "stage0"),
                    ("Stage 1 - Load stashed records into new store, bypassing cache.", "stage1"),
                    ("Stage 2 - Create local cache from new store.", "stage2"),
                ],
            ),
        ]
    )
    if answers["stage"] == "stage0":
        _stage0(logger, config, import_path)
    elif answers["stage"] == "stage1":
        _stage1(logger, config, import_path)
    elif answers["stage"] == "stage2":
        _stage2(logger, config)
    else:
        logger.error(f"Unknown stage '{answers['stage']}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
