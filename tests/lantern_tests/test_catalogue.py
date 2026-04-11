import logging
from collections.abc import Callable
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory
from typing import Final

import pytest
from mypy_boto3_s3 import S3Client
from pytest_mock import MockerFixture

from lantern.catalogue import BasCatalogue, BasCatEnv, BasCatTrusted, BasCatUntrusted, CatalogueBase
from lantern.config import Config
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
from tests.resources.catalogues.fake_catalogue import FakeCatalogue
from tests.resources.stores.fake_records_store import FakeRecordsStore


class TestCatalogueBase:
    """Test catalogue abstract base class via fake catalogue implementation."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config, fx_fake_store: FakeRecordsStore):
        """Can create a catalogue instance."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "output"
        cat = FakeCatalogue(logger=fx_logger, config=fx_config, store=fx_fake_store, base_path=tmp_path)
        assert isinstance(cat, CatalogueBase)

    def test_export(self, fx_fake_catalogue: FakeCatalogue):
        """
        Can export static site.

        Note: Performs an actual export so takes a few seconds.
        """
        export_path: Path = fx_fake_catalogue._path
        fx_fake_catalogue.export()
        assert export_path.joinpath("favicon.ico").exists()

    def test_verify(self, fx_fake_catalogue: FakeCatalogue, fx_exporter_static_server: Popen):
        """
        Can verify catalogue contents.

        Performs a real export and verification of a test record using a local server (as per e2e tests). This server
        contains all test records which takes a few seconds to build.

        Note: Uses the minimal product test record ('3c77ffae-6aa0-4c26-bc34-5521dbf4bf23') rather the verification
        record (`cf80b941-3de6-4a04-8f5a-a2349c1e3ae0`) because it has external distribution options with fake values
        that trip up the request method.
        """
        identifiers = {"3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"}  # minimal product test record
        fx_fake_catalogue._verify_context["BASE_URL"] = "http://localhost:8123"
        fx_fake_catalogue.export(identifiers)
        export_path: Path = fx_fake_catalogue._path

        fx_fake_catalogue.verify(identifiers)
        assert export_path.joinpath("-/verification/data.json").exists()

    def test_purge(self, fx_fake_catalogue: FakeCatalogue):
        """Can purge export target."""
        identifiers = {"3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"}  # minimal product test record
        export_path: Path = fx_fake_catalogue._path
        fx_fake_catalogue.export(identifiers)
        assert export_path.joinpath("favicon.ico").exists()

        fx_fake_catalogue.purge()
        assert not export_path.joinpath("favicon.ico").exists()


