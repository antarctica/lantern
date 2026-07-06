# Recreate catalogue search index

import time

from tasks._shared import init

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config


def _reindex(cat: BasCatalogue, config: Config) -> None:
    algolia = cat.repo._make_algolia_store()
    algolia.push(records=cat.repo.select_records(), admin_keys=config.ADMIN_METADATA_KEYS)


def main() -> None:
    """Entrypoint."""
    logger, config, catalogue = init()

    params = "task search-reindex"

    start = time.monotonic()
    _reindex(cat=catalogue, config=config)
    logger.info(f"Rebuilt search index in {round(time.monotonic() - start)} seconds.")
    logger.info(f"Re-run as: '% {params}'")


if __name__ == "__main__":
    main()
