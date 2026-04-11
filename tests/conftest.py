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
from typing import get_args
from unittest.mock import MagicMock, PropertyMock

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys, AdministrationWrapper
from boto3 import client as S3Client  # noqa: N812
from gitlab import Gitlab
from moto import mock_aws
from pytest_mock import MockerFixture

from lantern.catalogue import BasCatalogue, BasCatEnv, BasCatTrusted, BasCatUntrusted
from lantern.config import Config
from lantern.exporters.local import LocalExporter
from lantern.exporters.rsync import RsyncExporter
from lantern.exporters.s3 import S3Exporter
from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.dataclasses import ItemProperties as ArcGisItemProperties
from lantern.lib.arcgis.gis.enums import ItemType as ArcGisItemType
from lantern.lib.arcgis.gis.enums import SharingLevel as ArcGisSharingLevel
from lantern.lib.metadata_library.models.record.elements.common import Date, Dates, Identifiers
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record as RecordBase
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.item.arcgis.item import ItemArcGis
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.base.item import ItemBase
from lantern.models.item.catalogue.elements import Dates as ItemCatDates
from lantern.models.item.catalogue.elements import Identifiers as ItemCatIdentifiers
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.item.catalogue.tabs import AdditionalInfoTab, AdminTab
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent, SiteEnvironment, SiteMeta, SitePageMeta
from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext
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
from lantern.stores.base import SelectRecordProtocol, SelectRecordsProtocol
from lantern.stores.gitlab import GitLabSource, GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore, GitLabLocalCache
from lantern.utils import get_jinja_env, prettify_html
from lantern.verification import Verification
from tests.resources.admin_keys import test_keys
from tests.resources.catalogues.fake_catalogue import FakeCatalogue
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


@pytest.fixture(scope="session")
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
def fx_site_page_meta() -> SitePageMeta:
    """Site page metadata."""
    return SitePageMeta(title="x", url="x", description="x", inc_meta=False)


@pytest.fixture()
def fx_site_content() -> SiteContent:
    """Site content item."""
    return SiteContent(content="x", path=Path("x"), media_type="x")


@pytest.fixture()
def fx_site_meta(fx_config: Config) -> SiteMeta:
    """Site build metadata."""
    return SiteMeta.from_config_store(config=fx_config, env="testing", store=None, build_repo_ref="83fake48")


@pytest.fixture()
def fx_export_meta(fx_config: Config) -> ExportMeta:
    """Exporter build metadata (superset of site metadata)."""
    return ExportMeta.from_config_store(config=fx_config, env="testing", store=None, build_repo_ref="83fake48")


@lru_cache(maxsize=1)
def _admin_meta_keys() -> AdministrationKeys:
    """
    BAS Metadata Library administration metadata test encryption and signing keys.

    These test keys are not secret and so not sensitive.

    Standalone method to allow use outside of fixtures in test parametrisation.

    Cached for better performance.
    """
    return test_keys()


@pytest.fixture()
def fx_admin_meta_keys() -> AdministrationKeys:
    """Administration keys for signing and encrypting administrative metadata."""
    return _admin_meta_keys()


@pytest.fixture()
def fx_admin_meta_element() -> AdministrationMetadata:
    """Administrative metadata element."""
    return AdministrationMetadata(id="x")


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
    Minimal (base) record configuration (MAGIC presets).

    Minimal record that can create a valid RecordMagic instance. Does not include properties the preset will
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
def fx_item_base_model_min(fx_item_config_min_base: dict) -> ItemBase:
    """Minimal ItemBase model instance."""
    return ItemBase(record=RecordRevision.loads(fx_item_config_min_base))


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
    meta = SiteMeta.from_config_store(config=Config(), env="testing", store=None, build_repo_ref="83fake48")
    model = ItemCatalogue(
        site_meta=meta,
        record=RecordRevision.loads(_item_config_min_catalogue()),
        admin_meta_keys=_admin_meta_keys(),
        trusted_context=True,
        select_record=_select_record,
    )
    set_admin(keys=model._admin_keys, record=model._record, admin_meta=AdministrationMetadata(id=model.resource_id))
    return model


@pytest.fixture()
def fx_item_cat_model_min(
    fx_site_meta: SiteMeta,
    fx_item_config_min_catalogue: dict,
    fx_admin_meta_keys: AdministrationKeys,
    fx_select_record: SelectRecordProtocol,
) -> ItemCatalogue:
    """
    Minimal ItemCatalogue model instance.

    Includes minimal admin metadata and admin keys required by admin tab.
    """
    model = ItemCatalogue(
        site_meta=fx_site_meta,
        record=RecordRevision.loads(fx_item_config_min_catalogue),
        admin_meta_keys=fx_admin_meta_keys,
        trusted_context=True,
        select_record=fx_select_record,
    )
    set_admin(keys=model._admin_keys, record=model._record, admin_meta=AdministrationMetadata(id=model.resource_id))
    return model


