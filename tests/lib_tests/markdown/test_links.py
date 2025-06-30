import pytest
from markdown import Markdown

from lantern.lib.markdown.extensions.links import LinkifyExtension


class TestLinkifyExtension:
    """Test automatic linking markdown extension."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("x", "<p>x</p>"),
            ("[x](y)", '<p><a href="y" rel="nofollow">x</a></p>'),
            ('<a href="y">x</a>', '<p><a href="y">x</a></p>'),
            ("http://example.com", '<p><a href="http://example.com" rel="nofollow">http://example.com</a></p>'),
            ("https://example.com", '<p><a href="https://example.com" rel="nofollow">https://example.com</a></p>'),
            (
                "https://example.ac.uk",
                '<p><a href="https://example.ac.uk" rel="nofollow">https://example.ac.uk</a></p>',
            ),
            ("x@x.com", '<p><a href="mailto:x@x.com">x@x.com</a></p>'),
        ],
    )
    def test_conversion(self, value: str, expected: str):
        """Can create links for URLs and email addresses within text."""
        md = Markdown(extensions=[LinkifyExtension()])
        result = md.convert(value)
        assert result == expected
