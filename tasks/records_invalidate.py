# Invalidate record specific outputs in CloudFront cache for live site

from argparse import ArgumentParser
from pathlib import Path

from tasks._shared import init
from tasks.site_invalidate import get_cf_distribution_id, invalidate_keys


def _get_cli_args() -> set[str]:
    """
    Get command line arguments.

    Return record identifiers, via positional and/or named `--record` arguments.
    """
    parser = ArgumentParser(description="Invalidate cached record exports in the live catalogue.")
    parser.add_argument(
        "records",
        nargs="*",
        help="Record identifier(s) as positional arguments (file identifier, URL, or file name).",
    )
    parser.add_argument(
        "--record",
        action="append",
        help="Record identifier. Can be specified multiple times.",
    )
    args = parser.parse_args()
    return set(list(args.records or []) + list(args.record or []))


def get_record_invalidation_keys(file_identifiers: set[str]) -> list[str]:
    """
    Generate keys to invalidate within CloudFront distribution based on selected records.

    Includes keys for specific resources (as items and records), and global outputs such as indexes.
    """
    keys = ["/-/index/index.html", "/waf/*"] if file_identifiers else []
    fids = file_identifiers
    keys.extend([f"/items/{fid}/*" for fid in fids] + [f"/records/{fid}/*" for fid in fids])
    return keys


def main() -> None:
    """Entrypoint."""
    logger, _config, _store = init()

    cf_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_cf_id")
    cf_replica_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_replica_cf_id")

    file_identifiers = _get_cli_args()
    keys = get_record_invalidation_keys(file_identifiers)

    # also apply to replica site distribution
    for cid in [cf_id, cf_replica_id]:
        invalidate_keys(logger=logger, config=_config, distribution_id=cid, keys=keys)


if __name__ == "__main__":
    main()
