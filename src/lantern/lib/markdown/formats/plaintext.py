# Based on: https://github.com/kostyachum/python-markdown-plain-text/blob/main/markdown_plain_text/extention.py
from xml.etree.ElementTree import Element, ElementTree

from markdown import Extension, Markdown


def _serialize_plain_text(data: list, elem: Element) -> None:
    tag = elem.tag
    text = elem.text

    if text and (tag is None or tag.lower() not in ["script", "style"]):
        data.append(text)
    for e in elem:
        _serialize_plain_text(data, e)
    if elem.tail:
        data.append(elem.tail)


def to_plain_text(element: Element) -> str:
    """Recursively convert HTML elements to plain text."""
    root = ElementTree(element).getroot()
    if not isinstance(root, Element):
        msg = "Cannot get root element"
        raise ValueError(msg) from None  # noqa: TRY004
    text = []
    _serialize_plain_text(text, root)
    return "".join(text)


class PlainTextExtension(Extension):
    """Markdown library extension to remove Markdown formatting."""

    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802
        """Add plain text serialiser to Markdown instance."""
        md.serializer = to_plain_text
        md.stripTopLevelTags = False

        # Prevent rewriting serializer we have just changed
        md.set_output_format = lambda x: x  # ty: ignore[invalid-assignment]
