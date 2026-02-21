import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import requests
from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config
from lantern.exporters.site import SiteExporter
from lantern.lib.metadata_library.models.record.record import RecordInvalidError
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.record.record import Record
from lantern.models.site import ExportMeta
from lantern.stores.base import RecordNotFoundError
from lantern.stores.gitlab import CommitResults, GitLabSource, GitLabStore


@dataclass
class Args:
    """Script arguments."""

    path: Path
    changeset_base: str
    changeset_title: str
    changeset_message: str
    commit_title: str
    commit_message: str
    author_name: str
    author_email: str
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
            logger.exception(f"Record '{config.get('file_identifier', '<unknown>')}' does not validate, skipping.")
            logger.exception(e.validation_error)
            sys.exit(1)
        if hasattr(Record, "_config_supported") and not Record._config_supported(config):
            logger.warning(
                f"Record '{config.get('file_identifier', '<unknown>')}' contains unsupported content the catalogue will ignore."
            )
        records[json_path] = record
    logger.info(f"Discovered {len(records)} valid records")
    return records


def _filter_records(logger: logging.Logger, record_paths: dict[Path, Record], store: GitLabStore) -> dict[Path, Record]:
    """Filter out records that have not changed compared to the remote store."""
    records_ = {}
    for _path, record in record_paths.items():
        try:
            existing_record = store.select_one(record.file_identifier)
            if record.dumps() == existing_record.dumps():
                logger.info(f"Record '{record.file_identifier}' is the same as stored version, skipping.")
                continue
        except RecordNotFoundError:
            pass
        records_[_path] = record
    return records_


def _clean_input_records(logger: logging.Logger, record_paths: dict[Path, Record], results: CommitResults) -> None:
    """Remove JSON encoded record files included in a commit."""
    mapping = {record.file_identifier: path for path, record in record_paths.items()}
    for file_identifier in results.new_identifiers + results.updated_identifiers:
        path = mapping[file_identifier]
        logger.info(f"Cleaning imported record: {path.resolve()}")
        path.unlink(missing_ok=True)


def _import_records(logger: logging.Logger, store: GitLabStore, args: Args) -> dict[Path, Record]:
    """Commit a set of updated records to the store."""
    logger.info(f"Importing records from '{args.path.resolve()}'")
    record_paths = _parse_records(logger=logger, search_path=args.path)
    return _filter_records(logger=logger, record_paths=record_paths, store=store)


def _create_changeset(logger: logging.Logger, store: GitLabStore, args: Args) -> str:
    """Create, or use an existing changeset, to relate a set of commits."""
    mr = store._project.mergerequests.list(state="opened", source_branch=store._source.ref)
    if mr:
        logger.info(f"Merge request exists: {mr.web_url}")
        return mr[0].web_url

    logger.info("Creating merge request for changeset")
    mr = store._project.mergerequests.create(
        {
            "source_branch": store._source.ref,
            "target_branch": "main",
            "title": f"Automated publishing changeset: {args.changeset_title}",
            "description": f"{args.changeset_message}\n\nCreated by the experimental MAGIC Lantern non-interactive records publishing workflow.",
        }
    )
    logger.info(f"Merge request created: {mr.web_url}")
    return mr.web_url


def _commit_records(
    logger: logging.Logger, config: Config, store: GitLabStore, records: dict[Path, Record], args: Args
) -> CommitResults:
    results = store.push(
        records=list(records.values()),
        title=args.commit_title,
        message=args.commit_message,
        author=(args.author_name, args.author_email),
    )
    _clean_input_records(logger=logger, record_paths=records, results=results)
    logger.info(f"{len(results.new_identifiers) + len(results.updated_identifiers)} records imported.")
    logger.info(f"Commit: {config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{results.commit} created.")
    return results


