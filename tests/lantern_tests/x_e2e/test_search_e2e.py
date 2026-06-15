import json
from subprocess import Popen

from playwright.sync_api import Page, Route, expect


class TestSearch:
    """Test site search."""

    def test_link(self, fx_exporter_static_server: Popen, fx_static_server_url: str, page: Page):
        """
        Can perform a search for a known item.

        Sets intercept for search action
        """

        def handle(route: Route) -> None:
            result = {
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
            route.fulfill(status=200, content_type="application/json", body=json.dumps(result))

        # Algolia uses a range of hostnames so match on query parameter in request instead
        page.route(lambda url: "x-algolia-application" in url, handle)

        page.goto(f"{fx_static_server_url}/search/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        page.locator("#site-search").get_by_role("searchbox").fill("Falkland Islands overview map")
        page.wait_for_timeout(100)  # 100ms

        # within #search-hits expect a link containing /a39d3502-55a1-4e18-8f67-fcf14b23485e
        expect(page.locator("#search-hits a[href*='/a39d3502-55a1-4e18-8f67-fcf14b23485e']")).to_be_visible(
            timeout=30_000
        )
