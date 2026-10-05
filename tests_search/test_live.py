from algoliasearch.search.client import SearchClientSync
from dotenv import dotenv_values

from lantern.config import Config


class TestLiveSearch:
    """Test live/real site search returns expected results."""

    def setup_method(self) -> None:
        """
        Initialise search client for each test.

        App config cannot be used for Algolia credentials as `pytest-env` sets these to fake values. Whilst this is
        usually desirable, for these tests we need to make real requests and so need real values.

        We can't skip `pytest-env` for some tests, and we can't easily override how `Config` gets its values.
        Therefore, it's necessary to load values directly from the `.env` file, ignoring `os.environ` completely.
        """
        env = dotenv_values()
        config = Config()

        self._index = config.TEMPLATES_ALGOLIA_INDEX_NAME
        self._client = SearchClientSync(
            app_id=env["LANTERN_TEMPLATES_ALGOLIA_APP_ID"],
            api_key=env["LANTERN_TEMPLATES_ALGOLIA_SEARCH_API_KEY"],
        )

    def test_empty_query(self):
        """An empty query returns at least some results."""
        results = self._client.search_single_index(index_name=self._index, search_params={})
        assert len(results.hits) > 0
