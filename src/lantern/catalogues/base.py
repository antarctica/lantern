from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput

if TYPE_CHECKING:
    import logging

    from lantern.outputs.base import OutputBase


class CatalogueBase(ABC):
    """
    Abstract base class for a catalogue.

    Catalogues are responsible at a high level for managing a set of Records and transforming these into a static site
    built from representations of these Records plus global/static content.

    Combines and coordinates one or more Repositories (or Stores directly), Outputs, Sites and Exporters.

    This base Catalogue class is intended to be generic and minimal, with subclasses being more opinionated.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @staticmethod
    def _group_output_classes(
        outputs: list[type[OutputBase]] | None = None,
    ) -> tuple[list[type[OutputBase]], list[type[OutputBase]]]:
        """
        Sort selected output classes into individual and global types, or return all classes.

        Filters out the RedirectsOutput if included it needs to be run separately based on other Outputs.
        """
        all_global: list[type[OutputBase]] = [
            SiteResourcesOutput,
            SiteIndexOutput,
            SitePagesOutput,
            SiteApiOutput,
            SiteHealthOutput,
            RecordsWafOutput,
            ItemsBasWebsiteOutput,
        ]
        all_individual: list[type[OutputBase]] = [
            ItemCatalogueOutput,
            ItemAliasesOutput,
            RecordIsoJsonOutput,
            RecordIsoXmlOutput,
            RecordIsoHtmlOutput,
        ]

        if not outputs:
            return all_global, all_individual
        # RedirectsOutput won't be included as it isn't in either list
        return [output for output in all_global if output in outputs], [
            output for output in all_individual if output in outputs
        ]

    @abstractmethod
    def export(self, identifiers: set[str] | None = None) -> None:
        """Generate a static site from (selected) records and other content, then export to a host."""
        ...

    @abstractmethod
    def check(self, identifiers: set[str] | None = None) -> None:
        """Check catalogue site contents (optionally for selected records)."""
        ...
