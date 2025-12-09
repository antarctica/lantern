import logging
import os
import shutil
import socket
import sys
import time
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from http.client import HTTPConnection
from importlib.metadata import version
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from boto3 import client as S3Client  # noqa: N812
from gitlab import Gitlab
from moto import mock_aws
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.exporters.base import Exporter, ResourceExporter, S3Utils, get_jinja_env, prettify_html
from lantern.exporters.html import HtmlAliasesExporter, HtmlExporter
from lantern.exporters.records import RecordsExporter
from lantern.exporters.site import SiteExporter, SiteIndexExporter, SitePagesExporter, SiteResourcesExporter
from lantern.exporters.verification import VerificationExporter
from lantern.exporters.waf import WebAccessibleFolderExporter
from lantern.exporters.website import WebsiteSearchExporter
from lantern.exporters.xml import IsoXmlHtmlExporter
from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.elements.common import Date, Dates, Identifier, Identifiers
from lantern.lib.metadata_library.models.record.elements.identification import Constraint
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record as RecordBase
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, AdministrationWrapper, set_admin
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.base.item import ItemBase
from lantern.models.item.catalogue.elements import Dates as ItemCatDates
from lantern.models.item.catalogue.elements import Identifiers as ItemCatIdentifiers
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.item.catalogue.tabs import AdditionalInfoTab, AdminTab
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteMeta
from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext
from lantern.stores.gitlab import GitLabLocalCache, GitLabStore
from tests.resources.exporters.fake_exporter import FakeExporter, FakeResourceExporter
from tests.resources.records.admin_keys.testing_keys import load_keys
from tests.resources.stores.fake_records_store import FakeRecordsStore


def has_network() -> bool:
    """
    Determine if network access is available.

    Intended for use with `pytest.mark.skipif()` statements for tests that require online resources.

    E.g.:
    ```
    from tests.conftest import has_network

    @pytest.mark.skipif(not has_network(), reason="network unavailable")
    def test_foo():
        ...
    ```
    """
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=1)
    except OSError:
        return False
    else:
        return True


@pytest.fixture(scope="module")
def vcr_config():
    """Pytest Recording config."""
    return {"filter_headers": ["Authorization", "PRIVATE-TOKEN"]}


def freezer_time() -> datetime:
    """Freezer time for tests."""
    return datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)


@pytest.fixture()
def fx_freezer_time() -> datetime:
    """Freezer time for tests."""
    return freezer_time()


@pytest.fixture()
def fx_package_version() -> str:
    """Package version."""
    return version("lantern")


@pytest.fixture()
def fx_logger() -> logging.Logger:
    """App logger."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture()
def fx_config() -> Config:
    """App configuration."""
    return Config()


@pytest.fixture()
def fx_site_meta(fx_config: Config) -> SiteMeta:
    """Site build metadata."""
    return SiteMeta.from_config_store(config=fx_config, store=None, build_repo_ref="83fake48")


@pytest.fixture()
def fx_export_meta(fx_config: Config) -> ExportMeta:
    """Exporter build metadata (superset of site metadata)."""
    return ExportMeta.from_config_store(config=fx_config, store=None, build_repo_ref="83fake48")


@lru_cache(maxsize=1)
def _admin_meta_keys() -> AdministrationKeys:
    """
    Administration keys for signing and encrypting administrative metadata.

    Standalone method to allow use outside of fixtures in test parametrisation.

    Cached for better performance.
    """
    return load_keys()


@pytest.fixture()
def fx_admin_meta_keys() -> AdministrationKeys:
    """Administration keys for signing and encrypting administrative metadata."""
    return _admin_meta_keys()


@pytest.fixture()
def fx_admin_meta_element() -> Administration:
    """Administrative metadata element."""
    return Administration(id="x")


@pytest.fixture()
def fx_admin_wrapper(fx_admin_meta_keys: AdministrationKeys):
    """Administrative metadata wrapper."""
    return AdministrationWrapper(fx_admin_meta_keys)


"""
Record (Configs) and Item fixtures

