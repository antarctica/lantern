# Invalidate thumbnails for selected records in CloudFront cache for BAS CDN

import subprocess
from argparse import ArgumentParser
from typing import TYPE_CHECKING

import boto3
from tasks._shared import init

from lantern.exporters.cloudfront import CloudFrontExporter

if TYPE_CHECKING:
    import logging
    from pathlib import Path

    from tasks._config import ExtraConfig


def get_cf_distribution_id(iac_cwd: Path, cf_id: str) -> str:
    """Get CloudFront distribution ID from IaC state."""
    proc = subprocess.run(  # noqa: S603
        ["tofu", "output", "-raw", cf_id],
        cwd=str(iac_cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def _get_cli_args() -> tuple[str, str]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Invalidate cached thumbnails for an item.")
    parser.add_argument(
        "--item",
        "-i",
        required=True,
        help="Item to invalidate thumbnails for Will interactively prompt if omitted.",
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
