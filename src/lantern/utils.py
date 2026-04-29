from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

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


def prettify_html(html: str) -> str:
    """
    Prettify HTML string, removing any empty lines.

    Without very careful whitespace control, Jinja templates quickly look messy where conditionals and other logic are
    used. Whilst this doesn't strictly matter, it is nicer if output looks well-formed by removing empty lines.

    This gives a 'flat' structure when viewed as source. Browser dev tools will reformat this into a tree structure.
    The `prettify()` method is not used as it splits all elements onto new lines, which causes layout/spacing bugs.
    """
    return str(BeautifulSoup(html, parser="html.parser", features="lxml"))
