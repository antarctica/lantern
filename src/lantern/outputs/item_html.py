import logging
from pathlib import Path

from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent, SiteRedirect
from lantern.outputs.base import OutputRecord
from lantern.stores.base import SelectRecordProtocol
from lantern.utils import get_jinja_env, get_record_aliases, prettify_html


class ItemCatalogueOutput(OutputRecord):
    """
    Catalogue item HTML output.

    Outputs a Record as a human-readable data catalogue item page using an appropriate ItemCatalogue (sub)class.

    Supports trusted publishing (via export meta). Requires a record select method for related item summaries.
    """

    def __init__(
        self, logger: logging.Logger, meta: ExportMeta, record: RecordRevision, select_record: SelectRecordProtocol
    ) -> None:
        """Initialise."""
        super().__init__(logger=logger, meta=meta, record=record)
        self._select_record = select_record
        self._jinja = get_jinja_env()
        self._template_path = "_views/item.html.j2"

    @property
    def name(self) -> str:
        """Output name."""
        return "Item Catalogue HTML"

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {
            "build_key": self._meta.build_key,
            "file_identifier": self._record.file_identifier,
            "file_revision": self._record.file_revision,
        }

    def _item_class(self) -> type[ItemCatalogue]:
        """Get the ItemCatalogue (sub-)class to use for this record."""
        if ItemCataloguePhysicalMap.matches(self._record):
            return ItemCataloguePhysicalMap
        return ItemCatalogue

    @property
    def _content(self) -> str:
        """Encode record as data catalogue item in HTML."""
        item_class = self._item_class()
        item = item_class(
            site_meta=self._meta.site_metadata,
            record=self._record,
            admin_meta_keys=self._meta.admin_meta_keys,
            trusted_context=self._meta.trusted,
            select_record=self._select_record,
        )

        raw = self._jinja.get_template(self._template_path).render(item=item, meta=item.site_metadata)
        return prettify_html(raw)

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content for item."""
        return [
            SiteContent(
                content=self._content,
                path=Path("items") / self._record.file_identifier / "index.html",
                media_type="text/html",
                object_meta=self._object_meta,
            )
        ]


class ItemAliasesOutput(OutputRecord):
    """
    Item HTML aliases output.

    Creates redirect pages back to the item page for any aliases the item contains.

    Uses S3 object redirects where possible with a minimal HTML redirect page as a fallback.
    """

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Item Aliases"

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {"file_identifier": self._record.file_identifier, "file_revision": self._record.file_revision}

    def _get_aliases(self) -> list[str]:
        """Get optional aliases for record as relative paths."""
        identifiers = get_record_aliases(self._record)
        return [(identifier.href or "").replace(f"https://{CATALOGUE_NAMESPACE}/", "") for identifier in identifiers]

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content per item alias."""
        target = self._meta.base_url + f"/items/{self._record.file_identifier}/"  # ensure trailing slash
        return [
            SiteRedirect(path=Path(alias) / "index.html", target=target, object_meta=self._object_meta)
            for alias in self._get_aliases()
        ]
