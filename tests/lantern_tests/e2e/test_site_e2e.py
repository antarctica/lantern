from subprocess import Popen

from playwright.sync_api import Page, expect


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
