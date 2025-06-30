import pytest
from markdown import Markdown

from lantern.lib.markdown.extensions.prepend_new_line import PrependNewLineExtension


class TestPrependNewLineExtension:
    """Test automatic list formatting markdown extension."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("x", "<p>x</p>"),
            ("x\n\n* x", "<p>x</p>\n<ul>\n<li>x</li>\n</ul>"),
            ("x\n* x", "<p>x</p>\n<ul>\n<li>x</li>\n</ul>"),
            ("x\n* x\n* x", "<p>x</p>\n<ul>\n<li>x</li>\n<li>x</li>\n</ul>"),
        ],
    )
    def test_conversion(self, value: str, expected: str):
        """Can fix new lines for lists to ensure proper formatting."""
        md = Markdown(extensions=[PrependNewLineExtension()])
        result = md.convert(value)
        assert result == expected
