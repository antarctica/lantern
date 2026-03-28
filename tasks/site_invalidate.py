import logging
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from uuid import uuid4

import boto3
from tasks._config import ExtraConfig
from tasks._record_utils import confirm, init


def get_cf_distribution_id(iac_cwd: Path, cf_id: str) -> str:
    """Get CloudFront distribution ID from IaC state."""
    proc = subprocess.run(  # noqa: S603
        ["tofu", "output", "-raw", cf_id],  # noqa: S607
        cwd=str(iac_cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def _get_cli_args() -> list[str]:
    """
    Get command line arguments.

    Return a list of keys, via positional and/or named `--keys` arguments.
    """
    parser = ArgumentParser(description="Invalidate cached content in live catalogue hosting.")
    parser.add_argument(
        "keys",
        nargs="*",
        help="Key(s) in static hosting to invalidate.",
    )
    parser.add_argument(
        "--key",
        action="append",
        help="Key in static hosting to invalidate. Can be specified multiple times.",
    )
    args = parser.parse_args()
    return list(args.keys or [])


def invalidate_keys(logger: logging.Logger, config: ExtraConfig, distribution_id: str, keys: list[str]) -> None:
    """Create and execute CloudFront invalidation for selected keys."""
    if not keys:
        logger.info("No keys to invalidate.")
        return
    logger.info("Keys to invalidate:")
    for key in keys:
        logger.info(f"'{key}'")
    confirm(logger=logger, message="Continue?")

    client = boto3.client(
        "cloudfront",
        aws_access_key_id=config.SITE_UNTRUSTED_S3_ACCESS_ID,
        aws_secret_access_key=config.SITE_UNTRUSTED_S3_ACCESS_SECRET,
    )
    caller_ref = str(uuid4())
    logger.info(f"Creating CloudFront invalidation for distribution {distribution_id}")
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "Paths": {
                "Quantity": len(keys),
                "Items": keys,
            },
            "CallerReference": caller_ref,
        },
    )
    invalidation_id = response["Invalidation"]["Id"]
    logger.info(f"Invalidation created: {invalidation_id}")

    waiter = client.get_waiter("invalidation_completed")
    logger.info("Waiting for invalidation to complete ...")
    waiter.wait(DistributionId=distribution_id, Id=invalidation_id, WaiterConfig={"Delay": 10, "MaxAttempts": 60})
    logger.info("Invalidation completed.")


def main() -> None:
    """Entrypoint."""
    logger, _config, _store = init()

    cf_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_cf_id")
    keys = _get_cli_args()
    invalidate_keys(logger=logger, config=_config, distribution_id=cf_id, keys=keys)


if __name__ == "__main__":
    main()
