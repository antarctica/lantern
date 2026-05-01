# Invalidate record specific outputs in CloudFront cache for live site

import logging
from argparse import ArgumentParser
from pathlib import Path

import inquirer
from tasks._shared import init, process_record_references
from tasks.records_select import confirm_selection
from tasks.site_invalidate import get_cf_distribution_id, invalidate_keys


def _get_cli_args() -> tuple[bool, set[str]]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Invalidate cached record exports in the live catalogue.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force selected record references to CLI argument.",
    )
    parser.add_argument(
        "records",
        nargs="*",
        help="Record reference(s) as positional arguments (file identifier, URL, or file name).",
    )
    parser.add_argument(
        "--record",
        action="append",
        help="Record reference (file identifier, URL, or file name). Can be repeated.",
    )
    args = parser.parse_args()
    records = set(list(args.records or []) + list(args.record or []))
    return args.force, records


def _get_args(
    logger: logging.Logger,
    cli_args: tuple[bool, set[str]],
) -> set[str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_references = cli_args

    references = cli_references
    if cli_force:
        return references

    if cli_references:
        logger.info("Record references from command line arguments:")
        logger.info(f"{cli_references}")
        if not inquirer.confirm(message="Add others?", default=False):
            return references

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

    return references


def get_record_invalidation_keys(file_identifiers: set[str]) -> list[str]:
    """
    Generate keys to invalidate within CloudFront distribution based on selected records.

    Includes keys for specific resources (as items and records), and global outputs such as indexes.
    """
    keys = ["/-/index/index.html", "/waf/*"] if file_identifiers else []
    fids = file_identifiers
    keys.extend([f"/items/{fid}/*" for fid in fids] + [f"/records/{fid}/*" for fid in fids])
    return keys


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    cf_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_cf_id")
    cf_replica_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_replica_cf_id")

    cli_args = _get_cli_args()
    references = _get_args(logger=logger, cli_args=cli_args)
    file_identifiers = process_record_references(logger=logger, references=references)
    if not confirm_selection(logger=logger, cli_force=cli_args[0], file_identifiers=file_identifiers):
        logger.info("Selection rejected by user.")
        return

    keys = get_record_invalidation_keys(file_identifiers)
    # apply to primary and replica site distributions
    for cid in [cf_id, cf_replica_id]:
        invalidate_keys(logger=logger, config=config, distribution_id=cid, keys=keys)


if __name__ == "__main__":
    main()
