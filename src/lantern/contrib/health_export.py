import logging

from boto3 import client as S3Client  # noqa: N812

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.log import init as init_logging
from lantern.outputs.site_health import SiteHealthOutput


def _run(logger: logging.Logger, config: Config) -> None:
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.SITE_UNTRUSTED_AWS_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    catalogue = BasCatalogue(logger=logger, config=config, s3=s3)
    catalogue.export(env="live", outputs=[SiteHealthOutput])


def entrypoint() -> None:
    """Entrypoint."""
    config = Config()
    init_logging(logging_level=config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising Lantern health check export.")

    _run(logger=logger, config=config)
    print("Script exiting normally.")
