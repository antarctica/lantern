from tasks._record_utils import confirm_branch, init

from lantern.exporters.verification import VerificationExporter
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext


def main() -> None:
    """Entrypoint."""
    base_url = "https://data.bas.ac.uk"
    selected = set()  # to set use the form {"abc", "..."}

    logger, config, store, s3, _keys = init()
    context: VerificationContext = {
        "BASE_URL": base_url,
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
        "SAN_PROXY_ENDPOINT": config.VERIFY_SAN_PROXY_ENDPOINT,
    }

    confirm_branch(logger=logger, store=store, action="Validating records from")
    store.populate()
    meta = ExportMeta.from_config_store(config=config, store=None, build_repo_ref=store.head_commit)
    exporter = VerificationExporter(logger=logger, meta=meta, s3=s3, get_record=store.get, context=context)
    exporter.selected_identifiers = {record.file_identifier for record in store.records}
    if selected:
        exporter.selected_identifiers = selected
    exporter.run()
    exporter.export()
    logger.info(f"Verify report with {len(exporter.report)} tests saved.")


if __name__ == "__main__":
    main()
