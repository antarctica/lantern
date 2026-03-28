import logging
from collections.abc import Callable
from pathlib import Path

from tasks._record_utils import TargetEnv, init, init_s3

from lantern.catalogue import BasCatalogue, BasEnvironment
from lantern.exporters.local import LocalExporter
from lantern.outputs.base import OutputBase
from lantern.stores.gitlab_cache import GitLabCachedStore


def export(
    logger: logging.Logger,
    catalogue: BasCatalogue,
    env: BasEnvironment,
    target: TargetEnv,
    identifiers: set[str],
    outputs: list[Callable[..., OutputBase]] | None = None,
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
    env: BasEnvironment = "testing"  # testing/live
    target: TargetEnv = "local"  # local/remote

    logger, config, store = init(cached_store=True, frozen_store=True)
    s3 = init_s3(config=config)
    catalogue = BasCatalogue(logger=logger, config=config, store=store, s3=s3)
    export(logger=logger, catalogue=catalogue, env=env, target=target, identifiers=selected)


if __name__ == "__main__":
    main()