| Package         | Type                     | Fixture                         | Inherits                        |
| --------------- | ------------------------ | ------------------------------- | ------------------------------- |
| MetadataLibrary | dict                     | fx_lib_record_config_min_iso    | -                               |
|                 | dict                     | fx_lib_record_config_min_magic  | fx_lib_record_config_min_iso    |
|                 | Record (RecordBase)      | fx_lib_record_model_min_iso     | fx_lib_record_config_min_iso    |
| Lantern         | dict                     | fx_record_config_min            | fx_lib_record_config_min_iso    |
|                 | dict                     | fx_revision_config_min          | fx_record_config_min            |
|                 | dict                     | fx_item_config_min_base         | fx_revision_config_min          |
|                 | dict                     | fx_item_config_min_catalogue    | fx_item_config_min_base         |
|                 | dict                     | fx_item_config_min_physical_map | fx_item_config_min_catalogue    |
|                 | Record                   | fx_record_model_min             | fx_record_config_min            |
|                 | RecordRevision           | fx_revision_model_min           | fx_revision_config_min          |
|                 | ItemBase                 | fx_item_base_model_min          | fx_item_config_min_base         |
|                 | ItemCatalogue            | fx_item_cat_model_min           | fx_item_config_min_catalogue    |
|                 | ItemCatalogue            | fx_item_cat_model_min_open      | _item_cat_model_min             |
|                 | ItemCataloguePhysicalMap | fx_item_physical_map_model_min  | fx_item_config_min_physical_map |
"""


def _lib_record_config_min_iso() -> dict:
    """
    Minimal (base) record configuration (ISO).

    Minimal record that will validate against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return {
        "hierarchy_level": "dataset",
        "metadata": {
            "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
            "date_stamp": "2014-06-30",
        },
        "identification": {
            "title": {"value": "x"},
            "dates": {"creation": "2014-06-30"},
            "abstract": "x",
            "language": "eng",
        },
    }


@pytest.fixture()
def fx_lib_record_config_min_iso() -> dict:
    """
    Minimal (base) record configuration (ISO).

    Fixture wrapper for `_lib_record_config_min_iso()`.
    """
    return _lib_record_config_min_iso()


@pytest.fixture()
def fx_lib_record_config_min_magic(fx_lib_record_config_min_iso: dict) -> dict:
    """
    Minimal (base) record configuration (MAGIC preset).

    Minimal record that can create a valid RecordMagicDiscoveryV1 instance. Does not include properties the preset will
    configure automatically (such as identifiers, contacts, domain consistencies).

    Types must be safe to encode as JSON.
    """
    return {"file_identifier": "x", **fx_lib_record_config_min_iso}


@pytest.fixture()
def fx_lib_record_model_min_iso(fx_lib_record_config_min_iso: dict) -> RecordBase:
    """Minimal (base) Record model instance."""
    return RecordBase.loads(fx_lib_record_config_min_iso)


def _record_config_min() -> dict:
    """
    Minimal record configuration (catalogue).

    Minimal configuration that will validate against the Data Catalogue Record model.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    config: dict = {"file_identifier": "x", **deepcopy(_lib_record_config_min_iso())}
    config["identification"]["identifiers"] = [
        {
            "identifier": config["file_identifier"],
            "href": f"https://{CATALOGUE_NAMESPACE}/items/{config['file_identifier']}",
            "namespace": CATALOGUE_NAMESPACE,
        }
    ]
    config["identification"]["contacts"] = [{**deepcopy(config["metadata"]["contacts"][0]), "email": "x"}]

    return config


@pytest.fixture()
def fx_record_config_min() -> dict:
    """
    Minimal record configuration (catalogue).

    Wrapper for `_record_config_min()`.
    """
    return _record_config_min()


def _revision_config_min() -> dict:
    """
    Minimal record configuration (catalogue revision).

    Minimal configuration for a Data Catalogue Record Revision model.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return {"file_revision": "x", **deepcopy(_record_config_min())}


@pytest.fixture()
def fx_revision_config_min(fx_record_config_min: dict) -> dict:
    """
    Minimal record configuration (catalogue revision).

    Wrapper for `_revision_config_min()`.
    """
    return _revision_config_min()


