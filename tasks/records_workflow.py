import functools
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import inquirer
from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config
from lantern.exporters.site import SiteExporter
from lantern.exporters.verification import VerificationExporter
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext
from lantern.stores.gitlab import CommitResults, GitLabStore
from tasks.records_import import _clean_input_path, _parse_records, _process_records
from tasks.records_import import _get_args as _get_import_args


def _time_task(label: str) -> callable:
    """Time a task and log duration."""

    def decorator(func: callable) -> callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202,
            start = datetime.now(tz=UTC)
            result = func(*args, **kwargs)
            end = datetime.now(tz=UTC)
            print(f"{label} took {round((end - start).total_seconds())} seconds")
            return result

        return wrapper

    return decorator


def _confirm(logger: logging.Logger, message: str) -> None:
    """Confirm user wants to proceed."""
    answers = inquirer.prompt(
        [
            inquirer.Confirm(name="confirm", message=message, default=True),
        ]
    )
    if not answers["confirm"]:
        logger.info("Cancelled by the user.")
        sys.exit(1)


def _import(logger: logging.Logger, config: Config, store: GitLabStore, import_path: Path) -> CommitResults:
    """Import."""
    logger.info(f"Importing records from '{import_path.resolve()}'")
    title, message, author_name, author_email = _get_import_args()
    store.populate()  # to ensure cache is populated to check if any files are updates
    records = _parse_records(logger=logger, search_path=import_path)
    records.extend(_process_records(logger=logger, records=records, store=store))
    results = store.push(records=records, title=title, message=message, author=(author_name, author_email))
    logger.info("Cleaning records from import path")
    _clean_input_path(input_path=import_path)
    logging.info(f"{len(results.new_identifiers) + len(results.updated_identifiers)} records imported.")
    logging.info(f"Commit: {config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{results.commit}.")
    return results


@_time_task(label="Build")
def _build(logger: logging.Logger, commit: CommitResults, site: SiteExporter, bucket: str) -> None:
    """Build."""
    identifiers = set(commit.new_identifiers + commit.updated_identifiers)
    logger.info(f"Publishing {len(identifiers)} records to {bucket}.")
    site._meta.build_repo_ref = commit.commit  # set build context
    site.select(file_identifiers=identifiers)
    site.publish()
    logger.info("Records published:")
    for identifier in sorted(identifiers):
        logger.info(f"* https://{bucket}/items/{identifier}")


def _verify(logger: logging.Logger, config: Config, commit: CommitResults, store: GitLabStore, s3: S3Client) -> None:
    """Verify."""
    identifiers = set(commit.new_identifiers + commit.updated_identifiers)
    logger.info(f"Verifying {len(identifiers)} records.")
    context: VerificationContext = {
        "BASE_URL": config.BASE_URL,
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
    }
    meta = ExportMeta.from_config_store(config=config, store=store, build_repo_ref=store.head_commit)
    exporter = VerificationExporter(logger=logger, meta=meta, s3=s3, get_record=store.get, context=context)
    exporter.selected_identifiers = identifiers
    exporter.run()
    exporter.publish()

    logger.info(f"Verification complete, result: {exporter.report.data['pass_fail']}.")
    logger.info(f"See '{config.BASE_URL}/-/verification' for report.")


@_time_task(label="Workflow")
def main() -> None:
    """Entrypoint."""
    config = Config()
    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    meta = ExportMeta.from_config_store(config=config, store=None, build_repo_ref=store.head_commit)
    site = SiteExporter(config=config, meta=meta, logger=logger, s3=s3, get_record=store.get)

    import_path = Path("./import")
    production_bucket = "add-catalogue.data.bas.ac.uk"

    if production_bucket == config.AWS_S3_BUCKET:
        logger.error("No. Production bucket selected.")
        sys.exit(1)

    print("\nThis script is for adding or updating records in the Catalogue.")
    print("It combines the 'records-import', 'records-build' and `records-verify' scripts with some workflow logic.")
    print(f"\nTo begin, stage records for import in '{import_path.resolve()}'.")
    print("TIP! See the 'records-select' and/or 'records-load' tasks if useful.")
    _confirm(logger, "Are records staged in import directory?")

    commit = _import(logger=logger, config=config, store=store, import_path=import_path)
    _build(logger=logger, site=site, commit=commit, bucket=config.AWS_S3_BUCKET)
    _verify(logger=logger, config=config, commit=commit, store=store, s3=s3)


if __name__ == "__main__":
    main()
