from __future__ import annotations

# ruff: noqa: N812
from pathlib import Path
from typing import TYPE_CHECKING, get_args

from boto3 import client as BotoClient

from lantern.catalogues.base import CatalogueBase, group_output_classes
from lantern.checks import Checker
from lantern.exporters.cloudfront import CloudFrontExporter
from lantern.exporters.rsync import RsyncExporter
from lantern.exporters.s3 import S3Exporter
from lantern.models.checks import Check, CheckType
from lantern.models.site import ExportMeta, SiteContent, SiteEnvironment
from lantern.outputs.item_html import ItemCatalogueOutput
from lantern.outputs.redirects import RedirectsOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.repositories.bas import BasRepository
from lantern.site import Site

if TYPE_CHECKING:
    import logging
    from collections.abc import Collection

    from mypy_boto3_cloudfront import CloudFrontClient
    from mypy_boto3_s3 import S3Client

    from lantern.config import Config
    from lantern.models.record.record import Record
    from lantern.models.repository import GitUpsertContext, GitUpsertResults
    from lantern.outputs.base import OutputBase
    from lantern.repositories.base import RecordsProtocol

# AWS has a 150/second invalidations limit. Above this invalidating the whole distribution is cheaper and faster.
MAX_INVALIDATION_KEYS = 140


class BasCatUntrusted:
    """
    BAS data catalogue untrusted site.

    Sub-catalogue within an environment within a `BasCatEnv` sub-catalogue.

    Manages unrestricted (public) content for all site outputs, uploaded to AWS S3.

    Supports optional cache invalidation within a CloudFront distribution.
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        repo: BasRepository,
        s3: S3Client,
        bucket: str,
        distribution: str | None,
        env: SiteEnvironment,
    ) -> None:
        self._logger = logger
        self._config = config
        self._repo = repo
        self._s3 = s3
        self._env = env

        self._invalidator: CloudFrontExporter | None = None
        if env == "live" and distribution is not None:
            cf_client = self._create_cf_client()
            self._invalidator = CloudFrontExporter(logger=logger, cloudfront=cf_client, distribution=distribution)
        self._exporter = S3Exporter(logger=logger, s3=self._s3, bucket=bucket, parallel_jobs=config.PARALLEL_JOBS)

    def _create_cf_client(self) -> CloudFrontClient:
        """Create CloudFront boto client."""
        return BotoClient(
            "cloudfront",
            aws_access_key_id=self._config.SITE_UNTRUSTED_AWS_ACCESS_ID,
            aws_secret_access_key=self._config.SITE_UNTRUSTED_AWS_ACCESS_SECRET,
            region_name="us-east-1",
        )

    def export_content(self, content: list[SiteContent]) -> None:
        """Export pre-generated content to hosting."""
        self._exporter.export(content)

    def export(
        self,
        records: RecordsProtocol,
        identifiers: set[str] | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Generate and export site content to hosting.

        Optionally for selected records from a branch and for selected Output types.
        """
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=records.head_commit, trusted=False)
        global_, individual = group_output_classes(outputs=outputs)
        site_extras = {}
        content_params = {"global_outputs": global_, "individual_outputs": individual, "identifiers": identifiers}

        # include extras needed for some outputs
        if SiteHealthOutput in global_:
            site_extras["site_records_count"] = records.record_count
            site_extras["search_records_count"] = self._repo.search_record_count
            site_extras["entra_secret_expiry"] = self._config.CHECKS_MAGIC_RESOURCES_CLIENT_SECRET_EXP
            site_extras["entra_secret_id"] = self._config.CHECKS_MAGIC_RESOURCES_CLIENT_SECRET_ID

        site = Site(logger=self._logger, meta=meta, records=records, extras=site_extras)
        content = site.generate_content(**content_params)
        if outputs is None or RedirectsOutput in outputs:
            content.extend(RedirectsOutput(logger=self._logger, meta=meta, content=content).content)
        self._exporter.export(content)

        if self._invalidator:
            # Generate keys from site entries to avoid generating content we don't need.
            # Where keys get close to the AWS limit, invalidate the entire site instead.
            manifest_keys = site.generate_invalidation_keys(**content_params)
            keys = manifest_keys if 0 < len(manifest_keys) <= MAX_INVALIDATION_KEYS else ["/*"]
            self._invalidator.invalidate(keys)

    def checks(
        self,
        records: RecordsProtocol,
        identifiers: set[str] | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> list[Check]:
        """
        Generate checks from site entries.

        Optionally for selected records from a branch and for selected Output types.

        When not using the live site, filter out DOI checks as these are set externally for the live endpoint only.

        Site entries used to avoid generating content we don't need (i.e. generating checks doesn't need actual content).
        """
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=records.head_commit, trusted=False)
        site = Site(logger=self._logger, meta=meta, records=records)
        global_, individual = group_output_classes(outputs=outputs)

        checks = site.generate_checks(global_outputs=global_, individual_outputs=individual, identifiers=identifiers)
        if self._env != "live":
            checks = [check for check in checks if check.type != CheckType.DOI_REDIRECTS]
        return checks