def _item_config_min_base() -> dict:
    """
    Minimal record configuration (catalogue).

    Minimal configuration for an ItemBase model.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return deepcopy(_revision_config_min())


@pytest.fixture()
def fx_item_config_min_base(fx_revision_config_min: dict) -> dict:
    """
    Minimal record configuration (catalogue).

    Wrapper for `_item_config_min_base()`.
    """
    return _item_config_min_base()


def _item_config_min_catalogue() -> dict:
    """
    Minimal record configuration (catalogue).

    Minimal configuration for an ItemCatalogue model.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    config = deepcopy(_item_config_min_base())
    config["identification"]["contacts"] = deepcopy(config["metadata"]["contacts"])
    config["identification"]["contacts"][0]["email"] = "x"

    return config


@pytest.fixture()
def fx_item_config_min_catalogue() -> dict:
    """
    Minimal record configuration (catalogue).

    Wrapper for `_item_config_min_catalogue()`.
    """
    return _item_config_min_catalogue()


@pytest.fixture()
def fx_item_config_min_physical_map(fx_item_config_min_catalogue: dict) -> dict:
    """
    Minimal record configuration (catalogue physical maps).

    Minimal configuration for a Data Catalogue Record Revision model.

    Types must be safe to encode as JSON.
    """
    config = deepcopy(fx_item_config_min_catalogue)
    config["hierarchy_level"] = HierarchyLevelCode.PAPER_MAP_PRODUCT.value
    config["identification"]["aggregations"] = [
        {
            "identifier": {
                "identifier": "x",
                "href": f"https://{CATALOGUE_NAMESPACE}/items/x",
                "namespace": CATALOGUE_NAMESPACE,
            },
            "association_type": "isComposedOf",
            "initiative_type": "paperMap",
        }
    ]
    return config


@pytest.fixture()
def fx_record_model_min(fx_record_config_min: dict) -> Record:
    """Minimal record model instance."""
    return Record.loads(fx_record_config_min)


@pytest.fixture()
def fx_revision_model_min(fx_revision_config_min: dict) -> RecordRevision:
    """Minimal record revision model instance."""
    return RecordRevision.loads(fx_revision_config_min)


@pytest.fixture()
def fx_item_base_model_min(fx_item_config_min_base: dict, fx_admin_meta_keys: AdministrationKeys) -> ItemBase:
    """Minimal ItemBase model instance."""
    return ItemBase(record=RecordRevision.loads(fx_item_config_min_base), admin_keys=fx_admin_meta_keys)


def render_item_catalogue(item: ItemCatalogue) -> str:
    """Render item to HTML."""
    _jinja = get_jinja_env()
    _template_path = "_views/item.html.j2"
    raw = _jinja.get_template(_template_path).render(item=item, meta=item.site_metadata)
    return prettify_html(raw)


