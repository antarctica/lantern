from markdown import Markdown, markdown

from assets_tracking_service.lib.markdown.extensions.links import LinkifyExtension
from assets_tracking_service.lib.markdown.extensions.prepend_new_line import PrependNewLineExtension
from assets_tracking_service.lib.markdown.formats.plaintext import PlainTextExtension


def md_as_html(string: str) -> str:
    """
    Encode string with possible Markdown as HTML.

    At a minimum the string will be returned as a paragraph.
    """
    return markdown(string, output_format="html", extensions=["tables", PrependNewLineExtension(), LinkifyExtension()])


def md_as_plain(string: str | None) -> str:
    """Strip possible Markdown formatting from a string."""
    if string is None:
        return ""

    md = Markdown(extensions=[PlainTextExtension()])
    return md.convert(string)
