import logging

from tasks._record_utils import confirm_source, init

from lantern.stores.gitlab_cache import GitLabCachedStore


def init_cache(logger: logging.Logger, store: GitLabCachedStore) -> None:
    """Initialise cache in store."""
    confirm_source(logger=logger, store=store, action="Selecting records from")
    store.purge()
    store._cache._ensure_exists()
    if not store._cache.exists:
        msg = "Could not initialise cache."
        raise RuntimeError(msg) from None


# noinspection PyProtectedMember
def main() -> None:
    """Entrypoint."""
    logger, _config, store, _s3 = init()
    init_cache(logger=logger, store=store)


if __name__ == "__main__":
    main()
