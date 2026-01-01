from tasks._record_utils import confirm_source, init

from lantern.exporters.verification import VerificationExporter
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext


def main() -> None:
    """Entrypoint."""
    base_url = "https://data.bas.ac.uk"
    selected = {"00203387-0840-447c-b9ae-f25088501031"}  # set()  # to set use the form {"abc", "..."}

    logger, config, store, s3, _keys = init()
    context: VerificationContext = {
        "BASE_URL": base_url,
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
        "SAN_PROXY_ENDPOINT": config.VERIFY_SAN_PROXY_ENDPOINT,
    }

    confirm_source(logger=logger, store=store, action="Validating records from")
    if store.head_commit is None:
        # noinspection PyProtectedMember
        store._cache._ensure_exists()  # ensure cache exists to get head commit for ExportMeta
    meta = ExportMeta.from_config_store(config=config, store=None, build_repo_ref=store.head_commit, trusted=False)
    exporter = VerificationExporter(
        logger=logger, meta=meta, s3=s3, context=context, select_records=store.select, selected_identifiers=selected
    )
    exporter.run()
    exporter.export()
    logger.info("Verify report saved.")


if __name__ == "__main__":
    main()
