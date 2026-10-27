from algoliasearch.search.client import SearchClientSync
from algoliasearch.search.models import SearchResponse
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

    def _query(self, query: str) -> SearchResponse:
        """Helper to query the search index."""
        return self._client.search_single_index(
            index_name=self._index, search_params={"query": query, "analytics": False}
        )

    def test_empty_query(self):
        """Can get at least some results for an empty (unfiltered) query."""
        result = self._query(query="")
        assert len(result.hits) > 0

    def test_exact_match(self):
        """Can get an expected result for a known, unique, item title."""
        result = self._query(query="Falkland Islands overview map")
        assert len(result.hits) == 1
        assert result.hits[0].object_id == "a39d3502-55a1-4e18-8f67-fcf14b23485e"

    def test_misspelt_match(self):
        """Can get an expected result for a known, unique, misspelt item title."""
        result = self._query(query="Fallkand Inlands overveiw map")
        assert len(result.hits) == 1
        assert result.hits[0].object_id == "a39d3502-55a1-4e18-8f67-fcf14b23485e"
