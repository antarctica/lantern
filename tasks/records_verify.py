# Verify catalogue site

import logging
from pathlib import Path

from tasks._record_utils import TargetEnv, init, init_s3

from lantern.catalogue import BasCatalogue, BasEnvironment
from lantern.exporters.local import LocalExporter


def verify(
    logger: logging.Logger,
    catalogue: BasCatalogue,
    env: BasEnvironment,
    target: TargetEnv,
    identifiers: set[str],
    target_local: Path | None = None,
) -> None:
    """Run catalogue verify, optionally overloading exporter."""
    if target == "local":
        if not target_local:
            msg = "target_local must be set where target=local"
            raise ValueError(msg) from None
        catalogue._envs[env]._untrusted._exporter = LocalExporter(logger=logger, path=target_local)
    catalogue.verify(env=env, identifiers=identifiers)


def main() -> None:
    """Entrypoint."""
    selected = set()  # to set use the form {"abc", "..."}
    target: TargetEnv = "local"  # local/remote
    env: BasEnvironment = "testing"  # testing/live, only relevant where target='remote'
    target_local = Path("export")

    logger, config, store = init(cached_store=True, frozen_store=True)
    s3 = init_s3(config=config)
    catalogue = BasCatalogue(logger=logger, config=config, store=store, s3=s3)
    verify(logger=logger, catalogue=catalogue, env=env, target=target, identifiers=selected, target_local=target_local)


if __name__ == "__main__":
    main()
