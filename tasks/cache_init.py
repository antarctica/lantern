from tasks._record_utils import confirm_source, init


# noinspection PyProtectedMember
def main() -> None:
    """Entrypoint."""
    logger, _config, store, _s3, _keys = init()

    confirm_source(logger=logger, store=store, action="Selecting records from")
    store.purge()
    store._cache._ensure_exists()
    if not store._cache.exists:
        msg = "Could not initialise cache."
        raise RuntimeError(msg) from None


if __name__ == "__main__":
    main()