@pytest.fixture()
def fx_item_cat_model_open(
    fx_item_cat_model_min: ItemCatalogue,
    fx_item_config_min_catalogue: dict,
) -> ItemCatalogue:
    """Minimal cloned ItemCatalogue model instance with minimal admin metadata to allow open access."""
    model = _item_cat_model_min()
    set_admin(
        keys=model._admin_keys,
        record=model._record,
        admin_meta=AdministrationMetadata(
            id=model.resource_id, metadata_permissions=[OPEN_ACCESS], resource_permissions=[OPEN_ACCESS]
        ),
    )
    return model


@pytest.fixture()
def fx_item_physical_map_model_min(
    fx_site_meta: SiteMeta,
    fx_item_config_min_physical_map: dict,
    fx_admin_meta_keys: AdministrationKeys,
    fx_select_record: SelectRecordProtocol,
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
        select_record=fx_select_record,
    )
    set_admin(keys=model._admin_keys, record=model._record, admin_meta=AdministrationMetadata(id=model.resource_id))
    return model


def _select_record(identifier: str) -> RecordRevision:
    """
    Minimal record lookup method.

    Standalone method to allow use outside of fixtures.
    """
    record = RecordRevision.loads(deepcopy(_revision_config_min()))
    record.file_identifier = identifier
    return record


def _select_records(file_identifiers: set[str]) -> list[RecordRevision]:
    """
    Minimal records fetch method.

    Standalone method to allow use outside of fixtures.
    """
    return [_select_record(fid) for fid in file_identifiers]


def _select_records_fixed(file_identifiers: set[str] | None = None) -> list[RecordRevision]:
    """
    Minimal records fetch method returning a fixed set of records.

    `file_identifiers` parameter is ignored but needed for compatibility with the SelectRecordsProtocol and used by
    the Verification class.

    Standalone method to allow use outside of fixtures.
    """
    return [_select_record("x")]


@pytest.fixture()
def fx_select_record() -> Callable[[str], RecordRevision]:
    """Minimal record lookup method."""
    return _select_record


@pytest.fixture()
def fx_select_records() -> SelectRecordsProtocol:
    """Minimal records lookup method."""
    return _select_records


@pytest.fixture()
def fx_select_records_fixed() -> SelectRecordsProtocol:
    """Minimal records lookup method returning a fixed set of records."""
    return _select_records_fixed


