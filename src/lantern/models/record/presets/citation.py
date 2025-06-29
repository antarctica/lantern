from assets_tracking_service.lib.bas_data_catalogue.models.record import HierarchyLevelCode
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Date, Identifier


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
    type_ = hierarchy_level.value.capitalize()

    identifiers = [] if identifiers is None else identifiers
    href = "?"
    try:
        self_identifier = next(identifier for identifier in identifiers if identifier.namespace == "data.bas.ac.uk")
        href = self_identifier.href
    except StopIteration:
        pass
    reference = f"[{href}]({href})"

    return f"{author} ({year}). _{title}_ (Version {version}) [{type_}]. {publisher}. {reference}."
