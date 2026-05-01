# Generate and export catalogue site

import logging
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import get_args

import inquirer
from tasks._shared import ExportTarget, init, process_record_references

from lantern.catalogues.bas import BasCatalogue
from lantern.exporters.local import LocalExporter
from lantern.models.site import SiteEnvironment
from lantern.outputs.base import OutputBase


def _get_cli_args() -> tuple[bool, str | None, ExportTarget, SiteEnvironment, set[str]]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Generate and upload content for selected records and wider static site.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force branch to set value or default, and selection of records to CLI argument or all.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        type=str,
        default=None,
        help="Optional Git branch/ref to read records from. Will prompt or use default if omitted.",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=str,
        default="remote",
        choices=get_args(ExportTarget),
        help="Optional export target for outputs. Will use default if omitted.",
    )
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        default="testing",
        choices=get_args(SiteEnvironment),
        help="Optional site environment to use if export target is remote. Will use default if omitted.",
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
    return args.force, args.branch, args.target, args.env, records


def _get_args(
    logger: logging.Logger,
    cat: BasCatalogue,
    cli_args: tuple[bool, str | None, ExportTarget, SiteEnvironment, set[str]],
) -> tuple[SiteEnvironment, ExportTarget, str, set[str]]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_branch, cli_target, cli_env, cli_references = cli_args

    env = cli_env
    target = cli_target
    branch = cli_branch if cli_branch else cat.repo.gitlab_default_branch
    identifiers = process_record_references(logger=logger, references=cli_references)

    if cli_force:
        return env, target, branch, identifiers

    env = inquirer.list_input(message="Site environment (testing/live)", choices=get_args(SiteEnvironment), default=env)
    target = inquirer.list_input(message="Export target (local/remote)", choices=get_args(ExportTarget), default=target)
    branch = inquirer.text(message="Branch", default=branch)

    if identifiers:
        logger.info("Record identifiers from command line arguments:")
        logger.info(f"{identifiers}")
        logger.info("Note: Any empty set is allowed and will select all records.")
        if not inquirer.confirm(message="Add others?", default=False):
            return env, target, branch, identifiers

    references = set()
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
    identifiers = identifiers.union(process_record_references(logger=logger, references=references))

    return env, target, branch, identifiers


def export(
    cat: BasCatalogue,
    env: SiteEnvironment,
    target: ExportTarget,
    branch: str,
    identifiers: set[str],
    outputs: list[type[OutputBase]] | None = None,
) -> None:
    """Run catalogue export, optionally overloading exporter."""
    if target == "local":
        cat._envs[env]._untrusted._exporter = LocalExporter(logger=cat._logger, path=Path("export"))
        cat._envs[env]._trusted._exporter = LocalExporter(logger=cat._logger, path=Path("export-trusted"))
    cat.export(env=env, identifiers=identifiers, branch=branch, outputs=outputs)


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()

    cli_args = _get_cli_args()
    env, target, branch, identifiers = _get_args(logger=logger, cat=catalogue, cli_args=cli_args)

    start = time.monotonic()
    export(cat=catalogue, env=env, target=target, branch=branch, identifiers=identifiers)
    logger.info(f"Exported site in {round(time.monotonic() - start)} seconds.")


if __name__ == "__main__":
    main()
