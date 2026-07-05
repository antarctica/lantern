import json
from subprocess import Popen

from playwright.sync_api import Page, Route, expect

SEARCH_TERMS = "Falkland Islands overview map"  # a39d3502-55a1-4e18-8f67-fcf14b23485e
EXPECTED_ID = "a39d3502-55a1-4e18-8f67-fcf14b23485e"
UNEXPECTED_ID = "8196cad3-7dc1-4fac-842a-272215b2bf52"


class TestSearch:
    """Test site search."""

    @staticmethod
    def _handle_algolia(route: Route) -> None:
        """Return Algolia API response based on simple search query."""
        query = ""
        if route.request.method == "POST":
            try:
                request_data = json.loads(route.request.post_data)
                if "requests" in request_data and len(request_data["requests"]) > 0:
                    query = request_data["requests"][0].get("query")
            except (json.JSONDecodeError, TypeError, IndexError, KeyError):
                pass

        all_results = {
            "results": [
                {
                    "hits": [
                        {
                            "objectType": "MAP_PRODUCT",
                            "objectTypeIcon": "fa-regular fa-frame",
                            "objectRevID": "16e217046d1f60a1c261fd7a64c373e96afca684",
                            "objectRevDate": 1775433600,
                            "objectRecData": '["o", "Mapping and Geographic Information Centre, British Antarctic Survey", "magic@bas.ac.uk", "2025-09-15"]',
                            "type": "PRODUCT (MAP)",
                            "name": "Falkland Islands overview map",
                            "nameHtml": "Falkland Islands overview map",
                            "restricted": False,
                            "summaryHtml": "<p>An overview map of the Falkland Islands, showing key place names, settlements and elevation. </p>",
                            "objectDate": 1757894400,
                            "date": "15 September 2025",
                            "edition": "Ed. 1",
                            "imageUrl": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/a39d3502-55a1-4e18-8f67-fcf14b23485e/1016-thumbnail.png",
                            "objectID": "a39d3502-55a1-4e18-8f67-fcf14b23485e",
                            "_highlightResult": {
                                "name": {
                                    "value": "__ais-highlight__Falkland__/ais-highlight__ __ais-highlight__Islands__/ais-highlight__ __ais-highlight__overview__/ais-highlight__ __ais-highlight__map__/ais-highlight__",
                                    "matchLevel": "full",
                                    "fullyHighlighted": True,
                                    "matchedWords": ["falkland", "islands", "overview", "map"],
                                }
                            },
                        },
                        {
                            "objectType": "PRODUCT",
                            "objectTypeIcon": "fa-regular fa-file-fragment",
                            "objectRevID": "125fa191475ab14af0bc55d69fc18f247ae6956c",
                            "objectRevDate": 1781740800,
                            "objectRecData": '["o", "Mapping and Geographic Information Centre, British Antarctic Survey", "magic@bas.ac.uk", "2026-05-20T13:30:00+00:00"]',
                            "type": "PRODUCT",
                            "name": "Hillshade for British Antarctic Territory",
                            "nameHtml": "Hillshade for British Antarctic Territory",
                            "restricted": False,
                            "summaryHtml": "<p>Hillshade covering British Antarctic Territory, constructed using REMA v2.0 10m mosaic dataset.</p>",
                            "objectDate": 1781770039,
                            "date": "18 June 2026",
                            "edition": "Ed. 2",
                            "imageUrl": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/d6a0c661-c321-4849-b2af-e993acd96d2f/BAT_Hillshade.png",
                            "objectID": "8196cad3-7dc1-4fac-842a-272215b2bf52",
                        },
                    ],
                    "nbHits": 2,
                    "page": 0,
                    "nbPages": 1,
                    "hitsPerPage": 200,
                    "exhaustiveNbHits": True,
                    "exhaustiveTypo": True,
                    "exhaustive": {"nbHits": True, "typo": True},
                    "query": "",
                    "params": "highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=200",
                    "index": "records_all_v1",
                    "renderingContent": {
                        "facetOrdering": {
                            "facets": {"order": ["type"]},
                            "values": {"type": {"sortRemainingBy": "alpha"}},
                        }
                    },
                    "processingTimeMS": 1,
                    "processingTimingsMS": {"_request": {"roundTrip": 15}, "total": 0},
                }
            ]
        }
        single_result = {
            "results": [
                {
                    "hits": [
                        {
                            "objectType": "MAP_PRODUCT",
                            "objectTypeIcon": "fa-regular fa-frame",
                            "objectRevID": "16e217046d1f60a1c261fd7a64c373e96afca684",
                            "objectRevDate": 1775433600,
                            "objectRecData": '["o", "Mapping and Geographic Information Centre, British Antarctic Survey", "magic@bas.ac.uk", "2025-09-15"]',
                            "type": "PRODUCT (MAP)",
                            "name": "Falkland Islands overview map",
                            "nameHtml": "Falkland Islands overview map",
                            "restricted": False,
                            "summaryHtml": "<p>An overview map of the Falkland Islands, showing key place names, settlements and elevation. </p>",
                            "objectDate": 1757894400,
                            "date": "15 September 2025",
                            "edition": "Ed. 1",
                            "imageUrl": "https://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/a39d3502-55a1-4e18-8f67-fcf14b23485e/1016-thumbnail.png",
                            "objectID": "a39d3502-55a1-4e18-8f67-fcf14b23485e",
                            "_highlightResult": {
                                "name": {
                                    "value": "__ais-highlight__Falkland__/ais-highlight__ __ais-highlight__Islands__/ais-highlight__ __ais-highlight__overview__/ais-highlight__ __ais-highlight__map__/ais-highlight__",
                                    "matchLevel": "full",
                                    "fullyHighlighted": True,
                                    "matchedWords": ["falkland", "islands", "overview", "map"],
                                }
                            },
                        }
                    ],
                    "nbHits": 1,
                    "page": 0,
                    "nbPages": 1,
                    "hitsPerPage": 200,
                    "exhaustiveNbHits": True,
                    "exhaustiveTypo": True,
                    "exhaustive": {"nbHits": True, "typo": True},
                    "query": "Falkland Islands overview map",
                    "params": "highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=200&query=Falkland+Islands+overview+map",
                    "index": "records_all_v1",
                    "renderingContent": {
                        "facetOrdering": {
                            "facets": {"order": ["type"]},
                            "values": {"type": {"sortRemainingBy": "alpha"}},
                        }
                    },
                    "processingTimeMS": 1,
                    "processingTimingsMS": {"_request": {"roundTrip": 15}, "total": 0},
                }
            ]
        }
        result = single_result if query == SEARCH_TERMS else all_results

        route.fulfill(status=200, content_type="application/json", body=json.dumps(result))

    def test_query(self, fx_exporter_static_server: Popen, fx_static_server_url: str, page: Page):
        """
        Can return results for a known item via search input.

        Mocks Algolia API to control search results.
        """
        # Algolia uses a range of hostnames so match on query parameter and path in request instead
        page.route(lambda url: "x-algolia-application" in url and "/queries" in url, self._handle_algolia)

        page.goto(f"{fx_static_server_url}/search/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        expected_result = page.locator(f"#search-hits a[href*='/{EXPECTED_ID}']")
        unexpected_result = page.locator(f"#search-hits a[href*='/{UNEXPECTED_ID}']")
        stats = page.locator("#search-stats")
        share_link = page.get_by_role("link", name="Share results")

        # expect all results to be shown initially
        expect(expected_result).to_be_visible()
        expect(unexpected_result).to_be_visible()
        expect(stats).to_contain_text("2 results")
        expect(share_link).not_to_be_visible()

        page.locator("#search-form").get_by_role("searchbox").fill(SEARCH_TERMS)
        page.wait_for_timeout(100)  # 100ms

        # expect only matching results to be shown when a query is set
        expect(expected_result).to_be_visible()
        expect(unexpected_result).not_to_be_visible()
        expect(stats).to_contain_text("1 result")

        # expect share results link to now show
        expect(share_link).to_be_visible()
        expect(share_link).to_have_attribute("href", f"/search?q={SEARCH_TERMS.replace(' ', '+')}")

    def test_parameter(self, fx_exporter_static_server: Popen, fx_static_server_url: str, page: Page):
        """
        Can return results for a known item via URL parameter.

        Mocks Algolia API to control search results.
        """
        # Algolia uses a range of hostnames so match on query parameter and path in request instead
        page.route(lambda url: "x-algolia-application" in url and "/queries" in url, self._handle_algolia)

        page.goto(f"{fx_static_server_url}/search/index.html?q={SEARCH_TERMS.replace(' ', '+')}")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        expected_result = page.locator(f"#search-hits a[href*='/{EXPECTED_ID}']")
        unexpected_result = page.locator(f"#search-hits a[href*='/{UNEXPECTED_ID}']")

        # expect only matching results to be shown
        expect(expected_result).to_be_visible()
        expect(unexpected_result).not_to_be_visible()