@pytest.fixture()
def fx_item_cat_info_tab_minimal(fx_site_meta: SiteMeta) -> AdditionalInfoTab:
    """Minimal ItemCatalogue additional information tab."""
    dates = ItemCatDates(dates=Dates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
    identifiers = ItemCatIdentifiers(Identifiers([]))
    return AdditionalInfoTab(
        item_id="x",
        item_type=HierarchyLevelCode.PRODUCT,
        identifiers=identifiers,
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
        metadata_access=AccessLevel.NONE,
        resource_access=AccessLevel.NONE,
        admin_meta=None,
    )


@pytest.fixture()
def fx_lib_arcgis_item_properties() -> ArcGisItemProperties:
    """Minimal ArcGiS Item properties instance."""
    return ArcGisItemProperties(title="x", item_type=ArcGisItemType.FEATURE_SERVICE, metadata="x")


@pytest.fixture()
def fx_lib_arcgis_item(fx_lib_arcgis_item_properties: ArcGisItemProperties) -> ArcGisItem:
    """Minimal ArcGiS Item instance."""
    return ArcGisItem(
        id="x",
        owner="x",
        org_id="x",
        url="x",
        properties=fx_lib_arcgis_item_properties,
        sharing_level=ArcGisSharingLevel.PRIVATE,
    )


@pytest.fixture()
def fx_item_arc_model_min(fx_record_model_min: Record, fx_lib_arcgis_item: ArcGisItem):
    """Minimal ItemArcGis model instance."""
    return ItemArcGis(fx_record_model_min, arcgis_item=fx_lib_arcgis_item)


def _init_fake_store(logger: logging.Logger, config: Config | None = None, frozen: bool = False) -> FakeRecordsStore:
    """Callable to initialize a FakeRecordsStore."""
    return FakeRecordsStore(logger=logger, frozen=frozen)


@pytest.fixture()
def fx_fake_store(fx_logger: logging.Logger) -> FakeRecordsStore:
    """Fake records store."""
    return _init_fake_store(fx_logger)


@pytest.fixture()
def fx_gitlab_source(fx_config: Config) -> GitLabSource:
    """GitLab store source."""
    return GitLabSource(
        endpoint=fx_config.STORE_GITLAB_ENDPOINT,
        project=fx_config.STORE_GITLAB_PROJECT_ID,
        ref=fx_config.STORE_GITLAB_BRANCH,
    )


@pytest.fixture()
def fx_gitlab_store(fx_logger: logging.Logger, fx_config: Config, fx_gitlab_source: GitLabSource) -> GitLabStore:
    """GitLab store."""
    return GitLabStore(logger=fx_logger, source=fx_gitlab_source, access_token=fx_config.STORE_GITLAB_TOKEN)


@pytest.fixture()
def fx_gitlab_cache(fx_logger: logging.Logger, fx_config: Config, fx_gitlab_source: GitLabSource) -> GitLabLocalCache:
    """GitLab local cache."""
    with TemporaryDirectory() as tmp_path:
        cache_path = Path(tmp_path) / ".cache"

    return GitLabLocalCache(
        logger=fx_logger,
        parallel_jobs=fx_config.PARALLEL_JOBS,
        path=cache_path,
        gitlab_token="x",  # noqa: S106
        gitlab_client=Gitlab(url=fx_gitlab_source.endpoint, private_token=fx_config.STORE_GITLAB_TOKEN),
        gitlab_source=fx_gitlab_source,
    )


def _gitlab_cache_create(cache: fx_gitlab_cache) -> None:
    """
    Copy static GitLab local cache to simulate cloning from remote repository.

    Intended to be used as a side effect when mocking the `GitLabStore._create` method.
    """
    cache_src = Path(__file__).resolve().parent / "resources" / "stores" / "gitlab_cache"
    shutil.copytree(cache_src, cache._path, dirs_exist_ok=True)


@pytest.fixture()
def fx_gitlab_cache_pop(mocker: MockerFixture, fx_gitlab_cache: GitLabLocalCache) -> GitLabLocalCache:
    """
    GitLab local cache populated with records.

    To simulate and bypass fetching records from remote repository.
    """
    mocker.patch.object(fx_gitlab_cache, "_create", side_effect=lambda: _gitlab_cache_create(fx_gitlab_cache))
    fx_gitlab_cache._create()
    return fx_gitlab_cache


@pytest.fixture()
def fx_gitlab_cache_frozen(fx_gitlab_cache: GitLabLocalCache) -> GitLabLocalCache:
    """Frozen GitLab local cache populated with records."""
    fx_gitlab_cache._frozen = True
    _gitlab_cache_create(fx_gitlab_cache)
    return fx_gitlab_cache


@pytest.fixture()
def fx_gitlab_cached_store(fx_logger: logging.Logger, fx_config: Config, fx_gitlab_source: GitLabSource) -> GitLabStore:
    """GitLab cached store."""
    with TemporaryDirectory() as tmp_path:
        cache_path = Path(tmp_path) / ".cache"

    return GitLabCachedStore(
        logger=fx_logger,
        source=fx_gitlab_source,
        access_token=fx_config.STORE_GITLAB_TOKEN,
        parallel_jobs=fx_config.PARALLEL_JOBS,
        cache_dir=cache_path,
    )


@pytest.fixture()
def fx_gitlab_cached_store_frozen(fx_gitlab_cached_store: GitLabCachedStore) -> GitLabCachedStore:
    """Frozen GitLab cached store."""
    fx_gitlab_cached_store._frozen = True
    return fx_gitlab_cached_store


@pytest.fixture()
def fx_gitlab_cached_store_pop(
    mocker: MockerFixture, fx_gitlab_cached_store: GitLabCachedStore, fx_gitlab_cache_pop: GitLabLocalCache
) -> GitLabCachedStore:
    """GitLab cached store with a populated/existing cache."""
    # mock:
    # - fx_gitlab_cache_pop._project.commits.get to return an object with an 'attributes' dict property
    # - fx_gitlab_cache_pop._project.http_url_to_repo to return a URL
    mock_project = MagicMock()
    mock_commit = MagicMock()
    mock_commit.attributes = {"id": "x"}
    mock_project.commits.get.return_value = mock_commit
    mock_project.http_url_to_repo = "https://gitlab.example.com/x.git"
    mocker.patch.object(type(fx_gitlab_cache_pop), "_project", new_callable=PropertyMock, return_value=mock_project)

    fx_gitlab_cached_store._cache = fx_gitlab_cache_pop
    return fx_gitlab_cached_store


def _index_site_content_outputs(outputs: list[SiteContent]) -> dict[Path, SiteContent]:
    """Index site content outputs by path."""
    return {output.path: output for output in outputs}


@pytest.fixture()
def fx_item_output(
    fx_logger: logging.Logger,
    fx_export_meta: ExportMeta,
    fx_revision_model_min: RecordRevision,
    fx_select_record: SelectRecordProtocol,
) -> ItemCatalogueOutput:
    """Catalogue item output."""
    return ItemCatalogueOutput(
        logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min, select_record=fx_select_record
    )


@pytest.fixture()
def fx_item_aliases_output(
    fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision
) -> ItemAliasesOutput:
    """Catalogue item aliases output."""
    return ItemAliasesOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)


