import json
import logging
from argparse import ArgumentParser
from pathlib import Path

import cattrs
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from tasks._record_utils import confirm_source, init
from tasks.record_clone import _get_record

from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict
from lantern.stores.gitlab import GitLabStore


def _get_cli_args(logger: logging.Logger) -> dict:
    """
    Get optional command line arguments.

    Positional `ref` may be a path to a record config, or an id.
    Setting `--id` or `--path` will take precedence over `ref`.
    Setting `--path` will take precedence over `--id`.
    Setting neither will prompt for a record ID interactively outside this method.
    """
    parser = ArgumentParser(description="Dump administrative metadata from a record.")
    parser.add_argument(
        "ref",
        nargs="?",
        type=str,
        help="Optional positional reference: path to a record config file or an ID.",
    )
    parser.add_argument(
        "--id",
        type=str,
        help="Record identifier (file identifier, URL, or file name). Will interactively prompt if missing.",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to a record configuration file, as an alternative to a record identifier.",
    )
    args = parser.parse_args()

    path = None
    record_id = None

    if args.path is not None:
        path_candidate = Path(args.path)
        if not path_candidate.is_file():
            msg = f"Path to record config file specified but not found at: '{path_candidate.resolve()}'"
            raise FileNotFoundError(msg)
        path = path_candidate
    if args.id is not None:
        record_id = args.id

    if path is None and record_id is None and args.ref is not None:
        ref_candidate = Path(args.ref)
        if ref_candidate.is_file():
            path = ref_candidate
        else:
            record_id = args.ref

    return {"id": record_id, "path": path}


def _load_record(logger: logging.Logger, args: dict, store: GitLabStore) -> Record:
    """Load a record from a store by its identifier or from a local file path."""
    if args["path"] is not None:
        with args["path"].open(mode="r") as f:
            return Record.loads(json.load(f))
    return _get_record(logger=logger, store=store, identifier=args["id"])


def _dumps_admin_meta(logger: logging.Logger, admin_keys: AdministrationKeys, record: Record) -> None:
    """
    Get and display admin metadata.

    Replaces the metadata datestamp, file identifier, catalogue identifier and administrative metadata identifier only.

    Other references to the original record such as other identifiers, citations, etc. are not changed.
    """
    admin_meta = get_admin(keys=admin_keys, record=record)
    if admin_meta is None:
        msg = "Missing administrative metadata in source record."
        raise ValueError(msg) from None
    converter = cattrs.Converter()
    converter.register_unstructure_hook(AdministrationMetadata, lambda d: d.unstructure())
    result = clean_dict(converter.unstructure(admin_meta))
    logger.info("Admin metadata:")
    logger.info(json.dumps(result, indent=2))


def main() -> None:
    """Entrypoint."""
    logger, config, store, _s3 = init()
    confirm_source(logger=logger, store=store, action="Selecting records from")
    args = _get_cli_args(logger)

    record = _load_record(logger=logger, args=args, store=store)
    _dumps_admin_meta(logger=logger, admin_keys=config.ADMIN_METADATA_KEYS, record=record)


if __name__ == "__main__":
    main()
