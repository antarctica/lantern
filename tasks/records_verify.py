import logging

from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config
from lantern.exporters.verification import VerificationExporter
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext
from lantern.stores.gitlab import GitLabStore


def main() -> None:
    """Entrypoint."""
    config = Config()
    init_logging(config.LOG_LEVEL)
    init_sentry()
    logger = logging.getLogger("app")
    logger.info("Initialising")

    base_url = "https://data.bas.ac.uk"
    selected = set()  # to set use the form {"abc", "..."}

    s3 = S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )

    store = GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        branch=config.STORE_GITLAB_BRANCH,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )
    store.populate()

    context: VerificationContext = {
        "BASE_URL": base_url,
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
    }
    meta = ExportMeta.from_config_store(config=config, store=None, build_repo_ref=store.head_commit)

    exporter = VerificationExporter(logger=logger, meta=meta, s3=s3, get_record=store.get, context=context)
    exporter.selected_identifiers = {record.file_identifier for record in store.records}
    if selected:
        exporter.selected_identifiers = selected
    exporter.run()
    exporter.export()
    logger.info(f"Verify report with {len(exporter.report)} tests saved.")


if __name__ == "__main__":
    main()
