from lantern.repositories.bas import BasRepository
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore


class FakeBasRepository(BasRepository):
    """
    BAS Data Catalogue repository with altered methods for testing upstream classes.

    Uses a FakeStore subclass with additional properties instead of GitLab stores which are complex to mock.
    """

    def _make_gitlab_store(
        self, branch: str | None = None, cached: bool = False, frozen: bool = False
    ) -> GitLabStore | GitLabCachedStore:
        return super()._make_gitlab_store(branch, cached, frozen)
