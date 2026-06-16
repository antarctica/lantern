from lxml import html as lhtml
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
    return str(
        Markup(  # noqa: S704
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
    )


def md_as_html_unwrapped(string: str) -> str:
    """
    Encode string with possible Markdown as HTML, without wrapping paragraph tags.

    Applies to outer tags only. I.e. '<div><p>...</p></div>' will not be modified.

    At a minimum returns an empty string.
    """
    doc = lhtml.fromstring(md_as_html(string))

    if doc.tag == "p":
        # unwrap and return contents of a single <p> tag
        inner_html = doc.text or ""
        for child in doc:
            inner_html += lhtml.tostring(child, encoding="unicode", method="html")
        inner_html += (doc.tail or "").strip()
        return inner_html

    # For non-`<p>` root elements, return as-is
    return lhtml.tostring(doc, encoding="unicode", method="html")


def md_as_plain(string: str | None) -> str:
    """Strip possible Markdown formatting from a string."""
    if string is None:
        return ""

    md = Markdown(extensions=[PlainTextExtension()])
    return md.convert(string)