def _publish_records(logger: logging.Logger, config: Config, site: SiteExporter, commit: CommitResults) -> None:
    """
    Publish items and records for records included in a commit.

    - publishes to S3 publicly
    - additionally uploads items as trusted content to secure hosting
    """
    identifiers = set(commit.new_identifiers + commit.updated_identifiers)

    logger.info(f"Publishing {len(identifiers)} records.")
    site._records_exporter.publish()

    logger.info("Records published:")
    for identifier in sorted(identifiers):
        logger.info(f"* https://{config.AWS_S3_BUCKET}/items/{identifier}")
        logger.info(f"* https://{config.AWS_S3_BUCKET}/-/items/{identifier}")


def _webhook(logger: logging.Logger, config: Config, commit: CommitResults, mr_url: str, wh_url: str) -> None:
    """Trigger webhook if set."""
    logger.info(f"Sending webhook to {wh_url}")
    payload = {
        "commit": {
            **commit.unstructure(),
            "url": f"{config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{commit.commit}",
        },
        "merge_request": {"url": mr_url},
    }
    logger.info("Webhook payload:")
    logger.info(payload)
    resp = requests.post(wh_url, json=payload, timeout=30)
    resp.raise_for_status()


def _parse_args() -> Args:
    """Parse and validate script arguments."""
    parser = argparse.ArgumentParser(description="Import and publish catalogue records.")
    parser.add_argument("--path", type=Path, required=True, help="Directory containing record config files")
    parser.add_argument("--changeset-base", type=str, required=True, help="Changeset base branch name")
    parser.add_argument("--changeset-title", type=str, required=True, help="Changest title")
    parser.add_argument("--changeset-message", type=str, required=True, help="Changest message")
    parser.add_argument("--commit-title", type=str, required=True, help="Changeset commit title")
    parser.add_argument("--commit-message", type=str, required=True, help="Changeset commit message")
    parser.add_argument("--author-name", type=str, required=True, help="Changeset author name")
    parser.add_argument("--author-email", type=str, required=True, help="Changeset author email")
    parser.add_argument("--webhook", type=str, help="Optional webhook URL")
    args_ns = parser.parse_args()

    if not args_ns.changeset_base.replace("-", "").isalnum() or args_ns.changeset_base.startswith("-"):
        print(f"Error: '{args_ns.path}' must be alphanumeric with hyphens only. Values cannot start with a hyphen.")
        sys.exit(1)

    if not args_ns.path.is_dir():
        print(f"Error: '{args_ns.path}' must be a directory.")
        sys.exit(1)

    return Args(**vars(args_ns))


def _run(logger: logging.Logger, config: Config, args: Args) -> None:
    store = GitLabStore(
        logger=logger,
        source=GitLabSource(
            endpoint=config.STORE_GITLAB_ENDPOINT,
            project=config.STORE_GITLAB_PROJECT_ID,
            ref=args.changeset_base,
        ),
        access_token=config.STORE_GITLAB_TOKEN,
    )

    records = _import_records(logger=logger, store=store, args=args)
    if len(records) < 1:
        logger.info("No new or updated records to commit, exiting.")
        sys.exit(0)

    mr_url = _create_changeset(logger=logger, store=store, args=args)
    commit = _commit_records(logger=logger, config=config, store=store, records=records, args=args)
    if len(set(commit.new_identifiers + commit.updated_identifiers)) == 0:
        logger.info("No records committed, exiting.")
        sys.exit(0)

    meta = ExportMeta.from_config_store(config=config, store=store, build_repo_ref=commit.commit)
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    site = SiteExporter(
        logger=logger,
        config=config,
        meta=meta,
        s3=s3,
        store=store,
        selected_identifiers=set(commit.new_identifiers + commit.updated_identifiers),
    )
    _publish_records(logger=logger, config=config, site=site, commit=commit)

    if args.webhook:
        _webhook(logger=logger, config=config, commit=commit, mr_url=mr_url, wh_url=args.webhook)


def main() -> None:
    """Entrypoint."""
    init_sentry()

    config = Config()
    args = _parse_args()

    init_logging(logging_level=config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising Lantern non-interactive publishing workflow.")

    _run(logger=logger, config=config, args=args)

    print("Script exiting normally.")


if __name__ == "__main__":
    main()
