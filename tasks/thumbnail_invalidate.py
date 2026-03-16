import subprocess
from argparse import ArgumentParser
from pathlib import Path

from tasks._record_utils import init
from tasks.site_invalidate import invalidate_keys


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


def _get_cli_args() -> str:
    """
    Get command line arguments.

    Return an item identifier via positional and/or named `--item` arguments.
    """
    parser = ArgumentParser(description="Invalidate cached thumbnails for an item.")
    parser.add_argument(
        "item",
        nargs="?",
        help="Item to invalidate thumbnails for (positional).",
    )
    parser.add_argument(
        "--item",
        dest="item_opt",
        help="Item to invalidate thumbnails for (optional flag).",
    )
    args = parser.parse_args()
    item = args.item_opt if args.item_opt is not None else args.item
    if item is None:
        parser.error("Item is required (positional or using --item)")
    return item


def main() -> None:
    """Entrypoint."""
    logger, _config, _store, _s3 = init()

    cf_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="thumbnails_cf_id")
    item = _get_cli_args()
    keys = [f"/add-catalogue/0.0.0/img/items/{item}/*"]
    invalidate_keys(logger=logger, config=_config, distribution_id=cf_id, keys=keys)


if __name__ == "__main__":
    main()
