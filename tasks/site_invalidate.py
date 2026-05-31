# Invalidate selected outputs in CloudFront cache for live site

from argparse import ArgumentParser

from tasks._shared import init


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


def main() -> None:
    """Entrypoint."""
    _logger, _config, catalogue = init()

    keys = _get_cli_args()
    catalogue._envs["live"]._untrusted._invalidator.invalidate(keys)  # ty:ignore[unresolved-attribute]


if __name__ == "__main__":
    main()
