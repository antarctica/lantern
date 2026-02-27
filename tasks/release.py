import argparse
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from dunamai import Style, Version

__VERSION__ = "0.4.0"  # of this release workflow, not the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _bump_change_log_version(version: str, breaking: bool = False) -> None:
    path = PROJECT_ROOT / "CHANGELOG.md"
    version_line = f"[{version}] - {datetime.now(tz=UTC).date().isoformat()}"
    if breaking:
        version_line += " [BREAKING!]"

    with path.open(mode="r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith("## [Unreleased]"):
            lines[i] = f"## [Unreleased]\n\n## {version_line}\n"
    with path.open(mode="w") as f:
        f.writelines(lines)


def _bump_uv(version: str | None = None, bump: Literal["major", "minor", "patch"] | None = None) -> str:
    set_args = ["uv", "version"]
    if version:
        set_args.append(version)
    elif bump:
        set_args.extend(["--bump", bump])
    else:
        msg = "Must specify either a version or a bump element (major/minor/patch)."
        raise ValueError(msg) from None

    try:
        subprocess.run(set_args, check=True, capture_output=True, text=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        print(f"Error setting 'uv version': {e.stderr}")
        raise
    try:
        out = subprocess.run(["uv", "version", "--short"], check=True, capture_output=True, text=True)  # noqa: S607
        return out.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting 'uv version': {e.stderr}")
        raise


def main() -> None:
    """Entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument("version_element", choices=["major", "minor", "patch", "prerelease"])
    parser.add_argument(
        "breaking",
        help="Whether this release includes breaking changes. Affects the CHANGELOG.md entry.",
        nargs="?",
        default="false",
    )
    args = parser.parse_args()
    breaking = args.breaking.lower() == "true"

    if args.version_element == "prerelease":
        current_version = Version.from_git()
        current_version_fmt = current_version.serialize(style=Style.SemVer, format="{base}")
        bumped_version = current_version.serialize(style=Style.SemVer, format="{base}-post.{distance}")
        print(f"Bumping version: {current_version_fmt} -> {bumped_version}")
        _bump_uv(version=bumped_version)
        return

    if args.version_element not in ["major", "minor", "patch"]:
        msg = f"Invalid bump element: {args.version_element}"
        raise ValueError(msg) from None
    bumped_version = _bump_uv(bump=args.version_element)
    _bump_change_log_version(version=bumped_version, breaking=breaking)


if __name__ == "__main__":
    main()
