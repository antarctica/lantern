import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import get_args

from mypy_boto3_s3 import S3Client

from lantern.checks import Checker
from lantern.config import Config
from lantern.exporters.rsync import RsyncExporter
from lantern.exporters.s3 import S3Exporter
from lantern.models.checks import CheckType
from lantern.models.site import ExportMeta, SiteEnvironment
from lantern.outputs.base import OutputBase
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
from lantern.stores.gitlab import GitLabStore


class CatalogueBase(ABC):
    """
    Abstract base class for a catalogue.

    Catalogues are responsible at a high level for managing a set of Records and transforming these into a static site
    built from representations of these Records plus global/static content.

    Combines and coordinates one or more Stores, Outputs, Sites and Exporters.

    This base Catalogue class is intended to be generic and minimal, with subclasses being more opinionated.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @staticmethod
    def _group_output_classes(
        outputs: list[type[OutputBase]] | None = None,
    ) -> tuple[list[type[OutputBase]], list[type[OutputBase]]]:
        """Sort selected output classes into individual and global types, or return all classes."""
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


class BasCatUntrusted(CatalogueBase):
    """
    BAS data catalogue untrusted site.

    Sub-catalogue within an environment within a BasCatalogue instance.

    Manages unrestricted (public) content for all site outputs (except trusted content), uploaded to AWS S3.
    """

    def __init__(
        self,
        logger: logging.Logger,
        meta: ExportMeta,
        store: GitLabStore,
        s3: S3Client,
        bucket: str,
    ) -> None:
        super().__init__(logger)
        self._meta = meta
        self._store = store

        self._site = Site(logger=logger, meta=self._meta, store=self._store)
        self._exporter = S3Exporter(logger=logger, s3=s3, bucket=bucket, parallel_jobs=self._meta.parallel_jobs)
        self._checker = Checker(logger=self._logger, meta=self._meta)

    def export(self, identifiers: set[str] | None = None, outputs: list[type[OutputBase]] | None = None) -> None:
        """Generate and export site content to hosting."""
        global_, individual = self._group_output_classes(outputs=outputs)
        content = self._site.generate_content(
            global_outputs=global_, individual_outputs=individual, identifiers=identifiers
        )
        self._exporter.export(content)

    def check(self, identifiers: set[str] | None = None, outputs: list[type[OutputBase]] | None = None) -> None:
        """Check site contents (optionally for selected records)."""
        global_, individual = self._group_output_classes(outputs=outputs)
        checks = self._site.generate_checks(
            global_outputs=global_, individual_outputs=individual, identifiers=identifiers
        )

        # filter out DOI checks if not using live site
        if self._meta.base_url != "https://data.bas.ac.uk":
            checks = [check for check in checks if check.type != CheckType.DOI_REDIRECTS]

        content = self._checker.check(checks)
        self._exporter.export(content)


class BasCatTrusted(CatalogueBase):
    """
    BAS data catalogue trusted site.

    Sub-catalogue within an environment within a BasCatalogue instance.

    Manages restricted content for catalogue items only to support viewing administration metadata.

    Uses the BAS Operations Data Store as a trusted host, responsible for controlling access.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, store: GitLabStore, host: str, path: Path) -> None:
        super().__init__(logger)
        self._site = Site(logger=logger, meta=meta, store=store)
        self._exporter = RsyncExporter(logger=logger, host=host, path=path)

    def export(self, identifiers: set[str] | None = None, outputs: list[type[OutputBase]] | None = None) -> None:
        """
        Generate and export site content to hosting.

        Output classes cannot be set for the trusted site.
        """
        content = self._site.generate_content(
            global_outputs=[], individual_outputs=[ItemCatalogueOutput], identifiers=identifiers
        )
        self._exporter.export(content)

    def check(self, identifiers: set[str] | None = None) -> None:
        """
        Check site contents (optionally for selected records).

        Trusted site content is not validated due to Ops Data Store auth. See docs/monitoring.md for details.
        """
        raise NotImplementedError


class BasCatEnv(CatalogueBase):
    """
    BAS data catalogue environment.

    Sub-catalogue within a BasCatalogue instance. Consists of two sites, trusted and untrusted.
    """

    def __init__(
        self, logger: logging.Logger, config: Config, store: GitLabStore, s3: S3Client, env: SiteEnvironment
    ) -> None:
        super().__init__(logger)
        self._config = config
        self._store = store
        self._s3 = s3
        self._env = env

        meta_untrusted = ExportMeta.from_config_store(
            config=self._config, env=self._env, store=self._store, trusted=False
        )
        meta_trusted = ExportMeta.from_config_store(config=self._config, env=self._env, store=self._store, trusted=True)
        bucket = config.SITE_UNTRUSTED_S3_BUCKET_TESTING if env == "testing" else config.SITE_UNTRUSTED_S3_BUCKET_LIVE
        path = Path(
            config.SITE_TRUSTED_RSYNC_BASE_PATH_TESTING
            if env == "testing"
            else config.SITE_TRUSTED_RSYNC_BASE_PATH_LIVE
        )

        self._untrusted = BasCatUntrusted(logger=self._logger, meta=meta_untrusted, store=store, s3=s3, bucket=bucket)

        self._trusted = BasCatTrusted(
            logger=self._logger,
            meta=meta_trusted,
            store=store,
            host=config.SITE_TRUSTED_RSYNC_HOST,
            path=path,
        )

    def export(self, identifiers: set[str] | None = None, outputs: list[type[OutputBase]] | None = None) -> None:
        """Generate and export site content to hosting."""
        self._logger.info(f"Exporting untrusted {self._env} site")
        self._untrusted.export(identifiers=identifiers, outputs=outputs)
        self._logger.info(f"Exporting trusted {self._env} site")
        self._trusted.export(identifiers=identifiers, outputs=outputs)

    def check(self, identifiers: set[str] | None = None) -> None:
        """
        Verify untrusted site contents (optionally for selected records).

        Trusted site content is not validated due to Ops Data Store auth. See docs/monitoring.md for details.
        """
        self._logger.info(f"Verifying untrusted {self._env} site")
        self._untrusted.check(identifiers=identifiers)


class BasCatalogue:
    """
    British Antarctic Survey data catalogue.

    Consists of two environments:
    - testing: for publishers to preview records and site changes
    - live: for general use

    And two sites within each environment:
    - untrusted (public): for the vast majority of site content, hosted on AWS S3
    - a trusted (restricted) for Items with administration metadata included, hosted within the BAS Operations Data Store

    Each environment and site is managed as a sub-catalogue, with this class acting as an entrypoint and coordinator.

    Uses GitLab as a Records Store.
    """

    def __init__(self, logger: logging.Logger, config: Config, store: GitLabStore, s3: S3Client) -> None:
        self._logger = logger
        self._config = config
        self._store = store
        self._s3 = s3

        self._envs = {
            env: BasCatEnv(logger=logger, config=config, store=store, s3=s3, env=env)
            for env in get_args(SiteEnvironment)
        }

    def export(
        self,
        env: SiteEnvironment,
        identifiers: set[str] | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """Export generated sites to relevant hosting."""
        self._envs[env].export(identifiers=identifiers, outputs=outputs)

    def check(self, env: SiteEnvironment, identifiers: set[str] | None = None) -> None:
        """
        Check catalogue site contents (optionally for selected records).

        Trusted site content is not validated due to Ops Data Store auth. See docs/monitoring.md for details.
        """
        self._envs[env].check(identifiers=identifiers)
