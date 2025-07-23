import tomllib
from pathlib import Path


def _read_pyproject_version() -> str:
    with Path("pyproject.toml").open(mode="rb") as f:
        data = tomllib.load(f)

    return data["project"]["version"]


def main() -> None:
    """Get the project version."""
    print(_read_pyproject_version())


if __name__ == "__main__":
    main()
