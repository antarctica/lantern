import logging
from collections.abc import Collection
from pathlib import Path
from typing import get_args

from mypy_boto3_s3 import S3Client

from lantern.catalogues.base import CatalogueBase
from lantern.checks import Checker
from lantern.config import Config
from lantern.exporters.rsync import RsyncExporter
from lantern.exporters.s3 import S3Exporter
from lantern.models.checks import CheckType
from lantern.models.record.record import Record
from lantern.models.repository import GitUpsertContext, GitUpsertResults
from lantern.models.site import ExportMeta, SiteEnvironment
from lantern.outputs.base import OutputBase
from lantern.outputs.item_html import ItemCatalogueOutput
from lantern.repositories.bas import BasRepository
from lantern.site import Site


class BasCatUntrusted(CatalogueBase):
    """
    BAS data catalogue untrusted site.

    Sub-catalogue within an environment within a BasCatalogue instance.

    Manages unrestricted (public) content for all site outputs (except trusted content), uploaded to AWS S3.
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        repo: BasRepository,
        s3: S3Client,
        bucket: str,
        env: SiteEnvironment,
    ) -> None:
        super().__init__(logger)
        self._config = config
        self._repo = repo
        self._env = env

        self._exporter = S3Exporter(logger=logger, s3=s3, bucket=bucket, parallel_jobs=config.PARALLEL_JOBS)
        self._checker = Checker(logger=self._logger, parallel_jobs=config.PARALLEL_JOBS)

    def export(
        self,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Generate and export site content to hosting.

        Optionally for selected records from a branch for selected output types.

        Site requires direct access to underlying store for additional processing.
        """
        store = self._repo._make_gitlab_store(branch=branch, cached=True, frozen=True)
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=store.head_commit, trusted=False)
        site = Site(logger=self._logger, meta=meta, store=store)
        global_, individual = self._group_output_classes(outputs=outputs)

        content = site.generate_content(global_outputs=global_, individual_outputs=individual, identifiers=identifiers)
        self._exporter.export(content)

    def check(
        self,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Check site contents (optionally for selected records).

        Optionally for selected records from a branch for selected output types.

        When not using the live site, filter out DOI checks as these are set externally for the live endpoint only.

        Site requires direct access to underlying store for additional processing.
        """
        store = self._repo._make_gitlab_store(branch=branch, cached=True, frozen=True)
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=store.head_commit, trusted=False)
        site = Site(logger=self._logger, meta=meta, store=store)
        global_, individual = self._group_output_classes(outputs=outputs)

        checks = site.generate_checks(global_outputs=global_, individual_outputs=individual, identifiers=identifiers)
        if self._env != "live":
            checks = [check for check in checks if check.type != CheckType.DOI_REDIRECTS]

        content = self._checker.check(meta=meta, checks=checks)
        self._exporter.export(content)


class BasCatTrusted(CatalogueBase):
    """
    BAS data catalogue trusted site.

    Sub-catalogue within an environment within a BasCatalogue instance.

    Manages restricted content for catalogue items only to support viewing administration metadata.

    Uses the BAS Operations Data Store as a trusted host, responsible for controlling access.
    """

    def __init__(
        self, logger: logging.Logger, config: Config, repo: BasRepository, host: str, path: Path, env: SiteEnvironment
    ) -> None:
        super().__init__(logger)
        self._config = config
        self._repo = repo
        self._env = env

        self._exporter = RsyncExporter(logger=logger, host=host, path=path)

    def export(self, identifiers: set[str] | None = None, branch: str | None = None) -> None:
        """
        Generate and export site content to hosting.

        Optionally for selected records from a branch. Output classes are fixed for the trusted site environment.
        """
        store = self._repo._make_gitlab_store(branch=branch, cached=True, frozen=True)
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=store.head_commit, trusted=True)
        site = Site(logger=self._logger, meta=meta, store=store)

        content = site.generate_content(
            global_outputs=[], individual_outputs=[ItemCatalogueOutput], identifiers=identifiers
        )
        self._exporter.export(content)

    def check(self, identifiers: set[str] | None = None) -> None:
        """
        Check site contents (optionally for selected Records).

        Trusted site content is not validated due to Ops Data Store auth. See docs/monitoring.md for details.
        """
        raise NotImplementedError


class BasCatEnv(CatalogueBase):
    """
    BAS data catalogue environment.

    Sub-catalogue within a BasCatalogue instance. Consists of two sites, trusted and untrusted.
    """

    def __init__(
        self, logger: logging.Logger, config: Config, repo: BasRepository, s3: S3Client, env: SiteEnvironment
    ) -> None:
        super().__init__(logger)
        config = config
        repo = repo
        s3 = s3
        self._env = env

        bucket = config.SITE_UNTRUSTED_S3_BUCKET_TESTING if env == "testing" else config.SITE_UNTRUSTED_S3_BUCKET_LIVE
        path = Path(
            config.SITE_TRUSTED_RSYNC_BASE_PATH_TESTING
            if env == "testing"
            else config.SITE_TRUSTED_RSYNC_BASE_PATH_LIVE
        )

        self._untrusted = BasCatUntrusted(
            logger=self._logger, config=config, repo=repo, s3=s3, bucket=bucket, env=self._env
        )

        self._trusted = BasCatTrusted(
            logger=self._logger,
            config=config,
            repo=repo,
            host=config.SITE_TRUSTED_RSYNC_HOST,
            path=path,
            env=self._env,
        )

    def export(
        self,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """Generate and export site content to hosting."""
        self._logger.info(f"Exporting untrusted {self._env} site")
        self._untrusted.export(identifiers=identifiers, branch=branch, outputs=outputs)
        self._logger.info(f"Exporting trusted {self._env} site")
        self._trusted.export(identifiers=identifiers, branch=branch)

    def check(
        self,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Verify untrusted site contents (optionally for selected records).

        Trusted site content is not validated due to Ops Data Store auth. See docs/monitoring.md for details.
        """
        self._logger.info(f"Verifying untrusted {self._env} site")
        self._untrusted.check(identifiers=identifiers, branch=branch, outputs=outputs)


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

    Uses a BasRepository as a wrapper around a branch based GitLab records Store.
    """

    def __init__(self, logger: logging.Logger, config: Config, s3: S3Client) -> None:
        self._logger = logger
        self._config = config
        self._s3 = s3
        self.repo = BasRepository(logger=logger, config=self._config)

        self._envs = {
            env: BasCatEnv(logger=logger, config=config, repo=self.repo, s3=s3, env=env)
            for env in get_args(SiteEnvironment)
        }

    def commit(self, records: Collection[Record], context: GitUpsertContext) -> GitUpsertResults:
        """
        Add or update a set of Records to underlying Stores.

        This action is global for all site environments.

        Requires additional context for who authored the changes and why.
        """
        return self.repo.upsert(records=records, context=context)

    def export(
        self,
        env: SiteEnvironment,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Export generated sites to relevant hosting.

        Output classes are fixed for the trusted site environment.
        """
        self._envs[env].export(identifiers=identifiers, branch=branch, outputs=outputs)

    def check(
        self,
        env: SiteEnvironment,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Check catalogue site contents (optionally for selected records).

        Trusted site content is not validated due to Ops Data Store auth. See docs/monitoring.md for details.
        """
        self._envs[env].check(identifiers=identifiers, branch=branch, outputs=outputs)