def _item_cat_model_min() -> ItemCatalogue:
    """
    Minimal ItemCatalogue model instance.

    Includes minimal admin metadata required by admin tab.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    meta = SiteMeta.from_config_store(config=Config(), store=None, build_repo_ref="83fake48")
    model = ItemCatalogue(
        site_meta=meta,
        record=RecordRevision.loads(_item_config_min_catalogue()),
        admin_meta_keys=_admin_meta_keys(),
        trusted_context=True,
        get_record=_get_record,
    )
    # noinspection PyProtectedMember
    set_admin(keys=model._admin_keys, record=model._record, admin_meta=Administration(id=model.resource_id))
    return model


@pytest.fixture()
def fx_item_cat_model_min(
    fx_site_meta: SiteMeta,
    fx_item_config_min_catalogue: dict,
    fx_admin_meta_keys: AdministrationKeys,
    fx_get_record: Callable[[str], RecordRevision],
) -> ItemCatalogue:
    """
    Minimal ItemCatalogue model instance.

    Includes minimal admin metadata required by admin tab.
    """
    model = ItemCatalogue(
        site_meta=fx_site_meta,
        record=RecordRevision.loads(fx_item_config_min_catalogue),
        admin_meta_keys=fx_admin_meta_keys,
        trusted_context=True,
        get_record=fx_get_record,
    )
    # noinspection PyProtectedMember
    set_admin(keys=model._admin_keys, record=model._record, admin_meta=Administration(id=model.resource_id))
    return model


# noinspection PyProtectedMember
@pytest.fixture()
def fx_item_cat_model_open(
    fx_item_cat_model_min: ItemCatalogue,
    fx_item_config_min_catalogue: dict,
) -> ItemCatalogue:
    """Minimal cloned ItemCatalogue model instance with minimal admin metadata to allow open access."""
    model = _item_cat_model_min()
    # noinspection PyProtectedMember
    set_admin(
        keys=model._admin_keys,
        record=model._record,
        admin_meta=Administration(id=model.resource_id, access_permissions=[OPEN_ACCESS]),
    )
    return model


@pytest.fixture()
def fx_item_physical_map_model_min(
    fx_site_meta: SiteMeta,
    fx_item_config_min_physical_map: dict,
    fx_admin_meta_keys: AdministrationKeys,
    fx_get_record: Callable[[str], RecordRevision],
) -> ItemCataloguePhysicalMap:
    """
    Minimal ItemCataloguePhysicalMap model instance.

    Includes minimal admin metadata required by admin tab.
    """
    model = ItemCataloguePhysicalMap(
        site_meta=fx_site_meta,
        record=RecordRevision.loads(fx_item_config_min_physical_map),
        admin_meta_keys=fx_admin_meta_keys,
        trusted_context=True,
        get_record=fx_get_record,
    )
    # noinspection PyProtectedMember
    set_admin(keys=model._admin_keys, record=model._record, admin_meta=Administration(id=model.resource_id))
    return model


def _get_record(identifier: str) -> RecordRevision:
    """
    Minimal record lookup method.

    Standalone method to allow use outside of fixtures.
    """
    record = RecordRevision.loads(deepcopy(_revision_config_min()))
    record.file_identifier = identifier
    return record


@pytest.fixture()
def fx_get_record() -> Callable[[str], RecordRevision]:
    """
    Minimal record lookup method.

    Wrapper for `_get_record()`.
    """
    return _get_record


@pytest.fixture()
def fx_item_cat_info_tab_minimal(fx_site_meta: SiteMeta) -> AdditionalInfoTab:
    """Minimal ItemCatalogue additional information tab."""
    dates = ItemCatDates(dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
    identifiers = ItemCatIdentifiers(Identifiers([]))
    return AdditionalInfoTab(
        item_id="x",
        item_type=HierarchyLevelCode.PRODUCT,
        identifiers=identifiers,
        gitlab_issues=[],
        dates=dates,
        datestamp=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC).date(),
        kv={},
        build_time=fx_site_meta.build_time,
    )


@pytest.fixture()
def fx_item_cat_admin_tab_min() -> AdminTab:
    """Minimal ItemCatalogue admin tab."""
    return AdminTab(
        trusted=True,
        item_id="x",
        revision=Link(value="x", href="x", external=True),
        gitlab_issues=[],
        restricted=False,
        access_level=AccessLevel.NONE,
        access_permissions=[],
    )


@pytest.fixture()
def fx_fake_store(fx_logger: logging.Logger) -> FakeRecordsStore:
    """Fake records store."""
    return FakeRecordsStore(logger=fx_logger)


@pytest.fixture()
def fx_gitlab_cache(fx_logger: logging.Logger, fx_config: Config) -> GitLabLocalCache:
    """GitLab local cache."""
    with TemporaryDirectory() as tmp_path:
        cache_path = Path(tmp_path) / ".cache"

    return GitLabLocalCache(
        logger=fx_logger,
        parallel_jobs=fx_config.PARALLEL_JOBS,
        path=cache_path,
        project_id=fx_config.STORE_GITLAB_PROJECT_ID,
        ref=fx_config.STORE_GITLAB_BRANCH,
        gitlab_client=Gitlab(url=fx_config.STORE_GITLAB_ENDPOINT, private_token=fx_config.STORE_GITLAB_TOKEN),
    )


def _gitlab_cache_create(cache: fx_gitlab_cache) -> None:
    """
    Copy static GitLab local cache to simulate cloning from remote repository.

    Intended to be used as a side effect when mocking the `GitLabStore._create` method.
    """
    cache_src = Path(__file__).resolve().parent / "resources" / "stores" / "gitlab_cache"
    # noinspection PyProtectedMember
    shutil.copytree(cache_src, cache._path, dirs_exist_ok=True)


@pytest.fixture()
def fx_gitlab_cache_pop(mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache) -> GitLabLocalCache:
    """
    GitLab local cache populated with records.

    To simulate and bypass fetching records from remote repository.
    """
    mocker.patch.object(fx_gitlab_cache, "_create", side_effect=lambda: _gitlab_cache_create(fx_gitlab_cache))
    # noinspection PyProtectedMember
    fx_gitlab_cache._create()
    return fx_gitlab_cache


@pytest.fixture()
def fx_gitlab_store(fx_logger: logging.Logger, fx_config: Config) -> GitLabStore:
    """GitLab store."""
    with TemporaryDirectory() as tmp_path:
        cache_path = Path(tmp_path) / ".cache"

    return GitLabStore(
        logger=fx_logger,
        parallel_jobs=fx_config.PARALLEL_JOBS,
        endpoint=fx_config.STORE_GITLAB_ENDPOINT,
        access_token=fx_config.STORE_GITLAB_TOKEN,
        project_id=fx_config.STORE_GITLAB_PROJECT_ID,
        branch=fx_config.STORE_GITLAB_BRANCH,
        cache_path=cache_path,
    )


@pytest.fixture()
def fx_gitlab_store_cached(fx_gitlab_store: GitLabStore, fx_gitlab_cache_pop: GitLabLocalCache) -> GitLabStore:
    """GitLab store with populated/existing cache."""
    # noinspection PyProtectedMember
    fx_gitlab_store._cache = fx_gitlab_cache_pop
    return fx_gitlab_store


@pytest.fixture()
def fx_gitlab_store_pop(fx_gitlab_store_cached: GitLabStore) -> GitLabStore:
    """GitLab store populated with records from a populated/existing local cache."""
    fx_gitlab_store_cached.populate()
    return fx_gitlab_store_cached


@pytest.fixture()
def fx_s3_bucket_name() -> str:
    """S3 bucket name."""
    return "testing"


@pytest.fixture()
def fx_s3_client(mocker: MockerFixture, fx_s3_bucket_name: str) -> S3Client:
    """Mocked S3 client with testing bucket pre-created."""
    mock_config = mocker.Mock()
    type(mock_config).AWS_ACCESS_ID = PropertyMock(return_value="x")
    type(mock_config).AWS_ACCESS_SECRET = PropertyMock(return_value="x")

    with mock_aws():
        client = S3Client(
            "s3",
            aws_access_key_id=mock_config.AWS_ACCESS_ID,
            aws_secret_access_key=mock_config.AWS_ACCESS_SECRET,
            region_name="eu-west-1",
        )

        client.create_bucket(
            Bucket=fx_s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )

        yield client


@pytest.fixture()
def fx_s3_utils(fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str) -> S3Utils:
    """S3Utils with a mocked S3 client."""
    with TemporaryDirectory() as tmp_path:
        base_path = Path(tmp_path)
    return S3Utils(logger=fx_logger, s3=fx_s3_client, s3_bucket=fx_s3_bucket_name, relative_base=base_path)


@pytest.fixture()
def fx_exporter_base(
    mocker: MockerFixture, fx_logger: logging.Logger, fx_s3_bucket_name: str, fx_s3_client: S3Client
) -> Exporter:
    """
    Base Data Catalogue exporter.

    With a mocked config and S3 client

    Actual exporter has abstract method so a subclass is used.
    """
    mock_config = mocker.Mock()
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return FakeExporter(logger=fx_logger, meta=meta, s3=fx_s3_client)


@pytest.fixture()
def fx_exporter_resource_base(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_exporter_base: Exporter,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_revision_model_min: RecordRevision,
) -> ResourceExporter:
    """
    Base resource exporter.

    With a mocked config and S3 client

    Actual exporter has abstract method so a subclass is used.
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    fx_exporter_base._config = mock_config
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return FakeResourceExporter(
        logger=fx_logger,
        meta=meta,
        s3=fx_s3_client,
        record=fx_revision_model_min,
        export_base=output_path.joinpath("x"),
        export_name="x.txt",
    )