class BasCatTrusted:
    """
    BAS data catalogue trusted site.

    Sub-catalogue within an environment within a `BasCatEnv` sub-catalogue.

    Manages restricted versions of catalogue items outputs to support viewing administration metadata only.

    Uses the BAS Operations Data Store as a trusted host exported responsible for controlling access via Rsync.
    """

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        repo: BasRepository,
        host: str | None,
        path: Path,
        env: SiteEnvironment,
    ) -> None:
        self._logger = logger
        self._config = config
        self._repo = repo
        self._env = env
        self._exporter = RsyncExporter(logger=logger, host=host, path=path)

    def export(self, records: RecordsProtocol, identifiers: set[str] | None = None) -> None:
        """
        Generate and export site content to hosting.

        Optionally for selected records from a branch. Output classes are fixed for the trusted site environment.
        """
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=records.head_commit, trusted=True)
        site = Site(logger=self._logger, meta=meta, records=records)

        content = site.generate_content(
            global_outputs=[], individual_outputs=[ItemCatalogueOutput], identifiers=identifiers
        )
        self._exporter.export(content)

    def checks(self, records: RecordsProtocol, identifiers: set[str] | None = None) -> list[Check]:
        """
        Generate checks from site entries.

        Optionally for selected records from a branch. Output classes are fixed for the trusted site environment.

        Trusted content is reverse proxied to appear at a prefixed path. The URLs in generated checks are not aware of
        this prefix and so need correcting before checking.

        Trusted content requires authentication to access. Generated checks are not aware of this requirement and so
        need updating before checking.

        Site entries used to avoid generating content we don't need (i.e. generating checks doesn't need actual content).
        """
        meta = ExportMeta.from_config(config=self._config, env=self._env, build_ref=records.head_commit, trusted=True)
        site = Site(logger=self._logger, meta=meta, records=records)

        checks = site.generate_checks(
            global_outputs=[], individual_outputs=[ItemCatalogueOutput], identifiers=identifiers
        )
        for check in checks:
            check.url = check.url.replace("/items/", "/-/items/")
            check.type = CheckType.ITEM_PAGES_TRUSTED
        return checks


class BasCatEnv(CatalogueBase):
    """
    BAS data catalogue environment.

    Sub-catalogue within a `BasCatalogue`. Consists of two `BasCatTrusted` and `BasCatUntrusted` sub-catalogues:
    - untrusted (public): for the vast majority of site content, hosted on AWS S3
    - trusted (restricted): for Items with administration metadata only, hosted within the BAS Operations Data Store

    These sites form a logical whole, with this class acting as an entrypoint and router. A common `Checks` instance
    is used for the overall logical site. Sub-catalogues manage specific Site and Exporter instances.
    """

    def __init__(
        self, logger: logging.Logger, config: Config, repo: BasRepository, s3: S3Client, env: SiteEnvironment
    ) -> None:
        super().__init__(logger)
        self._config = config
        self._repo = repo
        self._env = env

        self._bucket = (
            config.SITE_UNTRUSTED_S3_BUCKET_LIVE if env == "live" else config.SITE_UNTRUSTED_S3_BUCKET_TESTING
        )
        distribution = config.SITE_UNTRUSTED_CLOUDFRONT_DIST_LIVE if env == "live" else None
        path = Path(
            config.SITE_TRUSTED_RSYNC_BASE_PATH_LIVE if env == "live" else config.SITE_TRUSTED_RSYNC_BASE_PATH_TESTING
        )

        self._untrusted = BasCatUntrusted(
            logger=self._logger,
            config=self._config,
            repo=self._repo,
            s3=s3,
            distribution=distribution,
            bucket=self._bucket,
            env=self._env,
        )
        self._trusted = BasCatTrusted(
            logger=self._logger,
            config=self._config,
            repo=self._repo,
            host=config.SITE_TRUSTED_RSYNC_HOST,
            path=path,
            env=self._env,
        )
        self._checker = Checker(logger=self._logger, config=self._config)

    def export(
        self,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Generate and export catalogue site content.

        Export is delegated to each site as different exporters and build context are used.
        """
        with self._repo.snapshot(branch) as records:
            self._logger.info("Exporting untrusted %s site", self._env)
            self._untrusted.export(records=records, identifiers=identifiers, outputs=outputs)
            if outputs is None or ItemCatalogueOutput in outputs:
                self._logger.info("Exporting trusted %s site", self._env)
                self._trusted.export(records=records, identifiers=identifiers)

    def check(
        self,
        identifiers: set[str] | None = None,
        branch: str | None = None,
        outputs: list[type[OutputBase]] | None = None,
    ) -> None:
        """
        Check catalogue site contents (optionally for selected records).

        Checks are executed at this level to produce a combined report for checks from the trusted and untrusted Sites.
        """
        with self._repo.snapshot(branch) as records:
            meta = ExportMeta.from_config(
                config=self._config, env=self._env, build_ref=records.head_commit, trusted=False
            )

            self._logger.info("Generating checks for untrusted %s site", self._env)
            checks = self._untrusted.checks(identifiers=identifiers, records=records, outputs=outputs)
            if outputs is None or ItemCatalogueOutput in outputs:
                self._logger.info("Generating checks for trusted %s site", self._env)
                checks.extend(self._trusted.checks(identifiers=identifiers, records=records))

            self._logger.info("Checking %s site", self._env)
            content = self._checker.check(meta=meta, checks=checks)
            self._untrusted.export_content(content)


class BasCatalogue:
    """
    British Antarctic Survey data catalogue.

    Consists of three environments:
    - testing: for publishers to preview records and site changes
    - live: for general use

    Each environment is managed as a `BasCatEnv` sub-catalogue, with this class acting as an entrypoint and router.
    A common `BasRepository` is used for records access.
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
        return self.repo.upsert_records(records=records, context=context)

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
