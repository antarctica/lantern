import json
import logging
from pathlib import Path

from lantern.lib.metadata_library.models.record.enums import AggregationAssociationCode
from lantern.models.checks import CheckType
from lantern.models.item.website.search import ItemWebsiteSearch
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputRecords
from lantern.stores.base import SelectRecordsProtocol


class ItemsBasWebsiteOutput(OutputRecords):
    """
    BAS Public Website search items output.

    Note: This output is intended for BAS use only.

    Generates lightweight representations of Items for searching in-scope Records within the BAS public website
    (www.bas.ac.uk) to aid discovery and improve integration. These representations are further processed by an external
    API to aggregate resources across BAS catalogues to then sync with the public website search index.

    See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450 for background information.

    Workflow:

    1. create Website Search Items from Records
    2. filters these Items to only include Items which are:
        1. open access (based on an `unrestricted` resource permissions)
        2. not superseded by another Item (based on not being the target of any `RevisionOf` aggregations)

    Note: This second filtering condition is not implemented efficiently as it requires a reverse lookup.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, select_records: SelectRecordsProtocol) -> None:
        super().__init__(
            logger=logger,
            meta=meta,
            name="Items Public Website Search Results",
            check_type=CheckType.BAS_WEBSITE_SEARCH,
            select_records=select_records,
        )

    @property
    def _object_meta(self) -> dict[str, str]:
        return {"build_ref": self._meta.build_repo_ref} if self._meta.build_repo_ref else {}

    @staticmethod
    def _get_superseded_records(records: list[RecordRevision]) -> list[str]:
        """List identifiers of records superseded by other records."""
        supersedes = set()
        for record in records:
            aggregations = record.identification.aggregations.filter(
                namespace=CATALOGUE_NAMESPACE, associations=AggregationAssociationCode.REVISION_OF
            )
            supersedes.update(aggregations.identifiers())
        return list(supersedes)

    @property
    def _in_scope_items(self) -> list[ItemWebsiteSearch]:
        """
        Items in-scope for public website search.

        See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450/#note_142966 for initial criteria.
        """
        records = self._select_records()
        superseded = self._get_superseded_records(records)
        items = [
            ItemWebsiteSearch(
                record=record,
                admin_meta_keys=self._meta.admin_meta_keys,
                source=self._meta.generator,
                base_url=self._meta.base_url,
            )
            for record in records
        ]
        filtered_items = [item for item in items if item.resource_id not in superseded and item.open_access]
        self._logger.debug(
            f"{len(filtered_items)} items of {len(items)} in-scope for website search ({len(superseded)} superseded, "
            f"{len(filtered_items) - len(superseded)} not open-access)."
        )
        return filtered_items

    @property
    def _content(self) -> str:
        """Generate aggregation API resources for in-scope items."""
        payload = [item.dumps() for item in self._in_scope_items]
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @property
    def content(self) -> list[SiteContent]:
        """Output content aggregating all items."""
        return [
            SiteContent(
                content=self._content,
                path=Path("-") / "public-website-search" / "items.json",
                media_type="application/json",
                object_meta=self._object_meta,
            )
        ]
