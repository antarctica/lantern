from argparse import ArgumentParser
from pathlib import Path

import inquirer
from tasks._record_utils import confirm_source, dump_records, init, process_record_selections


def _get_cli_args() -> dict:
    """
    Get optional command line arguments.

    Missing arguments will be prompted for interactively and return as None here.
    """
    parser = ArgumentParser(description="Copy records from cache to import directory for editing.")
    parser.add_argument(
        "ids",
        nargs="?",
        type=str,
        help="Optional record identifiers (file identifiers, URLs, and/or file names). Will interactively prompt if missing.",
    )
    return {"ids": parser.parse_args().ids}


def _get_args(cli_identifiers: str | None) -> list[str]:
    """Get record identifiers interactively."""
    identifiers = []

    if cli_identifiers:
        print("Record identifiers from command line arguments:")
        print(f"> {cli_identifiers}")
        if not inquirer.prompt([inquirer.Confirm("continue", message="Add others?", default=False)])["continue"]:
            return [cli_identifiers]

    print("Record identifiers can be URLs, file names, or bare identifiers with optional markdown formatting.")
    print("Multiple record identifiers can be given together separated by commas and/or spaces.")
    print("To cancel selecting additional records, enter a blank value.")
    print("Examples:")
    print("> 'https://example.com/items/123/index.html#tab-info'")
    print("> 'https://example.com/items/123/index.html'")
    print("> 'https://example.com/items/123/'")
    print("> 'https://example.com/items/123'")
    print("> '123.json'")
    print("> '123'")
    print("> '123,https://example.com/items/123/,...'")
    print("> '123, https://example.com/items/123/, ...'")
    print("> '123 https://example.com/items/123/ ...'")
    print("> '- https://example.com/items/123'")
    print("> '* https://example.com/items/123'")

    while True:
        answers = inquirer.prompt(
            [
                inquirer.Text("identifiers", message="Record identifier(s)", default=""),
                inquirer.Confirm("continue", message="Add another?", default=False),
            ]
        )
        # abort by cancelling
        if answers["identifiers"].strip() == "":
            break

        identifiers.append(answers["identifiers"].strip())

        # abort by not continuing
        if not answers["continue"]:
            break

    return identifiers


def _confirm_selection(file_identifiers: set[str]) -> bool:
    """Confirm the selected file identifiers with the user."""
    if len(file_identifiers) == 0:
        print("No records selected, aborting.")
        return False

    print("Selected records:")
    for file_identifier in file_identifiers:
        print(f"- {file_identifier}")

    answers = inquirer.prompt(
        [
            inquirer.Confirm("confirm", message="Confirm selection?", default=True),
        ]
    )
    return answers["confirm"]


def main() -> None:
    """Entrypoint."""
    logger, _config, store, _s3, _keys = init()

    confirm_source(logger=logger, store=store, action="Selecting records from")
    args = _get_cli_args()
    identifiers = _get_args(cli_identifiers=args.get("ids", None))

    file_identifiers = process_record_selections(logger=logger, identifiers=identifiers)
    if not _confirm_selection(file_identifiers):
        logger.info("Selection rejected by user.")
        return

    import_path = Path("./import")
    logger.info("Loading records from Store")
    records = store.select(file_identifiers=file_identifiers)

    logger.info(f"Dumping {len(file_identifiers)} selected records from '{store._source.ref}' in Store")
    dump_records(logger=logger, output_path=import_path, records=records)
    logger.info(f"{len(file_identifiers)} records in {import_path.resolve()} for editing.")


if __name__ == "__main__":
    main()
