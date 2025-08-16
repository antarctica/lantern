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
        context.close()
