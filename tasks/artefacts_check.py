# Check any files in a directory are supported as file artefacts.

from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import inquirer
from inquirer import Path as InquirerPath
from tasks._shared import init

from lantern.lib.magic_distribution.models.artefact import (
    ArtefactFormatLabel,
    ArtefactFormatNotSupportedError,
    ArtefactFormats,
    ArtefactFormatUnknownError,
)

if TYPE_CHECKING:
    import logging


def _get_cli_args() -> tuple[bool, Path]:
    """Get command line arguments."""
    parser = ArgumentParser(description="Check file artefacts are supported.")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force artefacts path.",
    )
    parser.add_argument(
        "--artefacts-path",
        "-a",
        type=Path,
        default=Path("./artefacts"),
        help="Directory containing artefact files to check. Will use default if omitted.",
    )
    args = parser.parse_args()
    return args.force, args.artefacts_path


def _get_args(cli_args: tuple[bool, Path]) -> tuple[Path, str]:
    """Get task inputs, interactively if needed/allowed."""
    cli_force, cli_artefacts_path = cli_args

    artefacts_path = cli_artefacts_path

    if cli_force:
        params = f"task artefacts-check --force --artefacts-path {artefacts_path.resolve()}"
        return artefacts_path, params

    artefacts_path = Path(
        inquirer.path("Artefacts path", path_type=InquirerPath.DIRECTORY, exists=True, default=artefacts_path)
    )

    msg = "Artefacts path MUST be set for this task."
    if not isinstance(artefacts_path, Path):
        raise TypeError(msg) from None

    params = f"task artefacts-check --force --artefacts-path {artefacts_path.resolve()}"
    return artefacts_path, params


class Result(NamedTuple):
    """."""

    path: Path
    status: str
    msg: str | None
    ext: str
    format: ArtefactFormatLabel | None


def _check_artefacts(logger: logging.Logger, artefacts_path: Path) -> list[Result]:
    """Generate artefacts for supported file types."""
    logger.info("Checking files as supported artefacts without recursion in: %s", artefacts_path.resolve())
    results: list[Result] = []

    for path in artefacts_path.iterdir():
        if path.is_file():
            ext = "".join(path.suffixes)
            logger.info("Evaluating file: %s", path.resolve())
            try:
                fmt = ArtefactFormats.get_file_format(file=path)
            except ArtefactFormatUnknownError:
                results.append(Result(path=path, status="⚠️", msg="Format unknown", ext=ext, format=None))
            except ArtefactFormatNotSupportedError:
                results.append(
                    Result(path=path, status="❌", msg="Format explicitly unsupported", ext=ext, format=None)
                )
            else:
                results.append(Result(path=path, status="✅", msg=None, ext=ext, format=fmt.label))

    return results


def main() -> None:
    """Entrypoint."""
    logger, _config, _catalogue = init()

    cli_args = _get_cli_args()
    artefacts_path, params = _get_args(cli_args=cli_args)

    results = _check_artefacts(logger=logger, artefacts_path=artefacts_path)
    fmt_padding = max(len(s) for s in [str(x.format.name if x.format else "") for x in results]) + 1

    for result in results:
        fmt = result.format.name if result.format else ""
        logger.info("%s %s %s %s", result.status, fmt.ljust(fmt_padding, " "), result.path.resolve(), result.msg or "")
        if result.status != "✅":
            logger.info("  ext: %s", result.ext)

    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
