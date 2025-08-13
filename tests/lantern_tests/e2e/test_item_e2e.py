from subprocess import Popen

import pytest
from playwright.sync_api import Page, Route, expect

from tests.conftest import has_network
from tests.resources.records.item_cat_data import record as product_data
from tests.resources.records.item_cat_product_min import record as product_min_supported


class TestItemTabs:
    """Test tabs implementation in Catalogue Item template."""

    def test_switch(self, fx_exporter_static_server: Popen, page: Page):
        """Can switch between tabs."""
        endpoint = f"http://localhost:8123/items/{product_min_supported.file_identifier}/index.html"
        page.goto(endpoint)

        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        # initial tab will be 'licence', expect element from another tab not to be visible
        expect(page.locator("strong", has_text="Item licence")).to_be_visible()
        expect(page.locator("dt", has_text="Item ID")).not_to_be_visible()

        # change to another tab and expect its content to now be visible
        expect(page.locator("#item-tabs label[for='tab-info']")).to_be_visible()
        page.locator("#item-tabs label[for='tab-info']").click()
        expect(page.locator("dt", has_text="Item ID")).to_be_visible()
        expect(page.locator("strong", has_text="Item licence")).not_to_be_visible()

    def test_history(self, fx_exporter_static_server: Popen, page: Page):
        """Can switch between visited tabs."""
        endpoint = f"http://localhost:8123/items/{product_min_supported.file_identifier}/index.html"
        page.goto(endpoint)
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        expect(page.locator("strong", has_text="Item licence")).to_be_visible()

        # On load, no tab is explicitly selected so there's no URL fragment is present. Changing tab will explicitly
        # select that tab but if navigating back, the original, fragment-less URL will be used so the tab won't change.
        # To fix this we change tabs once to set the fragment, then run the test.
        page.locator("#item-tabs label[for='tab-info']").click()
        page.locator("#item-tabs label[for='tab-licence']").click()

        # change to another tab, then go back via browser, initial tab should be visible
        page.locator("#item-tabs label[for='tab-info']").click()
        expect(page.locator("dt", has_text="Item ID")).to_be_visible()
        page.go_back()
        expect(page.locator("strong", has_text="Item licence")).to_be_visible()

    def test_load(self, fx_exporter_static_server: Popen, page: Page):
        """Can set initial tab on page load if set in URL fragment."""
        endpoint = f"http://localhost:8123/items/{product_min_supported.file_identifier}/index.html"
        page.goto(endpoint + "#tab-info")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        expect(page.locator("dt", has_text="Item ID")).to_be_visible()


@pytest.mark.skipif(not has_network(), reason="network unavailable")
class TestItemEmbeddedMap:
    """
    Test embedded extent map in Catalogue Item template.

    As this test checks the contents of the iframe loaded from an external service, it is skipped if offline.
    """

    def test_load(self, fx_exporter_static_server: Popen, page: Page):
        """Can load embedded map."""

        def handle(route: Route) -> None:
            route.fulfill(
                status=200, content_type="text/html", body="<html><body>BAS Embedded Maps Service</body></html>"
            )

        page.route("https://embedded-maps.data.bas.ac.uk/*", handle)

        endpoint = f"http://localhost:8123/items/{product_min_supported.file_identifier}/index.html#tab-extent"
        page.goto(endpoint)
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        # get iframe for embedded map by looking for iframe with a base src value
        map_src = page.locator('iframe[src*="embedded-maps.data.bas.ac.uk"]').get_attribute("src")
        map_iframe = next((frame for frame in page.frames if frame.url == map_src), None)
        assert map_iframe is not None

        # verify iframe has expected content
        assert map_iframe.evaluate("document.title") == "BAS Embedded Maps Service"


class TestItemContactForm:
    """Test contact form in Catalogue Item template."""

    def test_send(self, fx_exporter_static_server: Popen, page: Page):
        """
        Can use item contact form.

        Sets intercept for contact form action
        """

        def handle(route: Route) -> None:
            route.fulfill(status=200, content_type="text/html", body="<html><body>OK</body></html>")

        page.route("https://example.com/contact*", handle)

        endpoint = f"http://localhost:8123/items/{product_min_supported.file_identifier}/index.html#tab-contact"
        page.goto(endpoint)
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        expect(page.locator("textarea#message-content")).to_be_visible()
        page.get_by_label("Message").fill("x")
        page.get_by_label("Your email address").fill("conwat@bas.ac.uk")
        page.get_by_text("Send Message").click()

        # Verify form submission
        expect(page.locator("body")).to_have_text("OK")


class TestItemDataActions:
    """Test data access information sections in Catalogue Item template."""

    def test_access_info(self, fx_exporter_static_server: Popen, page: Page):
        """Can open a data access information section in an item."""
        endpoint = f"http://localhost:8123/items/{product_data.file_identifier}/index.html#tab-data"
        page.goto(endpoint)
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        # find trigger button for a data access info section
        trigger = page.locator("#tab-content-data button[data-target]").first
        expect(trigger).to_be_visible()
        data_target = trigger.get_attribute("data-target")

        # click trigger and expect content to be visible
        trigger.click()
        expect(page.locator(f"{data_target}")).to_be_visible()
