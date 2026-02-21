import logging

from boto3 import client as S3Client  # noqa: N812

from lantern.config import Config
from lantern.exporters.verification import VerificationExporter
from lantern.log import init as init_logging
from lantern.log import init_sentry
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext
from lantern.stores.gitlab import GitLabSource, GitLabStore


def _run(logger: logging.Logger, config: Config, base_url: str) -> None:
    store = GitLabStore(
        logger=logger,
        source=GitLabSource(
            endpoint=config.STORE_GITLAB_ENDPOINT,
            project=config.STORE_GITLAB_PROJECT_ID,
            ref="main",
        ),
        access_token=config.STORE_GITLAB_TOKEN,
    )
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    context: VerificationContext = {
        "BASE_URL": base_url,
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
        "SAN_PROXY_ENDPOINT": config.VERIFY_SAN_PROXY_ENDPOINT,
    }
    meta = ExportMeta.from_config_store(config=config, store=None, build_repo_ref=store.head_commit)
    exporter = VerificationExporter(logger=logger, meta=meta, s3=s3, context=context, select_records=store.select)
    exporter.run()
    exporter.publish()


def main() -> None:
    """Entrypoint."""
    init_sentry()

    config = Config()

    init_logging(logging_level=config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising Lantern site-wide verification.")

    base_url = "https://data.bas.ac.uk"
    logger.info(f"Base URL: {base_url}")
    _run(logger=logger, config=config, base_url=base_url)

    print("Script exiting normally.")


if __name__ == "__main__":
    main()
