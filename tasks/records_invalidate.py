from argparse import ArgumentParser
from pathlib import Path

from tasks._record_utils import init
from tasks.site_invalidate import get_cf_distribution_id, invalidate_keys


def _get_cli_args() -> list[str]:
    """
    Get command line arguments.

    Return a list of record identifiers, via positional and/or named `--record` arguments.
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
    return list(args.records or []) + list(args.record or [])


def _get_invalidation_keys(file_identifiers: list[str]) -> list[str]:
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
    logger, _config, _store, _s3 = init()

    cf_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_cf_id")
    file_identifiers = _get_cli_args()
    keys = _get_invalidation_keys(file_identifiers)
    invalidate_keys(logger=logger, config=_config, distribution_id=cf_id, keys=keys)


if __name__ == "__main__":
    main()