@pytest.fixture()
def fx_record_iso_xml_output(
    fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_revision_model_min: RecordRevision
) -> RecordIsoXmlOutput:
    """ISO 19115 record XML output."""
    return RecordIsoXmlOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)


@pytest.fixture()
def fx_records_bas_website_output(
    fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records: SelectRecordsProtocol
) -> ItemsBasWebsiteOutput:
    """BAS Public Website Search items output (empty)."""
    return ItemsBasWebsiteOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records)


@pytest.fixture()
def fx_records_waf_output(
    fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_select_records: SelectRecordsProtocol
) -> RecordsWafOutput:
    """Records WAF output (empty)."""
    return RecordsWafOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records)


@pytest.fixture()
def fx_local_exporter(fx_logger: logging.Logger) -> LocalExporter:
    """Local filesystem exporter using a temporary directory."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "local"
    return LocalExporter(logger=fx_logger, path=tmp_path)


@pytest.fixture()
def fx_rsync_exporter(fx_logger: logging.Logger) -> RsyncExporter:
    """Rsync exporter using a temporary directory."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "rsync"
    return RsyncExporter(logger=fx_logger, path=tmp_path)


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
def fx_s3_exporter(fx_logger: logging.Logger, fx_s3_client: S3Client, fx_s3_bucket_name: str) -> S3Exporter:
    """S3 exporter using mocked s3 client."""
    return S3Exporter(logger=fx_logger, s3=fx_s3_client, bucket=fx_s3_bucket_name, parallel_jobs=1)


@pytest.fixture()
def fx_site(fx_logger: logging.Logger, fx_export_meta: ExportMeta, fx_fake_store: FakeRecordsStore) -> Site:
    """Site generator using fake/test records."""
    return Site(logger=fx_logger, meta=fx_export_meta, store=fx_fake_store)


@pytest.fixture()
def fx_verification_context(fx_export_meta: ExportMeta) -> VerificationContext:
    """Site Verification context."""
    return {
        "BASE_URL": fx_export_meta.base_url,
        "SHAREPOINT_PROXY_ENDPOINT": "x",
        "SAN_PROXY_ENDPOINT": "x",
    }


@pytest.fixture()
def fx_verification(
    fx_logger: logging.Logger,
    fx_export_meta: ExportMeta,
    fx_select_records: SelectRecordsProtocol,
    fx_verification_context: VerificationContext,
) -> Verification:
    """Site Verification with a global verification context."""
    return Verification(
        logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records, context=fx_verification_context
    )


@pytest.fixture()
def fx_verification_sel(fx_verification: Verification, fx_select_records_fixed: SelectRecordsProtocol) -> Verification:
    """Site Verification with a single selectable record."""
    fx_verification._select_records = fx_select_records_fixed
    return fx_verification


@pytest.fixture()
def fx_verification_post_run(fx_verification_sel: Verification) -> Verification:
    """Site Verification with a single selectable record and applicable jobs in a PASS state."""
    fx_verification_sel._jobs = [
        VerificationJob(
            result=VerificationResult.PASS,
            type=VerificationType.SITE_PAGES,
            url="https://data.bas.ac.uk/-/index",
            context=fx_verification_sel._context,
            data={"duration": timedelta(microseconds=1)},
        ),
        VerificationJob(
            result=VerificationResult.PASS,
            type=VerificationType.ITEM_PAGES,
            url="https://data.bas.ac.uk/items/123",
            context=fx_verification_sel._context,
            data={"file_identifier": "x", "duration": timedelta(microseconds=1)},
        ),
    ]
    return fx_verification_sel


