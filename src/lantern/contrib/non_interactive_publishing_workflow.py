import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import get_args

import requests
from boto3 import client as S3Client  # noqa: N812
from gitlab import GitlabGetError

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.lib.metadata_library.models.record.record import RecordInvalidError
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.record.record import Record
from lantern.models.repository import GitUpsertContext, GitUpsertResults
from lantern.models.site import SiteEnvironment
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.stores.base import RecordNotFoundError


@dataclass
class Args:
    """Script arguments."""

    env: SiteEnvironment
    path: Path
    # merge request
    changeset_base: str  # branch
    changeset_title: str
    changeset_message: str
    # commit within changeset
    commit_title: str
    commit_message: str
    author_name: str
    author_email: str
    # other
    webhook: str | None = None


def _parse_records(logger: logging.Logger, search_path: Path) -> dict[Path, Record]:
    """Attempt to load, parse and validate JSON encoded record files."""
    records = {}
    for json_path in search_path.glob("*.json"):
        with json_path.open("r") as f:
            config = json.load(f)
        try:
            record = Record.loads(config)
            record.validate()
        except RecordInvalidError as e:
            logger.exception("Record '%s' does not validate, skipping.", config.get("file_identifier", "<unknown>"))
            logger.exception(e.validation_error)
            continue
        if hasattr(Record, "_config_supported") and not Record._config_supported(config):
            logger.warning(
                "Record '%s' contains unsupported content the catalogue will ignore.",
                config.get("file_identifier", "<unknown>"),
            )
        records[json_path] = record
    logger.info("Discovered %s valid records", len(records))
    return records


def _filter_records(
    logger: logging.Logger, cat: BasCatalogue, branch: str, record_paths: dict[Path, Record]
) -> dict[Path, Record]:
    """Filter out records that have not changed compared to the remote store."""
    records_ = {}
    for _path, record in record_paths.items():
        try:
            existing_record = cat.repo.select_record(file_identifier=record.file_identifier, branch=branch)
            if record.dumps() == existing_record.dumps():
                logger.info("Record '%s' is the same as stored version, skipping.", record.file_identifier)
                continue
        except RecordNotFoundError, GitlabGetError:
            # GitlabGetError returned if branch doesn't exist
            pass
        records_[_path] = record
    return records_


def _clean_input_records(logger: logging.Logger, record_paths: dict[Path, Record], results: GitUpsertResults) -> None:
    """Remove JSON encoded record files included in a commit."""
    mapping = {record.file_identifier: path for path, record in record_paths.items()}
    for file_identifier in results.new_identifiers + results.updated_identifiers:
        path = mapping[file_identifier]
        logger.info("Cleaning imported record: %s", path.resolve())
        path.unlink(missing_ok=True)


def _reduce_records(logger: logging.Logger, cat: BasCatalogue, args: Args) -> dict[Path, Record]:
    """Reduce a set of records to be committed to exclude unchanged (existing) records."""
    logger.info("Importing records from '%s' to '%s", args.path.resolve(), args.changeset_base)
    record_paths = _parse_records(logger=logger, search_path=args.path)
    return _filter_records(logger=logger, cat=cat, branch=args.changeset_base, record_paths=record_paths)


def _ensure_changeset(logger: logging.Logger, cat: BasCatalogue, args: Args) -> str:
    """Create, or use an existing changeset, to relate a set of commits."""
    mr = cat.repo.select_merge_requests(state="opened", branch=args.changeset_base)
    if mr:
        logger.info("Merge request exists: %s", mr[0].web_url)
        return mr[0].web_url

    logger.info("Creating merge request for changeset")
    mr = cat.repo.create_merge_request(
        source_branch=args.changeset_base,
        target_branch="main",
        title=f"Automated publishing changeset: {args.changeset_title}",
        description=f"{args.changeset_message}\n\nCreated by the experimental MAGIC Lantern non-interactive records publishing workflow.",
    )
    logger.info("Merge request created: %s", mr.web_url)
    return mr.web_url


def _commit_records(
    logger: logging.Logger, config: Config, cat: BasCatalogue, records: dict[Path, Record], args: Args
) -> GitUpsertResults:
    results = cat.commit(
        records=list(records.values()),
        context=GitUpsertContext(
            title=args.commit_title,
            message=args.commit_message,
            author_name=args.author_name,
            author_email=args.author_email,
            branch=args.changeset_base,
        ),
    )
    _clean_input_records(logger=logger, record_paths=records, results=results)
    logger.info("%s records imported.", len(results.new_identifiers) + len(results.updated_identifiers))
    logger.info("Commit '%s' created.", f"{config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{results.commit}")
    return results


