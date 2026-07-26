from subprocess import Popen

from playwright.sync_api import Page, expect


class TestBackToTop:
    """Test back to top link."""

    def test_link(self, fx_exporter_static_server: Popen, fx_static_server_url: str, page: Page):
        """
        Can navigate to the top of the page.

        Privacy page chosen as it's long enough to scroll.
        """
        page.goto(f"{fx_static_server_url}/legal/privacy/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        back_to_top = page.get_by_role("link", name="Back to Top")
        back_to_top.click()
        expect(back_to_top).not_to_be_in_viewport()  # link is off-screen when at top of page


class TestFeedbackWidget:
    """Test site feedback widget."""

    def test_widget(self, fx_exporter_static_server: Popen, fx_static_server_url: str, page: Page):
        """
        Can open and close feedback widget.

        Does not test a feedback submission.

        Testing the close button requires calling click directly in JS to avoid the standard click giving an error that
        the button element isn't in the viewport, which can't be bypassed via `click(force=True). This is a problem when
        running tests offline as the close button's visible content is a font-awesome icon that won't load without the
        internet. `click()` by default requires visible content and evaluates to not found, which `force` mitigates but
        then triggers a viewport error which can't.
        """
        page.goto(f"{fx_static_server_url}/legal/privacy/index.html")
        status_code = page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200
        expect(page.locator("#site-feedback >> text=Site feedback")).not_to_be_visible()

        # widget can be opened
        page.locator("text=Is something wrong with this page?").click()
        expect(page.locator("#site-feedback")).to_be_visible()

        # clicking trigger again closes it
        page.locator("text=Is something wrong with this page?").click()
        expect(page.locator("#site-feedback")).not_to_be_visible()

        # clicking close button inside widget when open closes it
        page.locator("text=Is something wrong with this page?").click()
        page.evaluate(
            "document.querySelector('#site-feedback > header > button[data-target=\"#site-feedback\"]').click()"
        )
        expect(page.locator("#site-feedback")).not_to_be_visible()

    def test_fallback(self, fx_exporter_static_server: Popen, fx_static_server_url: str, page: Page):
        """Email link is shown where JavaScript is unavailable."""
        context = page.context.browser.new_context(java_script_enabled=False)
        no_js_page = context.new_page()
        no_js_page.goto(f"{fx_static_server_url}/legal/privacy/index.html")
        status_code = no_js_page.evaluate("window.performance.getEntries()[0].responseStatus")
        assert status_code == 200

        fallback_link = no_js_page.get_by_role("link", name="Is something wrong with this page?")
        expect(fallback_link).to_be_visible()
        href = fallback_link.get_attribute("href")
        assert href.startswith("mailto:")

        expect(no_js_page.get_by_role("button", name="Is something wrong with this page?")).to_be_hidden()
        context.close()