class TestBasCatUntrusted:
    """Test BAS data catalogue untrusted site."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_fake_store: FakeRecordsStore,
        fx_s3_client: S3Client,
        fx_s3_bucket_name: str,
    ):
        """
        Can create a BAS untrusted catalogue instance.

        Uses fake store over GitLab to avoid mocking and/or request recordings.
        """
        cat = BasCatUntrusted(
            logger=fx_logger,
            meta=fx_export_meta,
            store=fx_fake_store,
            s3=fx_s3_client,
            bucket=fx_s3_bucket_name,
            verify_sharepoint_endpoint="x",
            verify_san_endpoint="x",
        )
        assert isinstance(cat, BasCatUntrusted)

    all_global: Final[list[Callable[..., OutputBase]]] = [
        SiteResourcesOutput,
        SiteIndexOutput,
        SitePagesOutput,
        SiteApiOutput,
        SiteHealthOutput,
        RecordsWafOutput,
        ItemsBasWebsiteOutput,
    ]
    all_individual: Final[list[Callable[..., OutputBase]]] = [
        ItemCatalogueOutput,
        ItemAliasesOutput,
        RecordIsoJsonOutput,
        RecordIsoXmlOutput,
        RecordIsoHtmlOutput,
    ]

    @pytest.mark.cov()
    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            (None, (all_global, all_individual)),
            ([SiteResourcesOutput, ItemCatalogueOutput], ([SiteResourcesOutput], [ItemCatalogueOutput])),
        ],
    )
    def test__sort_output_classes(
        self,
        fx_bas_cat_untrusted: BasCatUntrusted,
        values: list[Callable[..., OutputBase]] | None,
        expected: tuple[list[Callable[..., OutputBase]], list[Callable[..., OutputBase]]],
    ):
        """Can sort selected output classes into individual and global types, or return all classes."""
        results = fx_bas_cat_untrusted._group_output_classes(values)
        assert results == expected

    def test_export(self, fx_bas_cat_untrusted: BasCatUntrusted):
        """Can export untrusted site."""
        identifier = "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"  # minimal product test record
        fx_bas_cat_untrusted.export(identifiers={identifier})

        assert (
            fx_bas_cat_untrusted._exporter._s3.get_object(
                Bucket=fx_bas_cat_untrusted._exporter._bucket, Key="favicon.ico"
            )["ResponseMetadata"]["HTTPStatusCode"]
            == 200
        )

        result = fx_bas_cat_untrusted._exporter._s3.get_object(
            Bucket=fx_bas_cat_untrusted._exporter._bucket, Key=f"items/{identifier}/index.html"
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        item_text = result["Body"].read().decode("utf-8")
        assert "tab-content-admin" not in item_text

    def test_verify(self, fx_bas_cat_untrusted: BasCatUntrusted):
        """Can verify untrusted site."""
        identifiers = {"3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"}  # minimal product test record
        fx_bas_cat_untrusted.verify(identifiers)
        result = fx_bas_cat_untrusted._exporter._s3.get_object(
            Bucket=fx_bas_cat_untrusted._exporter._bucket, Key="-/verification/data.json"
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestBasCatTrusted:
    """Test BAS data catalogue trusted site."""

    def test_init(self, fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_fake_store: FakeRecordsStore):
        """
        Can create a BAS trusted catalogue instance.

        Uses fake store over GitLab to avoid mocking and/or request recordings.
        """
        cat = BasCatTrusted(logger=fx_logger, meta=fx_export_meta, store=fx_fake_store, host="x", path=Path("x"))
        assert isinstance(cat, BasCatTrusted)

    def test_export(self, fx_bas_cat_trusted: BasCatTrusted):
        """Can export trusted site."""
        identifier = "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"  # minimal product test record
        fx_bas_cat_trusted.export(identifiers={identifier})
        trusted_path = fx_bas_cat_trusted._exporter._path

        item_path = trusted_path.joinpath(f"items/{identifier}/index.html")
        assert item_path.exists()
        with item_path.open() as f:
            item_text = f.read()
        assert "tab-content-admin" in item_text

    def test_verify(self, fx_bas_cat_trusted: BasCatTrusted):
        """Cannot verify trusted site (not supported)."""
        with pytest.raises(NotImplementedError):
            fx_bas_cat_trusted.verify()


class TestBasCatEnv:
    """Test BAS data catalogue environment subclass."""

    def test_init(
        self, fx_logger: logging.Logger, fx_config: Config, fx_fake_store: FakeRecordsStore, fx_s3_client: S3Client
    ):
        """
        Can create a BAS catalogue environment instance.

        Uses fake store over GitLab to avoid mocking and/or request recordings.
        """
        cat = BasCatEnv(logger=fx_logger, config=fx_config, store=fx_fake_store, s3=fx_s3_client, env="testing")
        assert isinstance(cat, BasCatEnv)
        assert isinstance(cat._untrusted, BasCatUntrusted)
        assert isinstance(cat._trusted, BasCatTrusted)

    def test_export(self, fx_bas_cat_env: BasCatEnv):
        """Can export static sites."""
        identifier = "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"  # minimal product test record
        fx_bas_cat_env.export(identifiers={identifier})

        result = fx_bas_cat_env._untrusted._exporter._s3.get_object(
            Bucket=fx_bas_cat_env._untrusted._exporter._bucket, Key=f"items/{identifier}/index.html"
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        trusted_path = fx_bas_cat_env._trusted._exporter._path
        assert trusted_path.joinpath(f"items/{identifier}/index.html").exists()

    def test_verify(self, mocker: MockerFixture, fx_bas_cat_env: BasCatEnv):
        """
        Can verify catalogue contents.

        Verification is not actually run, this test only verifies the coordination logic.
        """
        mocker.patch.object(fx_bas_cat_env._untrusted, "verify", return_value=None)
        fx_bas_cat_env.verify()


class TestBasCatalogue:
    """Test BAS data catalogue subclass."""

    def test_init(
        self, fx_logger: logging.Logger, fx_config: Config, fx_fake_store: FakeRecordsStore, fx_s3_client: S3Client
    ):
        """
        Can create a BAS catalogue instance.

        Uses fake store over GitLab to avoid mocking and/or request recordings.
        """
        cat = BasCatalogue(logger=fx_logger, config=fx_config, store=fx_fake_store, s3=fx_s3_client)
        assert isinstance(cat, BasCatalogue)
        assert isinstance(cat._envs["testing"], BasCatEnv)
        assert isinstance(cat._envs["live"], BasCatEnv)

    @pytest.mark.parametrize("env", ["testing", "live"])
    def test_export(self, mocker: MockerFixture, fx_bas_catalogue: BasCatalogue, env: SiteEnvironment):
        """Can export environment's static site."""
        mocker.patch.object(fx_bas_catalogue._envs[env], "export", return_value=None)
        fx_bas_catalogue.export(env=env)

    @pytest.mark.parametrize("env", ["testing", "live"])
    def test_verify(self, mocker: MockerFixture, fx_bas_catalogue: BasCatalogue, env: SiteEnvironment):
        """Can verify environment's static site."""
        mocker.patch.object(fx_bas_catalogue._envs[env], "verify", return_value=None)
        fx_bas_catalogue.verify(env=env)