def _publish_records(
    logger: logging.Logger, catalogue: BasCatalogue, args: Args, base_url: str, identifiers: set[str]
) -> None:
    """
    Publish items and records for records included in a commit.

    - publishes to S3 publicly
    - additionally uploads items as trusted content to secure hosting
    """
    logger.info("Publishing %s records.", len(identifiers))
    catalogue.export(
        env=args.env,
        identifiers=identifiers,
        branch=args.changeset_base,
        outputs=[
            ItemCatalogueOutput,
            ItemAliasesOutput,
            RecordIsoJsonOutput,
            RecordIsoXmlOutput,
            RecordIsoHtmlOutput,
        ],
    )

    logger.info("Records published:")
    for identifier in sorted(identifiers):
        logger.info("* %s/items/%s", base_url, identifier)
        logger.info("* %s/-/items/%s", base_url, identifier)


def _webhook(logger: logging.Logger, config: Config, commit: GitUpsertResults, mr_url: str, wh_url: str) -> None:
    """Trigger webhook if set."""
    logger.info("Sending webhook to '%s'", wh_url)
    payload = {
        "commit": {
            "branch": commit.branch,
            "commit": commit.commit,
            "new_identifiers": commit.new_identifiers,
            "updated_identifiers": commit.updated_identifiers,
            "url": f"{config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{commit.commit}",
        },
        "merge_request": {"url": mr_url},
    }
    logger.info("Webhook payload:")
    logger.info(payload)
    resp = requests.post(wh_url, json=payload, timeout=30)
    resp.raise_for_status()


def _run(logger: logging.Logger, config: Config, args: Args) -> None:
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.SITE_UNTRUSTED_AWS_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    catalogue = BasCatalogue(logger=logger, config=config, s3=s3)

    records = _reduce_records(logger=logger, cat=catalogue, args=args)
    if len(records) < 1:
        logger.info("No new or updated records to commit, exiting.")
        return

    mr_url = _ensure_changeset(logger=logger, cat=catalogue, args=args)
    commit = _commit_records(logger=logger, config=config, cat=catalogue, records=records, args=args)

    identifiers = set(commit.new_identifiers + commit.updated_identifiers)
    base_url = config.BASE_URL_TESTING if args.env == "testing" else config.BASE_URL_LIVE
    _publish_records(logger=logger, catalogue=catalogue, args=args, base_url=base_url, identifiers=identifiers)

    if args.webhook:
        _webhook(logger=logger, config=config, commit=commit, mr_url=mr_url, wh_url=args.webhook)


def parse_args() -> Args:  # pragma: no cover
    """Parse and validate script arguments."""
    parser = argparse.ArgumentParser(description="Import and publish catalogue records.")
    parser.add_argument(
        "--site",
        type=str,
        required=True,
        choices=get_args(SiteEnvironment),
        help="Catalogue site environment [testing/live]",
    )
    parser.add_argument("--path", type=Path, required=True, help="Directory containing record config files")
    parser.add_argument("--changeset-base", type=str, required=True, help="Changeset base branch name")
    parser.add_argument("--changeset-title", type=str, required=True, help="Changest title")
    parser.add_argument(
        "--changeset-message",
        type=lambda s: s.encode().decode("unicode_escape"),  # to handle newlines and other escaped characters
        required=True,
        help="Changest message",
    )
    parser.add_argument("--commit-title", type=str, required=True, help="Changeset commit title")
    parser.add_argument("--commit-message", type=str, required=True, help="Changeset commit message")
    parser.add_argument("--author-name", type=str, required=True, help="Changeset author name")
    parser.add_argument("--author-email", type=str, required=True, help="Changeset author email")
    parser.add_argument("--webhook", type=str, help="Optional webhook URL")
    args_ns = parser.parse_args()

    # rename `site` to `env` to match Args data class
    args_ns.env = args_ns.site
    del args_ns.site

    if not args_ns.changeset_base.replace("-", "").isalnum() or args_ns.changeset_base.startswith("-"):
        print(f"Error: '{args_ns.path}' must be alphanumeric with hyphens only. Values cannot start with a hyphen.")
        sys.exit(1)

    if not args_ns.path.is_dir():
        print(f"Error: '{args_ns.path}' must be a directory.")
        sys.exit(1)

    return Args(**vars(args_ns))


def entrypoint(args: Args) -> None:
    """Entrypoint."""
    init_sentry()
    config = Config()
    init_logging(logging_level=config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising Lantern non-interactive publishing workflow.")

    _run(logger=logger, config=config, args=args)
    print("Script exiting normally.")


if __name__ == "__main__":  # pragma: no cover
    entrypoint(parse_args())
