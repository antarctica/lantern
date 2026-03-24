import logging

from tasks._record_utils import init, time_task

from lantern.exporters.base import ExporterBase
from lantern.exporters.rsync import RsyncExporter
from lantern.exporters.s3 import S3Exporter
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_api import SiteApiOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.outputs.site_pages import SitePagesOutput
from lantern.outputs.site_resources import SiteResourcesOutput
from lantern.site import Site
from lantern.stores.base import Store


@time_task(label="Creating outputs")
def _create_outputs(
    logger: logging.Logger, meta: ExportMeta, store: Store, identifiers: set[str]
) -> tuple[list[SiteContent], list[SiteContent]]:
    records_len = len(identifiers) if identifiers else len(store.select())

    # untrusted / external
    untrusted_outputs = []
    logger.info(f"Creating untrusted (public) outputs for site and {records_len} records...")
    untrusted_generator = Site(logger=logger, meta=meta, store=store)
    untrusted_outputs.extend(
        untrusted_generator.run(
            global_outputs=[
                SiteResourcesOutput,
                SiteIndexOutput,
                SitePagesOutput,
                SiteApiOutput,
                SiteHealthOutput,
                RecordsWafOutput,
                ItemsBasWebsiteOutput,
            ],
            individual_outputs=[
                ItemCatalogueOutput,
                ItemAliasesOutput,
                RecordIsoJsonOutput,
                RecordIsoXmlOutput,
                RecordIsoHtmlOutput,
            ],
            identifiers=identifiers,
        )
    )

    # trusted / internal
    meta.trusted = True
    trusted_generator = Site(logger=logger, meta=meta, store=store)
    logger.info(f"Creating trusted (private) outputs for {records_len} records...")
    trusted_outputs = trusted_generator.run(
        global_outputs=[],
        individual_outputs=[ItemCatalogueOutput],
        identifiers=identifiers,
    )
    meta.trusted = False

    outputs = untrusted_outputs + trusted_outputs
    logger.info(f"Created {len(outputs)} outputs")
    return untrusted_outputs, trusted_outputs


@time_task(label="Untrusted export")
def _export_untrusted(logger: logging.Logger, exporter: ExporterBase, content: list[SiteContent]) -> None:
    """Wrapper method for timing."""
    logger.info(f"Exporting {len(content)} untrusted (public) content items...")
    exporter.export(content)


@time_task(label="Trusted export")
def _export_trusted(logger: logging.Logger, exporter: ExporterBase, content: list[SiteContent]) -> None:
    """Wrapper method for timing."""
    logger.info(f"Exporting {len(content)} trusted (private) content items...")
    exporter.export(content)


@time_task(label="Site export")
def main() -> None:
    """Entrypoint."""
    selected = set()  # to set use the form {"abc", "..."}

    logger, config, store, s3 = init(cached_store=True, frozen_store=True)
    meta = ExportMeta.from_config_store(config=config, store=store, trusted=False)
    untrusted_exporter = S3Exporter(logger=logger, s3=s3, bucket=config.AWS_S3_BUCKET)
    trusted_exporter = RsyncExporter(logger=logger, host=config.TRUSTED_UPLOAD_HOST, path=config.TRUSTED_UPLOAD_PATH)

    untrusted_outputs, trusted_outputs = _create_outputs(logger=logger, meta=meta, store=store, identifiers=selected)
    _export_untrusted(logger=logger, exporter=untrusted_exporter, content=untrusted_outputs)
    _export_trusted(logger=logger, exporter=trusted_exporter, content=trusted_outputs)


if __name__ == "__main__":
    main()
