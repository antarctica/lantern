import json
import logging

from mypy_boto3_s3 import S3Client

from lantern.exporters.base import ResourcesExporter
from lantern.lib.metadata_library.models.record.enums import AggregationAssociationCode
from lantern.models.item.website.search import ItemWebsiteSearch
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordsProtocol


class WebsiteSearchExporter(ResourcesExporter):
    """
    Public Website search exporter.

    Note: Intended for BAS use only.

    Generates items for searching selected records within the BAS public website (www.bas.ac.uk) to aid discovery.
    Items are processed by an API to aggregate items across BAS data catalogues for syncing with the public website.

    See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450 for background information.

    This exporter:

    1. creates Website Search Items from records (which provide methods called during filtering)
    2. filters items locally to those which are:
        1. open access (based on an `unrestricted` access constraint)
        2. not superseded by another record (based on `RevisionOf` aggregations)

    Note: Due to the second filtering condition, this exporter cannot be implemented as a RecordExporter as foreign
    records determine whether a record is superseded rather than each target record independently.
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        select_records: SelectRecordsProtocol,
    ) -> None:
        """Initialise exporter."""
        super().__init__(logger=logger, meta=meta, s3=s3, select_records=select_records)
        self._export_path = self._meta.export_path / "-" / "public-website-search" / "items.json"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "BAS Public Website Search Results"

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
        Items in-scope for website search.

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

    def _dumps(self) -> str:
        """Generate aggregation API resources for in-scope items."""
        payload = [item.dumps() for item in self._in_scope_items]
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def export(self) -> None:
        """Export aggregation API resources to local directory."""
        self._logger.info("Exporting public website search items.")
        self._export_path.parent.mkdir(parents=True, exist_ok=True)
        with self._export_path.open("w") as f:
            f.write(self._dumps())

    def publish(self) -> None:
        """Publish aggregation API resources to S3."""
        self._logger.info("Publishing public website search items.")
        index_key = self._s3_utils.calc_key(self._export_path)
        self._s3_utils.upload_content(key=index_key, content_type="application/json", body=self._dumps())
