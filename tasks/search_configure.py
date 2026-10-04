# Update the catalogue search index configuration

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import tomli_w
from tasks._shared import init

if TYPE_CHECKING:
    import logging

    from lantern.stores.algolia import AlgoliaStore


def _dump_config(logger: logging.Logger, algolia: AlgoliaStore, path: Path) -> None:
    """
    Populate path with TOML encoded index settings.

    Created to initially capture config, not necessarily intended for reuse.
    """
    settings = algolia.index_settings()
    if not settings:
        logger.error("Index settings are empty, aborting.")
        return
    with path.open(mode="wb") as f:
        tomli_w.dump(settings.to_dict(), f)


def _apply_config(logger: logging.Logger, algolia: AlgoliaStore, path: Path) -> None:
    """Update index based on TOML encoded settings."""
    with path.open(mode="rb") as f:
        logger.info("Loading index settings from: %s", path.resolve())
        settings = tomllib.load(f)
        algolia.configure_index(settings)


def main() -> None:
    """Entrypoint."""
    logger, _config, catalogue = init()
    algolia = catalogue.repo._make_algolia_store()

    config_path = Path(__file__).parent.parent / "resources" / "configs" / "search.toml"
    params = "task search-configure"

    _apply_config(logger=logger, algolia=algolia, path=config_path)
    logger.info("Re-run as: '%s'", params)


if __name__ == "__main__":
    main()
