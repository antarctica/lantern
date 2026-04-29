import logging
from copy import deepcopy
from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from mypy_boto3_s3 import S3Client
from pytest_mock import MockerFixture

from lantern.catalogues.bas import BasCatalogue, BasCatEnv, BasCatTrusted, BasCatUntrusted
from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.identification import Aggregations
from lantern.models.checks import CheckType
from lantern.models.record.record import Record
from lantern.models.repository import GitUpsertContext, GitUpsertResults
from lantern.models.site import SiteEnvironment
from lantern.repositories.bas import BasRepository
from lantern.stores.gitlab import GitLabSource, GitLabStore
from tests.resources.records.item_cat_checks import record as all_checks_test_record

pytestmark = pytest.mark.usefixtures("fx_reset_site_singletons")


class TestBasCatUntrusted:
    """Test BAS data catalogue untrusted site."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_config: Config,
        fx_bas_repo: BasRepository,
        fx_s3_client: S3Client,
        fx_s3_bucket_name: str,
    ):
        """Can create a BAS untrusted catalogue instance."""
        cat = BasCatUntrusted(
            logger=fx_logger,
            config=fx_config,
            repo=fx_bas_repo,
            s3=fx_s3_client,
            bucket=fx_s3_bucket_name,
            env="testing",
        )
        assert isinstance(cat, BasCatUntrusted)

    def test_export(
        self,
        fx_bas_cat_untrusted: BasCatUntrusted,
        fx_s3_bucket_name: str,
    ):
        """Can generate and export site content for untrusted catalogue."""
        expected_keys = {"legal/accessibility/index.html", "-/index/index.html", "items/x/index.html", "records/x.xml"}

        fx_bas_cat_untrusted.export()

        result = fx_bas_cat_untrusted._exporter._s3.list_objects(Bucket=fx_s3_bucket_name)
        keys = {o["Key"] for o in result["Contents"]}
        assert keys.issuperset(expected_keys)

        item_object = fx_bas_cat_untrusted._exporter._s3.get_object(
            Bucket=fx_bas_cat_untrusted._exporter._bucket, Key="items/x/index.html"
        )
        assert item_object["ResponseMetadata"]["HTTPStatusCode"] == 200
        item_text = item_object["Body"].read().decode("utf-8")
        assert "tab-content-admin" not in item_text

    def test_check(self, fx_bas_cat_untrusted: BasCatUntrusted):
        """Can check untrusted site content."""
        fx_bas_cat_untrusted.check()

        result = fx_bas_cat_untrusted._exporter._s3.get_object(
            Bucket=fx_bas_cat_untrusted._exporter._bucket, Key="-/checks/data.json"
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestBasCatTrusted:
    """Test BAS data catalogue trusted site."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config, fx_bas_repo: BasRepository):
        """Can create a BAS trusted catalogue instance."""
        cat = BasCatTrusted(
            logger=fx_logger, config=fx_config, repo=fx_bas_repo, host="x", path=Path("x"), env="testing"
        )
        assert isinstance(cat, BasCatTrusted)

    def test_export(self, fx_bas_cat_trusted: BasCatTrusted):
        """Can export trusted site."""
        fx_bas_cat_trusted.export()

        trusted_path = fx_bas_cat_trusted._exporter._path
        item_path = trusted_path.joinpath("items/x/index.html")
        assert item_path.exists()

        with item_path.open() as f:
            item_text = f.read()
        assert "tab-content-admin" in item_text

    def test_check(self, fx_bas_cat_trusted: BasCatTrusted):
        """Cannot check trusted site (not supported)."""
        with pytest.raises(NotImplementedError):
            fx_bas_cat_trusted.check()


