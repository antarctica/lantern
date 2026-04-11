# Generate and export catalogue site

import logging
import time
from pathlib import Path

from tasks._shared import TargetEnvironment, init, init_s3, init_store
from tasks.cache_init import init_cache

from lantern.catalogue import BasCatalogue
from lantern.exporters.local import LocalExporter
from lantern.models.site import SiteEnvironment
from lantern.outputs.base import OutputBase
from lantern.stores.gitlab_cache import CacheFrozenError, GitLabCachedStore


def export(
    logger: logging.Logger,
    catalogue: BasCatalogue,
    env: SiteEnvironment,
    target: TargetEnvironment,
    identifiers: set[str],
    outputs: list[type[OutputBase]] | None = None,
) -> None:
    """Run catalogue export, ensuring store is frozen for performance and optionally overloading exporter."""
    if isinstance(catalogue._store, GitLabCachedStore):
        catalogue._store._frozen = True
        catalogue._store._cache._frozen = True
    if target == "local":
        catalogue._envs[env]._untrusted._exporter = LocalExporter(logger=logger, path=Path("export"))
        catalogue._envs[env]._trusted._exporter = LocalExporter(logger=logger, path=Path("export-trusted"))
    catalogue.export(env=env, identifiers=identifiers, outputs=outputs)


def main() -> None:
    """Entrypoint."""
    selected = set()  # to set use the form {"abc", "..."}
    target: TargetEnvironment = "remote"  # local/remote
    env: SiteEnvironment = "testing"  # testing/live, only relevant where target='remote'

    logger, config, store = init(cached_store=True)
    if not isinstance(store, GitLabCachedStore):
        raise TypeError() from None
    s3 = init_s3(config=config)
    catalogue = BasCatalogue(logger=logger, config=config, store=store, s3=s3)

    # Ensure store cache is up to date, then freeze
    store._cache._ensure_exists()
    store._frozen = True
    store._cache._frozen = True

    start = time.monotonic()
    try:
        export(logger=logger, catalogue=catalogue, env=env, target=target, identifiers=selected)
    except CacheFrozenError:
        _store = init_store(logger=logger, config=config, cached=True)
        init_cache(logger=logger, store=_store)  # ty:ignore[invalid-argument-type]

        # retry export with new frozen store
        catalogue._store = init_store(logger=logger, config=config, cached=True, frozen=True)
        export(logger=logger, catalogue=catalogue, env=env, target=target, identifiers=selected)
    finally:
        logger.info(f"Exported site in {round(time.monotonic() - start)} seconds.")


if __name__ == "__main__":
    main()
