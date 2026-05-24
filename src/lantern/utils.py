from jinja2 import Environment, PackageLoader, select_autoescape
from minify_html import minify

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE
from lantern.models.record.record import Record


def get_record_aliases(record: Record) -> list[Identifier]:
    """Get optional aliases for record as relative file paths / S3 keys."""
    return record.identification.identifiers.filter(namespace=ALIAS_NAMESPACE)


def get_jinja_env() -> Environment:
    """Get Jinja environment with app templates."""
    _loader = PackageLoader("lantern", "resources/templates")
    return Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)


def minify_html(html: str) -> str:
    """
    Minify HTML string, removing any non-required whitespace and other optimisations.

    For performance and to avoid messy whitespace from Jinja template conditionals and other logic.
    """
    return minify(html, keep_closing_tags=True, keep_html_and_head_opening_tags=True, keep_input_type_text_attr=True)
