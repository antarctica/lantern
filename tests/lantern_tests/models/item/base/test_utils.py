import pytest

from lantern.models.item.base.utils import md_as_html, md_as_plain


class TestMdAsHtml:
    """Test _md_as_html util function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("_x_", "<p><em>x</em></p>"),
            ("https://example.com", '<p><a href="https://example.com" rel="nofollow">https://example.com</a></p>'),
            ("x\n* x", "<p>x</p>\n<ul>\n<li>x</li>\n</ul>"),
            ("> [!NOTE]\n> x", '<div class="admonition note">\n<p class="admonition-title">Note</p>\n<p>x</p>\n</div>'),
        ],
    )
    def test_md_as_html(self, value: str, expected: str):
        """Can convert Markdown to HTML with extensions."""
        assert md_as_html(value) == expected


class TestMdAsPlain:
    """Test _md_as_plain util function."""

    @pytest.mark.parametrize(("value", "expected"), [("_x_", "x"), (None, "")])
    def test_md_as_plain(self, value: str | None, expected: str):
        """Can convert Markdown to plain text."""
        assert md_as_plain(value) == expected
