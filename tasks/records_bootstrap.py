import logging
import sys
from pathlib import Path

import inquirer

from lantern.config import Config
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.stores.base import Store
from lantern.stores.gitlab import GitLabStore
from tasks.records_import import magic_collection_ids

max_stage = 3


def _dump_records(logger: logging.Logger, file_identifiers: list[str], store: Store, output_path: Path) -> None:
    """Dump selected records from the store to a path."""
    output_path.mkdir(parents=True, exist_ok=True)
    for file_identifier in file_identifiers:
        record_path = output_path / f"{file_identifier}.json"
        record = store.get(file_identifier)
        logger.debug(f"Writing {record_path.resolve()}")
        with record_path.open(mode="w") as f:
            f.write(record.dumps_json())


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
    print("Set `LANTERN_STORE_GITLAB_TOKEN` and `LANTERN_STORE_GITLAB_PROJECT_ID` in the `.env` to a working remote")
    print("Records for MAGIC collections used during record import need stashing from a working remote.")
    print(f"Confirm this GitLab project ID is an existing/working project: {config.STORE_GITLAB_PROJECT_ID}")
    _confirm(logger)

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )
    store.populate()

    logger.info("Dumping required collection records from existing store")
    _dump_records(logger, magic_collection_ids, store, working_path)
    logger.info(f"{len(magic_collection_ids)} records stashed in {working_path.resolve()}.")

    print(f"Stage {stage} complete.")
    print("Set `LANTERN_STORE_GITLAB_TOKEN` and `LANTERN_STORE_GITLAB_PROJECT_ID` in the `.env` to the new remote.")
    _confirm(logger)

    print(f"Re-run this script and select Stage {stage + 1}.")
    sys.exit(0)


def stage1(logger: logging.Logger, config: Config, working_path: Path) -> None:
    """Load required records into new store."""
    stage = 1
    print(f"This is stage {stage} [{stage + 1}/{max_stage}].")
    print("Ensure you have completed previous stages.")
    _confirm(logger)

    print(f"Confirm this GitLab project ID is the new project: {config.STORE_GITLAB_PROJECT_ID}")
    _confirm(logger)

    print("This stage is NOT idempotent and will fail if re-run.")
    _confirm(logger)

    answers = inquirer.prompt(
        [
            inquirer.Text(name="author_name", message="Committer name"),
            inquirer.Text(name="author_email", message="Committer email"),
        ]
    )

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )

    data = {
        "branch": "main",
        "commit_message": "Initialising records repository.",
        "author_name": answers["author_name"],
        "author_email": answers["author_email"],
        "actions": [],
    }

    for record_path in working_path.glob("*.json"):
        with record_path.open(mode="r") as f:
            content = f.read()
        data["actions"].append(
            {
                "action": "create",
                "file_path": store._get_remote_hashed_path(record_path.name),
                "content": content,
            }
        )

    logger.info(f"Committing {len(data['actions'])} records.")
    store._project.commits.create(data)

    print(f"Stage {stage} complete.")
    print(f"Re-run this script and select Stage {stage + 1}.")
    sys.exit(0)


# noinspection PyProtectedMember
def stage2(logger: logging.Logger, config: Config) -> None:
    """Create local cache from new remote project."""
    stage = 2
    print(f"This is stage {stage} [{stage + 1}/{max_stage}].")
    print("Ensure you have completed previous stages.")
    _confirm(logger)

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )

    if store._cache._exists:
        print(f"Local cache path {config.STORE_GITLAB_CACHE_PATH.resolve()} exists and needs purging.")
        store._cache.purge()

    store.populate()

    print(f"Stage {stage} complete.")
    print("All stages complete.")
    sys.exit(0)


def main() -> None:
    """Entrypoint."""
    config = Config()
    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    print("This script is for bootstrapping new GitLab stores.")
    print("It requires an existing/working store to copy required records from.")
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
        stage1(logger, config, import_path)
    elif answers["stage"] == "stage2":
        stage2(logger, config)
    else:
        logger.error(f"Unknown stage '{answers['stage']}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
