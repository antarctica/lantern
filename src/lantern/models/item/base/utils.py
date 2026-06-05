import re

from markdown import Markdown, markdown
from markdown_gfm_admonition import GfmAdmonitionExtension
from markupsafe import Markup

from lantern.lib.markdown.extensions.links import LinkifyExtension
from lantern.lib.markdown.extensions.prepend_new_line import PrependNewLineExtension
from lantern.lib.markdown.formats.plaintext import PlainTextExtension


def md_as_html(string: str) -> str:
    """
    Encode string with possible Markdown as HTML.

    At a minimum the string will be returned as a paragraph.
    """
    return Markup(  # noqa: S704
        markdown(
            string,
            output_format="html",
            extensions=[
                "tables",
                "admonition",
                GfmAdmonitionExtension(),
                PrependNewLineExtension(),
                LinkifyExtension(),
            ],
        )
    )


def md_as_html_unwrapped(string: str) -> str:
    """
    Encode string with possible Markdown as HTML, without wrapping paragraph tags.

    Applies to outer tags only. I.e. '<div><p>...</p></div>' will not be modified.

    At a minimum returns an empty string.
    """
    html = md_as_html(string)
    html = re.sub(r"^<p[^>]*>", "", html)  # Remove <p> tag at start of string
    return re.sub(r"</p>$", "", html)  # Remove </p> at end of string


def md_as_plain(string: str | None) -> str:
    """Strip possible Markdown formatting from a string."""
    if string is None:
        return ""

    md = Markdown(extensions=[PlainTextExtension()])
    return md.convert(string)
