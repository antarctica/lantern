import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from mypy_boto3_s3 import S3Client

from lantern.exporters.base import ResourceExporter
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.base import SelectRecordProtocol
from lantern.utils import RsyncUtils, dumps_redirect, get_jinja_env, get_record_aliases, prettify_html


class HtmlExporter(ResourceExporter):
    """
    Data Catalogue HTML item exporter.

    Exports a Record as ItemCatalogue HTML.

    Intended as the primary human-readable representation of a record.

    Supports trusted publishing.
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        s3: S3Client,
        record: RecordRevision,
        select_record: SelectRecordProtocol,
    ) -> None:
        """Initialise."""
        export_base = meta.export_path / "items" / record.file_identifier
        export_name = "index.html"
        super().__init__(
            logger=logger, meta=meta, s3=s3, record=record, export_base=export_base, export_name=export_name
        )
        self._select_record = select_record
        self._jinja = get_jinja_env()
        self._template_path = "_views/item.html.j2"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Item HTML"

    def _item_class(self) -> type[ItemCatalogue]:
        """Get the ItemCatalogue (sub-)class to use for this record."""
        if ItemCataloguePhysicalMap.matches(self._record):
            return ItemCataloguePhysicalMap
        return ItemCatalogue

    def dumps(self) -> str:
        """Encode record as data catalogue item in HTML."""
        item_class = self._item_class()
        item = item_class(
            site_meta=self._meta.site_metadata,
            record=self._record,
            admin_meta_keys=self._meta.admin_meta_keys,  # ty: ignore[invalid-argument-type]
            trusted_context=self._meta.trusted,
            select_record=self._select_record,
        )

        raw = self._jinja.get_template(self._template_path).render(item=item, meta=item.site_metadata)
        return prettify_html(raw)

    def _publish_trusted(self) -> None:
        """
        Save dumped output to secure hosting via rsync.

        Group write permissions are set on uploaded files (660) and directories (770) to allow shared management.
        """
        with TemporaryDirectory() as tmp_path:
            base_path = Path(tmp_path)

        items_source = base_path / "items"
        item_path = items_source / self._record.file_identifier / "index.html"
        env_path = "testing" if "testing" in self._meta.s3_bucket else "live"
        items_target = self._meta.trusted_path / env_path / "items"  # ty:ignore[unsupported-operator]

        item_path.parent.mkdir(parents=True, exist_ok=True)
        with item_path.open("w") as record_file:
            record_file.write(self.dumps())
        item_path.parent.chmod(0o770)
        item_path.chmod(0o660)

        sync = RsyncUtils(logger=self._logger)
        sync.put(src_path=items_source, target_path=items_target, target_host=self._meta.trusted_host)

    def publish(self) -> None:
        """Save dumped output to remote S3 bucket, or secure hosting if in trusted context."""
        if self._meta.trusted:
            self._publish_trusted()
            return
        super().publish()


class HtmlAliasesExporter(ResourceExporter):
    """
    HTML aliases exporter.

    Creates redirects back to Data Catalogue item pages for any aliases set within a Record.

    Uses S3 object redirects with a minimal HTML page as a fallback.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, s3: S3Client, record: RecordRevision) -> None:
        """
        Initialise.

        The `export_name` parameter required by the base Exporter is not used by this class, its value is not used.

        The `export_base` parameter MUST be the root of the overall site/catalogue output directory, so aliases under
        various prefixes can be generated.
        """
        export_base = meta.export_path
        export_name = f"--{record.file_identifier}--"
        self._site_base = export_base
        super().__init__(
            logger=logger, meta=meta, s3=s3, record=record, export_base=export_base, export_name=export_name
        )

    def _get_aliases(self) -> list[str]:
        """Get optional aliases for record as relative file paths / S3 keys."""
        identifiers = get_record_aliases(self._record)
        return [(identifier.href or "").replace(f"https://{CATALOGUE_NAMESPACE}/", "") for identifier in identifiers]

    @property
    def target(self) -> str:
        """Redirect location."""
        return f"/items/{self._record.file_identifier}/"

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Item Aliases"

    def dumps(self) -> str:
        """Generate redirect page for record."""
        return dumps_redirect(self.target)

    def export(self) -> None:
        """Write redirect pages for each alias to export directory."""
        for alias in self._get_aliases():
            alias_path = self._export_path.parent / alias / "index.html"
            alias_path.parent.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Writing file: {alias_path.resolve()}")
            with alias_path.open("w") as alias_file:
                alias_file.write(self.dumps())

    def publish(self) -> None:
        """Write redirect pages with redirect headers to S3."""
        location = f"{self.target}index.html"
        for alias in self._get_aliases():
            self._s3_utils.upload_object(
                key=f"{alias}/index.html", content_type="text/html", body=self.dumps(), redirect=location
            )
