# Force initialise GitLab cached store

from tasks._shared import confirm_gitlab_source, init

from lantern.catalogues.bas import BasCatalogue


def init_cache(cat: BasCatalogue) -> None:
    """Initialise cache in store."""
    confirm_gitlab_source(logger=cat._logger, cat=cat, action="Selecting records from")
    cat.repo.gitlab.purge()
    cat.repo.gitlab._cache._ensure_exists()
    if not cat.repo.gitlab._cache.exists:
        msg = "Could not initialise cache."
        raise RuntimeError(msg) from None


def main() -> None:
    """Entrypoint."""
    _logger, _config, catalogue = init(cached_store=True)
    init_cache(cat=catalogue)


if __name__ == "__main__":
    main()
