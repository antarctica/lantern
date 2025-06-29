# Based on: https://gitlab.com/ayblaq/prependnewline/-/blob/master/prependnewline.py
import re

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class PrependNewLinePreprocessor(Preprocessor):
    """Markdown library pre-processor to ensure proper spacing between paragraphs and lists."""

    LIST_ITEM_RE = re.compile(r"^(?P<indent>\s*)([*+-])\s+", re.MULTILINE)

    def run(self, lines: list[str]) -> list[str]:
        """Add new lines before lists if not preceded by a blank line."""
        new_lines = []
        prev_blank = True
        prev_item = False

        for line in lines:
            if self.LIST_ITEM_RE.match(line):
                if not prev_blank and not prev_item:
                    new_lines.append("")
                new_lines.append(line)
                prev_blank = False
                prev_item = True
            else:
                new_lines.append(line)
                prev_blank = line.strip() == ""
                prev_item = False

        return new_lines


class PrependNewLineExtension(Extension):
    """Markdown library extension to ensure proper spacing between paragraphs and lists."""

    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802
        """Add processor to Markdown instance."""
        md.preprocessors.register(PrependNewLinePreprocessor(md), "prependnewline", 12)
