import logging

import pytest

from lantern.config import Config
from lantern.stores.gitlab import GitLabStore
from lantern.utils import init_gitlab_store, init_s3_client


@pytest.mark.cov()
class TestUtils:
    """Test app utils not tested elsewhere."""

    @pytest.mark.parametrize("prefer_frozen", [True, False])
    def test_gitlab_store(self, fx_logger: logging.Logger, fx_config: Config, prefer_frozen: bool) -> None:
        """
        Can init GitLab store.

        Only called in dev-tasks so not considered as run in coverage.
        """
        store = init_gitlab_store(logger=fx_logger, config=fx_config, frozen=prefer_frozen)
        assert isinstance(store, GitLabStore)

    def test_s3_client(self, fx_logger: logging.Logger, fx_config: Config):
        """
        Can init S3 client.

        Initially a coverage only check.
        """
        client = init_s3_client(config=fx_config)
        assert client is not None
