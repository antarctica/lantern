import argparse
import logging
from typing import TYPE_CHECKING, get_args

from boto3 import client as S3Client  # noqa: N812

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.log import init as init_logging
from lantern.models.site import SiteEnvironment
from lantern.outputs.item_html import ItemCatalogueOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput

if TYPE_CHECKING:
    from lantern.outputs.base import OutputBase


def _run(logger: logging.Logger, config: Config, env: SiteEnvironment) -> None:
    s3 = S3Client(
        "s3",
        aws_access_key_id=config.SITE_UNTRUSTED_AWS_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
    catalogue = BasCatalogue(logger=logger, config=config, s3=s3)

    outputs: list[type[OutputBase]] = [SiteHealthOutput]
    if env == "live":
        # Include outputs that use or produce styles/scripts to update cache busting
        # (Site checks report not included as it will be updated on the next scheduled run)
        outputs.extend([SiteResourcesOutput, SitePagesOutput, SiteIndexOutput, ItemCatalogueOutput])
    catalogue.export(env=env, outputs=outputs)


def parse_args() -> SiteEnvironment:  # pragma: no cover
    """Parse and validate script arguments."""
    parser = argparse.ArgumentParser(description="Export site health check.")
    parser.add_argument(
        "--site",
        type=str,
        required=True,
        choices=get_args(SiteEnvironment),
        help="Catalogue site environment [testing/live]",
    )
    args_ns = parser.parse_args()
    return args_ns.site


def entrypoint(env: SiteEnvironment) -> None:
    """Entrypoint."""
    config = Config()
    init_logging(logging_level=config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising Lantern deployment site updates.")

    _run(logger=logger, config=config, env=env)
    print("Script exiting normally.")


if __name__ == "__main__":  # pragma: no cover
    entrypoint(parse_args())
