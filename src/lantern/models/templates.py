from dataclasses import dataclass, field
from datetime import date


@dataclass
class PageMetadata:
    """Common metadata used across Data Catalogue pages."""

    html_title: str
    sentry_src: str
    plausible_domain: str
    html_open_graph: dict = field(default_factory=dict)
    html_schema_org: str | None = None
    current_year: int = date.today().year  # noqa: DTZ011

    def __post_init__(self) -> None:
        """Configure values."""
        self.html_title = f"{self.html_title} | BAS Data Catalogue"