class TestBasCatEnv:
    """Test BAS data catalogue environment subclass."""

    def test_init(
        self, fx_logger: logging.Logger, fx_config: Config, fx_bas_repo: BasRepository, fx_s3_client: S3Client
    ):
        """
        Can create a BAS catalogue environment instance.

        Uses fake store over GitLab to avoid mocking and/or request recordings.
        """
        cat = BasCatEnv(logger=fx_logger, config=fx_config, repo=fx_bas_repo, s3=fx_s3_client, env="testing")
        assert isinstance(cat, BasCatEnv)
        assert isinstance(cat._untrusted, BasCatUntrusted)
        assert isinstance(cat._trusted, BasCatTrusted)

    def test_export(self, fx_bas_cat_env: BasCatEnv):
        """Can export static sites."""
        fx_bas_cat_env.export()

        result = fx_bas_cat_env._untrusted._exporter._s3.get_object(
            Bucket=fx_bas_cat_env._untrusted._exporter._bucket, Key="items/x/index.html"
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

        trusted_path = fx_bas_cat_env._trusted._exporter._path
        assert trusted_path.joinpath("items/x/index.html").exists()

    def test_check(self, mocker: MockerFixture, fx_bas_cat_env: BasCatEnv):
        """
        Can check catalogue contents.

        Checks are not actually run, this test only verifies the coordination logic.
        """
        mocker.patch.object(fx_bas_cat_env._untrusted, "check", return_value=None)
        fx_bas_cat_env.check()

    @pytest.mark.cov()
    @pytest.mark.parametrize("env", ["testing", "live"])
    def test_check_doi_filtering(
        self,
        mocker: MockerFixture,
        fx_logger: logging.Logger,
        fx_config: Config,
        fx_gitlab_source: GitLabSource,
        fx_bas_repo: BasRepository,
        fx_bas_cat_env: BasCatEnv,
        env: SiteEnvironment,
    ):
        """
        Can filter out DOI checks from non-live environment.

        The repo on the untrusted sub-catalogue is replaced with a mock that returns a test record with all check types
        (File ID: `cf80b941-3de6-4a04-8f5a-a2349c1e3ae0`).

        The checker on the untrusted sub-catalogue instance is replaced with a mock to capture the arguments passed to
        it to check DOI checks are removed if needed.
        """
        record = deepcopy(all_checks_test_record)
        record.identification.aggregations = Aggregations([])

        store = GitLabStore(logger=fx_logger, source=fx_gitlab_source, access_token=fx_config.STORE_GITLAB_TOKEN)
        mocker.patch.object(store, "select", return_value=[record])
        mocker.patch.object(store, "select_one", return_value=record)
        mocker.patch.object(type(store), "head_commit", new_callable=PropertyMock, return_value="x")
        mocker.patch.object(type(store), "_project", new_callable=PropertyMock, return_value="x")
        mocker.patch.object(fx_bas_repo, "_make_gitlab_store", return_value=store)
        fx_bas_cat_env._untrusted._repo = fx_bas_repo

        mock_checker = mocker.MagicMock()
        mocker.patch.object(fx_bas_cat_env._untrusted, "_checker", mock_checker)

        fx_bas_cat_env._untrusted._env = env

        fx_bas_cat_env.check()
        checks = mock_checker.check.call_args[1]["checks"]
        if env == "live":
            assert any(check.type == CheckType.DOI_REDIRECTS for check in checks)
        else:
            assert not any(check.type == CheckType.DOI_REDIRECTS for check in checks)


class TestBasCatalogue:
    """Test BAS data catalogue subclass."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config, fx_s3_client: S3Client):
        """Can create a BAS catalogue instance."""
        cat = BasCatalogue(logger=fx_logger, config=fx_config, s3=fx_s3_client)
        assert isinstance(cat, BasCatalogue)
        assert isinstance(cat._envs["testing"], BasCatEnv)
        assert isinstance(cat._envs["live"], BasCatEnv)

    def test_commit(self, mocker: MockerFixture, fx_bas_catalogue: BasCatalogue, fx_record_model_min: Record):
        """
        Can commit records to catalogue repository.

        Commits are not actually performed.
        """
        mocker.patch.object(
            fx_bas_catalogue.repo,
            "upsert",
            return_value=GitUpsertResults(
                branch="x",
                commit="x",
                new_identifiers=[fx_record_model_min.file_identifier],
                updated_identifiers=[],
            ),
        )

        result = fx_bas_catalogue.commit(
            records=[fx_record_model_min],
            context=GitUpsertContext(title="x", message="x", author_name="x", author_email="x"),
        )
        assert result is not None

    @pytest.mark.cov()
    @pytest.mark.parametrize("env", ["testing", "live"])
    def test_export(self, mocker: MockerFixture, fx_bas_catalogue: BasCatalogue, env: SiteEnvironment):
        """
        Can export environment's static site.

        Exports are not actually run, this test only verifies environment logic.
        """
        mocker.patch.object(fx_bas_catalogue._envs[env], "export", return_value=None)
        fx_bas_catalogue.export(env=env)

    @pytest.mark.cov()
    @pytest.mark.parametrize("env", ["testing", "live"])
    def test_check(self, mocker: MockerFixture, fx_bas_catalogue: BasCatalogue, env: SiteEnvironment):
        """
        Can check environment's static site.

        Checks are not actually run, this test only verifies environment logic.
        """
        mocker.patch.object(fx_bas_catalogue._envs[env], "check", return_value=None)
        fx_bas_catalogue.check(env=env)
