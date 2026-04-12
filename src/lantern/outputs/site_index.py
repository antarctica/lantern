import logging
from pathlib import Path

from lantern.models.checks import CheckType
from lantern.models.item.catalogue.enums import ResourceTypeIcon
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputSite
from lantern.stores.base import SelectRecordsProtocol
from lantern.utils import get_record_aliases, prettify_html


class SiteIndexOutput(OutputSite):
    """
    Proto catalogue index output.

    Generates a page with links to items and aliases for all records in a store.

    Not intended for general use (but also not sensitive).
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, select_records: SelectRecordsProtocol) -> None:
        super().__init__(logger=logger, meta=meta, name="Site Index", check_type=CheckType.SITE_INDEX)
        self._select_records = select_records
        self._template_path = "_views/-/index.html.j2"

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        meta = {"build_key": self._meta.build_key}
        if self._meta.build_repo_ref:
            meta["build_ref"] = self._meta.build_repo_ref
        return meta

    @property
    def _data(self) -> dict:
        """Assemble index data."""
        idx_records = []
        idx_aliases = []

        for record in self._select_records():
            idx_records.append(
                {
                    "icon_class": ResourceTypeIcon[record.hierarchy_level.name].value,
                    "type": record.hierarchy_level.name,
                    "file_identifier": record.file_identifier,
                    "title": record.identification.title,
                    "edition": record.identification.edition,
                }
            )
            identifiers = get_record_aliases(record)
            idx_aliases.extend(
                [
                    {
                        "alias": (identifier.href or "").replace("https://data.bas.ac.uk/", ""),
                        "href": f"/items/{record.file_identifier}",
                        "file_identifier": record.file_identifier,
                        "title": record.identification.title,
                    }
                    for identifier in identifiers
                ]
            )

        return {
            "records": idx_records,
            "aliases": idx_aliases,
        }

    @property
    def _content(self) -> str:
        """Generate index page."""
        self._meta.html_title = "Index"
        raw = self._jinja.get_template(self._template_path).render(meta=self._meta.site_metadata, data=self._data)
        return prettify_html(raw)

    @property
    def content(self) -> list[SiteContent]:
        """Output content for site."""
        return [
            SiteContent(
                content=self._content,
                path=Path("-") / "index" / "index.html",
                media_type="text/html",
                object_meta=self._object_meta,
            )
        ]
