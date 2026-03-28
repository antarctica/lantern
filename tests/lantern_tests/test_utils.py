import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from jinja2 import Environment
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import get_jinja_env, get_record_aliases, init_gitlab_store, prettify_html, time_task


@pytest.mark.cov()
class TestUtils:
    """Test app utils not tested elsewhere."""

    @pytest.mark.parametrize("path", [True, False])
    @pytest.mark.parametrize("cached", [True, False])
    @pytest.mark.parametrize("frozen", [True, False])
    def test_gitlab_store(
        self, fx_logger: logging.Logger, fx_config: Config, path: bool, cached: bool, frozen: bool
    ) -> None:
        """
        Can init GitLab store.

        Only called in dev-tasks so not considered as run in coverage.
        """
        if not cached and frozen:
            with pytest.raises(ValueError, match=r"Cannot create a frozen GitLab store without caching."):
                init_gitlab_store(logger=fx_logger, config=fx_config, cached=cached, frozen=frozen)
            return
        cache_dir = fx_config.STORE_GITLAB_CACHE_PATH
        if path:
            with TemporaryDirectory() as tmp_path:
                cache_dir = Path(tmp_path)
        cache_path = cache_dir if path else None

        store = init_gitlab_store(logger=fx_logger, config=fx_config, path=cache_path, cached=cached, frozen=frozen)
        assert isinstance(store, GitLabStore)
        assert isinstance(store, GitLabCachedStore) == cached
        if isinstance(store, GitLabCachedStore):
            assert store.frozen == frozen
            assert store._cache._cache_path.parent == cache_dir

    def test_get_record_aliases(self, fx_revision_model_min: RecordRevision):
        """Can get any aliases in a record."""
        alias = Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)

        fx_revision_model_min.identification.identifiers.append(alias)
        result = get_record_aliases(fx_revision_model_min)
        assert len(result) == 1
        assert result[0] == alias

    def test_get_jinja_env(self):
        """Can get app Jinja environment."""
        result = get_jinja_env()
        assert isinstance(result, Environment)
        assert "_macros/common.html.j2" in result.loader.list_templates()

    def test_prettify_html(self):
        """Can format HTML."""
        assert (
            prettify_html(html="<html>\n\n\n\n\n<body><p>...</p></body></html>")
            == "<html>\n<body><p>...</p></body></html>"
        )

    def test_time_task(self, mocker: MockerFixture):
        """Can time a task and log duration using decorator."""
        mock_logger = mocker.MagicMock()

        class _Dummy:
            _logger = mock_logger

            @time_task(label="Test task")
            def do_work(self) -> str:
                return "done"

        result = _Dummy().do_work()

        assert result == "done"
        mock_logger.info.assert_called_once()
        logged_msg = mock_logger.info.call_args[0][0]
        assert logged_msg.startswith("Test task took ")
        assert logged_msg.endswith(" seconds")
