# Push records into store as a changeset

import logging
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import clean_record_configs, init, parse_records

from lantern.catalogues.bas import BasCatalogue
from lantern.models.record.record import Record
from lantern.models.repository import GitUpsertContext, GitUpsertResults
from lantern.repositories.bas import ProtectedGitBranchError


def _get_cli_args() -> tuple[bool, Path, str | None, str | None, str | None, str | None, str | None]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Commit records from import directory to store.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force selection of branch and commit CLI arguments.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to import records from. Will use default if omitted.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        type=str,
        default=None,
        help="Optional Git branch/ref to push records to. Will prompt or use default if omitted.",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        help="Optional commit title. Will prompt if omitted.",
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        help="Optional commit message. Will prompt if omitted.",
    )
    parser.add_argument(
        "--author-name",
        "-an",
        type=str,
        help="Optional commit author name. Will prompt if omitted.",
    )
    parser.add_argument(
        "--author-email",
        "-ae",
        type=str,
        help="Optional commit author email address. Will prompt if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.path, args.branch, args.title, args.message, args.author_name, args.author_email


def get_default_author() -> tuple[str | None, str | None]:
    """Try to get default author identity from Git config."""
    name = subprocess.check_output(["git", "config", "--get", "user.name"]).decode().strip()  # noqa: S607
    email = subprocess.check_output(["git", "config", "--get", "user.email"]).decode().strip()  # noqa: S607
    return name, email


def get_git_commit_context(defaults: GitUpsertContext | None = None, branch: str | None = None) -> GitUpsertContext:
    """Prompt for commit context."""
    default_name, default_email = get_default_author()

    branch = branch if branch else defaults.branch if defaults else None
    title = defaults.title if defaults else None
    message = defaults.message if defaults else None
    author_name = defaults.author_name if defaults and defaults.author_name else default_name if default_name else None
    author_email = (
        defaults.author_email if defaults and defaults.author_email else default_email if default_email else None
    )

    return GitUpsertContext(
        branch=inquirer.text(message="Branch", default=branch),
        title=inquirer.text(message="Changeset title", default=title),
        message=message if message else inquirer.editor(message="Changeset message"),
        author_name=inquirer.text(message="Changeset author name", default=author_name),
        author_email=inquirer.text(message="Changeset author email", default=author_email),
    )


def _get_args(
    logger: logging.Logger, cli_args: tuple[bool, Path, str | None, str | None, str | None, str | None, str | None]
) -> tuple[Path, GitUpsertContext]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_path, cli_branch, cli_title, cli_message, cli_author_name, cli_author_email = cli_args

    path = cli_path
    context = GitUpsertContext(
        branch=cli_branch,
        title=cli_title if cli_title else "",
        message=cli_message if cli_message else "",
        author_name=cli_author_name if cli_author_name else "",
        author_email=cli_author_email if cli_author_email else "",
    )

    if not cli_force:
        path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=path))
        context = get_git_commit_context(context)

    msg = "Import path, branch and commit details MUST be set or have Git config defaults (for author identity) for this task."
    if not isinstance(path, Path):
        raise TypeError(msg) from None
    if not context.branch:
        raise ValueError(msg) from None
    if not context.title:
        raise ValueError(msg) from None
    if not context.message:
        raise ValueError(msg) from None
    if not context.author_name:
        raise ValueError(msg) from None
    if not context.author_email:
        raise ValueError(msg) from None

    logger.debug(context)
    return path, context


def load(logger: logging.Logger, import_path: Path) -> dict[Path, Record]:
    """
    Load valid records from import path.

    Records must pass catalogue validation.

    Returned as a dict of {RecordPath: Record} to allow targeted clean-up later.
    """
    logger.info(f"Loading records from: '{import_path.resolve()}'")
    records: list[tuple[Record, Path]] = parse_records(logger=logger, search_path=import_path, validate_catalogue=True)
    logger.info(f"Loaded {len(records)} valid records from '{import_path.resolve()}'.")
    return {path: record for record, path in records}


def push(
    logger: logging.Logger, cat: BasCatalogue, records: list[Record], commit_context: GitUpsertContext
) -> GitUpsertResults:
    """
    Prepare and apply a commit.

    Higher-level tasks SHOULD call this method to incorporate importing records.
    """
    try:
        results = cat.commit(records=records, context=commit_context)
    except ProtectedGitBranchError:
        logger.exception(f"Aborting. Cannot commit to default branch '{cat.repo.gitlab_default_branch}'.")
        sys.exit(1)
    if results.commit is None:
        return results

    logger.info(f"{len(results.new_identifiers) + len(results.updated_identifiers)} records imported")
    logger.info(f"Commit: {cat.repo.gitlab_project_url}/-/commit/{results.commit}")
    return results


def clean(logger: logging.Logger, records: dict[Path, Record], results: GitUpsertResults) -> None:
    """Clean up input path."""
    clean_record_configs(
        logger=logger, records=records, file_identifiers=results.new_identifiers + results.updated_identifiers
    )


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()

    cli_args = _get_cli_args()
    import_path, commit_context = _get_args(logger=logger, cli_args=cli_args)

    records = load(logger=logger, import_path=import_path)
    commit = push(logger=logger, cat=catalogue, records=list(records.values()), commit_context=commit_context)
    clean(logger=logger, records=records, results=commit)


if __name__ == "__main__":
    main()