@pytest.fixture()
def fx_exporter_iso_xml_html(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_revision_model_min: RecordRevision,
) -> Exporter:
    """ISO 19115 XML as HTML exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return IsoXmlHtmlExporter(logger=fx_logger, meta=meta, s3=fx_s3_client, record=fx_revision_model_min)


@pytest.fixture()
def fx_exporter_html(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_revision_model_min: RecordRevision,
) -> HtmlExporter:
    """HTML exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return HtmlExporter(
        logger=fx_logger, meta=meta, s3=fx_s3_client, record=fx_revision_model_min, get_record=_get_record
    )


@pytest.fixture()
def fx_exporter_html_alias(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_revision_model_min: RecordRevision,
) -> HtmlAliasesExporter:
    """HTML alias exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    fx_revision_model_min.identification.identifiers.append(
        Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)
    )

    return HtmlAliasesExporter(logger=fx_logger, meta=meta, s3=fx_s3_client, record=fx_revision_model_min)


@pytest.fixture()
def fx_exporter_records(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_admin_meta_keys: AdministrationKeys,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_get_record: Callable[[str], RecordRevision],
) -> RecordsExporter:
    """
    Site records exporter (empty).

    With:
    - a mocked config and S3 client
    - a minimal sample record
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).PARALLEL_JOBS = PropertyMock(return_value=1)
    type(mock_config).ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE = PropertyMock(
        return_value=fx_admin_meta_keys.encryption_private
    )
    type(mock_config).ADMIN_METADATA_SIGNING_KEY_PUBLIC = PropertyMock(return_value=fx_admin_meta_keys.signing_public)
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return RecordsExporter(logger=fx_logger, config=mock_config, meta=meta, s3=fx_s3_client, get_record=fx_get_record)


