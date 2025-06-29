# Based on: https://github.com/daGrevis/mdx_linkify/blob/master/mdx_linkify/mdx_linkify.py
from bleach.linkifier import Linker
from markdown import Markdown
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor


class LinkifyPostprocessor(Postprocessor):
    """Markdown library post-processor for converting URLs and email addresses into HTML links."""

    def __init__(self, md: Markdown) -> None:
        super().__init__(md)

        self._linker_options = {"skip_tags": ["code"], "parse_email": True}

    def run(self, text: str) -> str:
        """Convert URLs in text into full links."""
        linker = Linker(**self._linker_options)
        return linker.linkify(text)


class LinkifyExtension(Extension):
    """Markdown library extension to convert URLs and email addresses into HTML links."""

    def __init__(self) -> None:
        super().__init__()

    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802
        """Add processor to Markdown instance."""
        md.postprocessors.register(LinkifyPostprocessor(md), "linkify", 50)
