from tasks._record_utils import confirm_branch, init


def main() -> None:
    """Entrypoint."""
    logger, _config, store, _s3, _keys = init()

    confirm_branch(logger=logger, store=store, action="Selecting records from")
    # noinspection PyProtectedMember
    store._cache.purge()
    store.populate()


if __name__ == "__main__":
    main()