@pytest.fixture()
def fx_fake_catalogue(fx_logger: logging.Logger, fx_config: Config, fx_fake_store: FakeRecordsStore):
    """Fake catalogue instance."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "output"
    return FakeCatalogue(logger=fx_logger, config=fx_config, store=fx_fake_store, base_path=tmp_path)


@pytest.fixture()
def fx_bas_cat_untrusted(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_export_meta: ExportMeta,
    fx_fake_store: FakeRecordsStore,
    fx_s3_client: S3Client,
    fx_s3_bucket_name: str,
) -> BasCatUntrusted:
    """
    BAS untrusted catalogue instance.

    Uses Fake store over GitLab to avoid mocking and/or request recordings.

    Sets S3 export to local mock via mocked config.

    Mocks verification to return fixed results.
    """
    mock_verification = mocker.MagicMock()
    mock_verification.process.return_value = None
    mock_verification.outputs = [
        SiteContent(content="", path=Path("-/verification/data.json"), media_type="application/json")
    ]
    mocker.patch("lantern.catalogue.Verification", return_value=mock_verification)

    return BasCatUntrusted(
        logger=fx_logger,
        meta=fx_export_meta,
        store=fx_fake_store,
        s3=fx_s3_client,
        bucket=fx_s3_bucket_name,
        verify_sharepoint_endpoint="x",
        verify_san_endpoint="x",
    )


@pytest.fixture()
def fx_bas_cat_trusted(
    fx_logger: logging.Logger,
    fx_export_meta: ExportMeta,
    fx_fake_store: FakeRecordsStore,
    fx_s3_client: S3Client,
    fx_s3_bucket_name: str,
) -> BasCatTrusted:
    """
    BAS trusted catalogue instance.

    Uses Fake store over GitLab to avoid mocking and/or request recordings.

    Sets Rsync export to a temp directory.

    Mocks verification to return fixed results.
    """
    with TemporaryDirectory() as tmp_dir:
        rsync_path = Path(tmp_dir) / "rsync"
    fx_export_meta.trusted = True
    return BasCatTrusted(logger=fx_logger, meta=fx_export_meta, store=fx_fake_store, host=None, path=rsync_path)


@pytest.fixture()
def fx_bas_cat_env(
    fx_logger: logging.Logger,
    fx_config: Config,
    fx_fake_store: FakeRecordsStore,
    fx_s3_client: S3Client,
    fx_bas_cat_untrusted: BasCatUntrusted,
    fx_bas_cat_trusted: BasCatTrusted,
) -> BasCatEnv:
    """BAS untrusted catalogue instance."""
    cat = BasCatEnv(logger=fx_logger, config=fx_config, store=fx_fake_store, s3=fx_s3_client, env="testing")
    cat._untrusted = fx_bas_cat_untrusted
    cat._trusted = fx_bas_cat_trusted
    return cat


@pytest.fixture()
def fx_bas_catalogue(
    fx_logger: logging.Logger,
    fx_config: Config,
    fx_fake_store: FakeRecordsStore,
    fx_s3_client: S3Client,
    fx_s3_bucket_name: str,
    fx_bas_cat_env: BasCatEnv,
) -> BasCatalogue:
    """
    BAS catalogue instance.

    Uses Fake store over GitLab to avoid mocking and/or request recordings.

    Mocks remote export locations (to local S3 and temp directory) via config.

    Mocks verification to return fixed results.
    """
    cat = BasCatalogue(logger=fx_logger, config=fx_config, store=fx_fake_store, s3=fx_s3_client)
    cat._envs = dict.fromkeys(get_args(SiteEnvironment), fx_bas_cat_env)
    return cat


@pytest.fixture(scope="session")
def fx_static_site() -> TemporaryDirectory:
    """
    Build static site and export to a temp directory.

    Session scoped for performance. This means usual fixtures for logging, stores, etc. can't be used and are duplicated.
    """
    site_dir = TemporaryDirectory()
    site_path = Path(site_dir.name)

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    config = Config()
    store = FakeRecordsStore(logger=logger)
    meta = ExportMeta.from_config_store(
        config=config, env="testing", store=None, build_repo_ref="83fake48", trusted=True
    )
    exporter = LocalExporter(logger=logger, path=site_path)
    site = Site(logger=logger, meta=meta, store=store)

    content = site.process(
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
    )
    exporter.export(content)
    if not Path(site_dir.name).joinpath("favicon.ico").exists():
        msg = "Failed to generate static site"
        raise RuntimeError(msg) from None

    return site_dir


@pytest.fixture(scope="session")
def fx_exporter_static_server(fx_static_site: TemporaryDirectory):
    """Expose static site from a local server."""
    site_dir = fx_static_site.name

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
            fx_static_site.cleanup()