@pytest.fixture()
def fx_exporter_records_sel(
    fx_exporter_records: RecordsExporter, fx_revision_model_min: RecordRevision
) -> RecordsExporter:
    """Site records exporter with a single record selected."""
    fx_exporter_records.selected_identifiers = {fx_revision_model_min.file_identifier}
    return fx_exporter_records


@pytest.fixture()
def fx_exporter_site_resources(
    mocker: MockerFixture, fx_logger: logging.Logger, fx_s3_bucket_name: str, fx_s3_client: S3Client
) -> SiteResourcesExporter:
    """Site resources exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return SiteResourcesExporter(logger=fx_logger, meta=meta, s3=fx_s3_client)


def _get_record_alias(identifier: str) -> RecordRevision:
    """Minimal record lookup method with an alias identifier."""
    record = RecordRevision.loads(deepcopy(_revision_config_min()))
    record.file_identifier = identifier
    record.identification.identifiers.append(
        Identifier(identifier="x", href="https://data.bas.ac.uk/datasets/x", namespace=ALIAS_NAMESPACE)
    )
    return record


@pytest.fixture()
def fx_exporter_site_index(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_logger: logging.Logger, fx_s3_client: S3Client
) -> SiteIndexExporter:
    """
    Site index exporter (empty).

    With a mocked config and S3 client.
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return SiteIndexExporter(logger=fx_logger, meta=meta, s3=fx_s3_client, get_record=_get_record_alias)


@pytest.fixture()
def fx_exporter_site_index_sel(
    fx_exporter_site_index: SiteIndexExporter, fx_revision_model_min: RecordRevision
) -> SiteIndexExporter:
    """Site index exporter with a single record selected."""
    fx_exporter_site_index.selected_identifiers = {fx_revision_model_min.file_identifier}
    return fx_exporter_site_index


