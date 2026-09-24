# Invalidate thumbnails for selected records in CloudFront cache for BAS CDN

from argparse import ArgumentParser
from typing import TYPE_CHECKING

import boto3
from tasks._shared import init

from lantern.exporters.cloudfront import CloudFrontExporter

if TYPE_CHECKING:
    import logging

    from tasks._config import ExtraConfig


def _get_cli_args() -> tuple[str, str]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Invalidate cached thumbnails for an item.")
    parser.add_argument(
        "--item",
        "-i",
        required=True,
        help="Item to invalidate thumbnails for. Will interactively prompt if omitted.",
    )
    parser.add_argument(
        "--distribution",
        "-d",
        required=True,
        help="CloudFront distribution containing thumbnails. Will interactively prompt if omitted.",
    )
    args = parser.parse_args()
    return args.item, args.distribution


def invalidate_keys(logger: logging.Logger, config: ExtraConfig, distribution_id: str, keys: list[str]) -> None:
    """
    Create and execute CloudFront invalidation for selected keys.

    Using CDN (non-project specific) distribution.
    """
    client = boto3.client(
        "cloudfront",
        aws_access_key_id=config.SITE_UNTRUSTED_AWS_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_AWS_ACCESS_SECRET,
    )
    exporter = CloudFrontExporter(logger=logger, cloudfront=client, distribution=distribution_id)
    exporter.invalidate(keys)


def main() -> None:
    """Entrypoint."""
    logger, config, _catalogue = init()

    item, cf_id = _get_cli_args()
    keys = [f"/add-catalogue/0.0.0/img/items/{item}/*"]
    invalidate_keys(logger=logger, config=config, distribution_id=cf_id, keys=keys)


if __name__ == "__main__":
    main()
