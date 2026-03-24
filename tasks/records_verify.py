from tasks._record_utils import confirm_source, init

from lantern.exporters.local import LocalExporter
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext
from lantern.verification import Verification


def main() -> None:
    """Entrypoint."""
    base_url = "https://data.bas.ac.uk"
    identifiers = set()  # to set use the form {"abc", "..."}

    logger, config, store, _s3 = init(cached_store=True)
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
    verifier = Verification(
        logger=logger, meta=meta, context=context, select_records=store.select, identifiers=identifiers
    )
    verifier.run()
    exporter = LocalExporter(logger=logger, path=config.EXPORT_PATH)
    exporter.export(verifier.outputs)
    logger.info("Verify data and report saved.")


if __name__ == "__main__":
    main()