@pytest.fixture()
def fx_exporter_waf(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_logger: logging.Logger, fx_s3_client: S3Client
) -> WebAccessibleFolderExporter:
    """
    Web Accessible Folder exporter (empty).

    With a mocked config and S3 client.
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return WebAccessibleFolderExporter(logger=fx_logger, meta=meta, s3=fx_s3_client, get_record=_get_record_alias)


@pytest.fixture()
def fx_exporter_waf_sel(
    fx_exporter_waf: WebAccessibleFolderExporter, fx_revision_model_min: RecordRevision
) -> WebAccessibleFolderExporter:
    """Web Accessible Folder exporter with a single record selected."""
    fx_exporter_waf.selected_identifiers = {fx_revision_model_min.file_identifier}
    return fx_exporter_waf


def _get_record_open(identifier: str) -> RecordRevision:
    """Minimal record lookup method with open access constraint and admin access permissions."""
    record = RecordRevision.loads(deepcopy(_revision_config_min()))
    record.file_identifier = identifier

    # access permissions
    admin_meta = Administration(id=record.file_identifier, access_permissions=[OPEN_ACCESS])
    set_admin(keys=_admin_meta_keys(), record=record, admin_meta=admin_meta)

    # access constraints (informative)
    record.identification.constraints.append(
        Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
    )
    return record


@pytest.fixture()
def fx_exporter_website_search(
    mocker: MockerFixture,
    fx_admin_meta_keys: AdministrationKeys,
    fx_s3_bucket_name: str,
    fx_logger: logging.Logger,
    fx_s3_client: S3Client,
) -> WebsiteSearchExporter:
    """
    Public website search exporter (empty).

    With a mocked config and S3 client.
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).NAME = PropertyMock(return_value="lantern")
    type(mock_config).ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE = PropertyMock(
        return_value=fx_admin_meta_keys.encryption_private
    )
    type(mock_config).ADMIN_METADATA_SIGNING_KEY_PUBLIC = PropertyMock(return_value=fx_admin_meta_keys.signing_public)
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")
    # Inject private signing key so admin metadata can be signed in other fixtures and tests
    meta.admin_meta_keys = fx_admin_meta_keys

    return WebsiteSearchExporter(logger=fx_logger, meta=meta, s3=fx_s3_client, get_record=_get_record_open)


@pytest.fixture()
def fx_exporter_website_search_sel(
    fx_exporter_website_search: WebsiteSearchExporter,
    fx_revision_model_min: RecordRevision,
    fx_admin_meta_keys: AdministrationKeys,
) -> WebsiteSearchExporter:
    """Public website search exporter with a single record selected."""
    fx_exporter_website_search.selected_identifiers = {fx_revision_model_min.file_identifier}
    return fx_exporter_website_search


@pytest.fixture()
def fx_exporter_site_pages(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_logger: logging.Logger, fx_s3_client: S3Client
) -> SitePagesExporter:
    """Site pages exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return SitePagesExporter(logger=fx_logger, meta=meta, s3=fx_s3_client)


@pytest.fixture()
def fx_exporter_site(
    mocker: MockerFixture,
    fx_s3_bucket_name: str,
    fx_logger: logging.Logger,
    fx_admin_meta_keys: AdministrationKeys,
    fx_s3_client: S3Client,
    fx_get_record: Callable[[str], RecordRevision],
) -> SiteExporter:
    """
    Site exporter (empty records).

    With: a mocked config and S3 client
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).PARALLEL_JOBS = PropertyMock(return_value=1)
    type(mock_config).ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE = PropertyMock(
        return_value=fx_admin_meta_keys.encryption_private
    )
    type(mock_config).ADMIN_METADATA_SIGNING_KEY_PUBLIC = PropertyMock(return_value=fx_admin_meta_keys.signing_public)
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")
    mocker.patch("lantern.exporters.records._job_s3", return_value=fx_s3_client)
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    return SiteExporter(logger=fx_logger, config=mock_config, meta=meta, s3=fx_s3_client, get_record=fx_get_record)


