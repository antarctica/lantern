from enum import Enum

from lantern.lib.metadata_library.models.record.elements.common import Date, Identifier
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from lantern.models.record.const import CATALOGUE_NAMESPACE


class CitationHierarchyLevelCode(Enum):
    """Partial mapping of the Hierarchy Level code list to citation resource types."""

    DATASET = "Dataset"
    PRODUCT = "Product"
    MAP_PRODUCT = "Map"
    PAPER_MAP_PRODUCT = "Map"
    WEB_MAP_PRODUCT = "Online"


def make_magic_citation(
    title: str,
    hierarchy_level: HierarchyLevelCode,
    edition: str | None = None,
    publication_date: Date | None = None,
    identifiers: list[Identifier] | None = None,
) -> str:
    """Resource citation using MAGIC as a publisher with Markdown formatting."""
    author = "British Antarctic Survey"
    publisher = "British Antarctic Survey Mapping and Geographic Information Centre"
    year = "?year" if publication_date is None else publication_date.date.year
    version = "?version" if edition is None else edition
    type_ = ""
    if hierarchy_level.name in list(CitationHierarchyLevelCode.__members__.keys()):
        type_ = f" [{CitationHierarchyLevelCode[hierarchy_level.name].value}]"
    identifiers = [] if identifiers is None else identifiers
    href = "?"
    try:
        self_identifier = next(identifier for identifier in identifiers if identifier.namespace == CATALOGUE_NAMESPACE)
        href = self_identifier.href
    except StopIteration:
        pass
    reference = f"[{href}]({href})"

    return f"{author} ({year}). _{title}_ (Version {version}){type_}. {publisher}. {reference}."
