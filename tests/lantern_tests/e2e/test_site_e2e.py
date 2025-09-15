from subprocess import Popen

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import has_network


@pytest.mark.skipif(not has_network(), reason="network unavailable")
class TestSentry:
    """Test Sentry feedback in Catalogue template."""

    def test_widget(self, fx_exporter_static_server: Popen, page: Page):
        """Can open feedback widget between tabs."""
        page.goto("http://localhost:8123/legal/privacy/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        page.wait_for_timeout(1000)  # wait for Sentry to init

        page.locator("text=Is something wrong with this page?").click()
        expect(page.locator("text=Add a screenshot")).to_be_visible()

    def test_fallback(self, fx_exporter_static_server: Popen, page: Page):
        """Email link shown where JavaScript is unavailable."""
        context = page.context.browser.new_context(java_script_enabled=False)
        no_js_page = context.new_page()
        no_js_page.goto("http://localhost:8123/legal/privacy/index.html")
        status_code = no_js_page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        fallback_link = no_js_page.get_by_role("link", name="Is something wrong with this page?")
        expect(fallback_link).to_be_visible()
        href = fallback_link.get_attribute("href")
        assert href.startswith("mailto:")

        expect(no_js_page.get_by_role("button", name="Is something wrong with this page?")).to_be_hidden()
        context.close()


class TestBackToTop:
    """Test back to top link."""

    def test_link(self, fx_exporter_static_server: Popen, page: Page):
        """
        Can navigate to the top of the page.

        Privacy page chosen as it's long enough to scroll.
        """
        page.goto("http://localhost:8123/legal/privacy/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        back_to_top = page.get_by_role("link", name="Back to Top")
        back_to_top.click()
        expect(back_to_top).not_to_be_in_viewport()  # link is off-screen when at top of page


class TestPrimaryNavigation:
    """Test primary navigation is responsive."""

    def test_mobile(self, fx_exporter_static_server: Popen, page: Page):
        """Can access primary navigation from the page footer on mobile."""
        iphone_13_mini = {
            "viewport": {"width": 375, "height": 812},
            "user_agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            ),
            "device_scale_factor": 3,
            "is_mobile": True,
            "has_touch": True,
        }
        context = page.context.browser.new_context(**iphone_13_mini)
        mobile_page = context.new_page()
        mobile_page.goto("http://localhost:8123/legal/privacy/index.html")
        status_code = mobile_page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        # expect primary link not to be viewport initially (and so not in header)
        primary_link = mobile_page.get_by_role("link", name="Part of British Antarctic Survey")
        expect(primary_link).not_to_be_in_viewport()

        # scroll to end of page and expect link to now be visible
        mobile_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        expect(primary_link).to_be_in_viewport()

        context.close()

    def test_desktop(self, fx_exporter_static_server: Popen, page: Page):
        """Can access primary navigation from the page header on larger viewports."""
        page.goto("http://localhost:8123/legal/privacy/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        primary_link = page.get_by_role("link", name="Part of British Antarctic Survey")
        expect(primary_link).to_be_in_viewport()
