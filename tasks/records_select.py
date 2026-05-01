# Pull records from store

import logging
from argparse import ArgumentParser
from pathlib import Path

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import dump_records, get_gitlab_source, init, process_record_references

from lantern.catalogues.bas import BasCatalogue


def _get_cli_args() -> tuple[bool, Path, str | None, set[str]]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Copy records from store to import directory for editing.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force save path and branch to defaults, and selection of records to CLI argument.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=Path("./import"),
        help="Directory to save records to. Will use default if omitted.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        type=str,
        default=None,
        help="Optional Git branch/ref to read records from. Will prompt or use default if omitted.",
    )
    parser.add_argument(
        "records",
        nargs="*",
        help="Optional record reference(s) as positional arguments (file identifier, URL, or file name).",
    )
    parser.add_argument(
        "--record",
        action="append",
        help="Optional record reference (file identifier, URL, or file name). Can be repeated.",
    )
    args = parser.parse_args()
    records = set(list(args.records or []) + list(args.record or []))
    return args.force, args.path, args.branch, records


def _get_args(
    logger: logging.Logger,
    cat: BasCatalogue,
    cli_args: tuple[bool, Path, str | None, set[str]],
) -> tuple[Path, str, set[str]]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_path, cli_branch, cli_references = cli_args

    path = cli_path
    branch = cli_branch if cli_branch else cat.repo.gitlab_default_branch
    references = cli_references

    if cli_force:
        return path, branch, references

    path = Path(inquirer.path("Import path", path_type=InquirerPath.DIRECTORY, exists=True, default=path))
    branch = get_gitlab_source(logger=logger, cat=cat, action="Fetching records from")

    if cli_references:
        logger.info("Record references from command line arguments:")
        logger.info(f"{cli_references}")
        if not inquirer.confirm(message="Add others?", default=False):
            return path, branch, references

    message = [
        "Record references can be URLs, file names, or bare identifiers with optional markdown formatting.",
        "Multiple record references can be given together separated by commas and/or spaces.",
        "To cancel selecting additional records, enter a blank value.",
        "Examples:",
        "> 'https://example.com/items/123/index.html#tab-info'",
        "> 'https://example.com/items/123/index.html'",
        "> 'https://example.com/items/123/'",
        "> 'https://example.com/items/123'",
        "> '123.json'",
        "> '123'",
        "> '123,https://example.com/items/123/,...'",
        "> '123, https://example.com/items/123/, ...'",
        "> '123 https://example.com/items/123/ ...'",
        "> '- https://example.com/items/123'",
        "> '* https://example.com/items/123'",
    ]
    for msg in message:
        logger.info(msg)

    while True:
        answers = inquirer.prompt(
            [
                inquirer.Text("references", message="Record reference(s)", default=""),
                inquirer.Confirm("continue", message="Add another?", default=False),
            ]
        )
        # abort by cancelling
        if answers["references"].strip() == "":
            break

        references.add(answers["references"].strip())

        # abort by not continuing
        if not answers["continue"]:
            break

    return path, branch, references


def confirm_selection(logger: logging.Logger, cli_force: bool, file_identifiers: set[str]) -> bool:
    """Confirm the selected file identifiers with the user."""
    if len(file_identifiers) == 0:
        logger.info("No records selected, aborting.")
        return False
    if cli_force:
        logger.info("CLI selection forced, skipping interactive selection and conformation.")
        return True

    logger.info("Selected records:")
    for file_identifier in file_identifiers:
        logger.info(f"- {file_identifier}")
    return inquirer.confirm(message="Confirm selection?", default=True)


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()

    cli_args = _get_cli_args()
    import_path, branch, references = _get_args(logger=logger, cat=catalogue, cli_args=cli_args)

    file_identifiers = process_record_references(logger=logger, references=references)
    if not confirm_selection(logger=logger, cli_force=cli_args[0], file_identifiers=file_identifiers):
        logger.info("Selection rejected by user.")
        return

    logger.info("Loading records from Store")
    records = catalogue.repo.select(branch=branch, file_identifiers=file_identifiers)

    logger.info(f"Dumping {len(file_identifiers)} selected records from '{branch}' in GitLab store")
    dump_records(logger=logger, output_path=import_path, records=records)
    logger.info(f"{len(file_identifiers)} records in {import_path.resolve()} for editing.")


if __name__ == "__main__":
    main()
