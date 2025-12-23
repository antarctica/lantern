import logging

import pytest

from lantern.config import Config
from lantern.stores.gitlab import GitLabStore
from lantern.utils import init_gitlab_store


@pytest.mark.cov()
class TestUtils:
    """Test app utils not tested elsewhere."""

    def test_gitlab_store(self, fx_logger: logging.Logger, fx_config: Config):
        """
        Can init GitLab store.

        Only called in dev-tasks so not considered as run in coverage.
        """
        store = init_gitlab_store(logger=fx_logger, config=fx_config)
        assert isinstance(store, GitLabStore)