@pytest.fixture()
def fx_exporter_verify(
    mocker: MockerFixture,
    fx_s3_bucket_name: str,
    fx_logger: logging.Logger,
    fx_s3_client: S3Client,
    fx_get_record: Callable[[str], RecordRevision],
) -> VerificationExporter:
    """
    Verification exporter (empty records).

    With:
    - a mocked config and S3 client
    - global verification context
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).PARALLEL_JOBS = PropertyMock(return_value=1)
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).BASE_URL = PropertyMock(return_value="https://example.com")
    meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

    context: VerificationContext = {
        "BASE_URL": meta.base_url,
        "SHAREPOINT_PROXY_ENDPOINT": "x",
        "SAN_PROXY_ENDPOINT": "x",
    }

    return VerificationExporter(logger=fx_logger, meta=meta, s3=fx_s3_client, get_record=fx_get_record, context=context)


@pytest.fixture()
def fx_exporter_verify_sel(
    fx_exporter_verify: VerificationExporter, fx_revision_model_min: RecordRevision
) -> VerificationExporter:
    """Verification exporter with a single record selected."""
    fx_exporter_verify.selected_identifiers = {fx_revision_model_min.file_identifier}
    return fx_exporter_verify


@pytest.fixture()
def fx_exporter_verify_post_run(fx_exporter_verify_sel: VerificationExporter) -> VerificationExporter:
    """Verification exporter with a single record selected and applicable jobs in a PASS state."""
    fx_exporter_verify_sel._jobs = [
        VerificationJob(
            result=VerificationResult.PASS,
            type=VerificationType.SITE_PAGES,
            url="https://data.bas.ac.uk/-/index",
            context=fx_exporter_verify_sel._context,
            data={"duration": timedelta(microseconds=1)},
        ),
        VerificationJob(
            result=VerificationResult.PASS,
            type=VerificationType.ITEM_PAGES,
            url="https://data.bas.ac.uk/items/123",
            context=fx_exporter_verify_sel._context,
            data={"file_identifier": "x", "duration": timedelta(microseconds=1)},
        ),
    ]
    return fx_exporter_verify_sel


@pytest.fixture(scope="module")
def fx_exporter_static_site(module_mocker: MockerFixture) -> TemporaryDirectory:
    """
    Build static site and export to a temp directory.

    Module scoped for performance. Means usual fixtures for config, S3Client, get_record and FakeRecordsStore can't be
    used and are duplicated.
    """
    site_dir = TemporaryDirectory()

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    config = Config()
    module_mocker.patch.object(
        type(config),
        attribute="EXPORT_PATH",
        new_callable=PropertyMock,
        return_value=Path(site_dir.name),
    )
    module_mocker.patch.object(type(config), attribute="AWS_ACCESS_ID", new_callable=PropertyMock, return_value="x")
    module_mocker.patch.object(type(config), attribute="AWS_ACCESS_SECRET", new_callable=PropertyMock, return_value="x")
    meta = ExportMeta.from_config_store(config=config, store=None, build_repo_ref="83fake48", trusted=True)
    # load private signing key so admin metadata can be signed in other fixtures and tests
    meta.admin_meta_keys = _admin_meta_keys()

    with mock_aws():
        s3_client = S3Client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_ID,
            aws_secret_access_key=config.AWS_ACCESS_SECRET,
            region_name="eu-west-1",
        )

    store = FakeRecordsStore(logger=logger)
    store.populate()
    exporter = SiteExporter(logger=logger, config=config, meta=meta, s3=s3_client, get_record=store.get)
    exporter.select({record.file_identifier for record in store.records})
    exporter.export()

    if not Path(site_dir.name).joinpath("favicon.ico").exists():
        msg = "Failed to generate static site"
        raise RuntimeError(msg) from None

    return site_dir


@pytest.fixture(scope="module")
def fx_exporter_static_server(fx_exporter_static_site: TemporaryDirectory):
    """Expose static site from a local server."""
    site_dir = fx_exporter_static_site.name

    if os.environ.get("CI"):
        # In CI, requests to this local server won't resolve, instead we need to symlink the site_dir to within the
        # build/ directory and then return (don't need to clean up the temp dir given the container is destroyed)
        link = Path(os.environ["STATIC_SITE_PATH"])
        link.unlink(missing_ok=True)
        link.symlink_to(site_dir)
        yield None
    else:
        python_bin = sys.executable
        args = [python_bin, "-m", "http.server", "8123", "--directory", site_dir]
        process = Popen(args, stdout=PIPE)  # noqa: S603
        retries = 5

        while retries > 0:
            try:
                conn = HTTPConnection("localhost:8123")
                conn.request("HEAD", "/")
                response = conn.getresponse()
                if response is not None:
                    break
            except ConnectionRefusedError:
                time.sleep(1)
                retries -= 1
        if not retries:
            process.terminate()
            process.wait()
            msg = "Failed to start http server"
            raise RuntimeError(msg) from None
        try:
            yield process
        finally:
            process.terminate()
            process.wait()
            fx_exporter_static_site.cleanup()
