import logging
import os
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from http.client import HTTPConnection
from importlib.metadata import version
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

import pytest
from boto3 import client as S3Client  # noqa: N812
from moto import mock_aws
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.exporters.base_exporter import Exporter, ResourceExporter, S3Utils
from lantern.exporters.html_exporter import HtmlAliasesExporter, HtmlExporter
from lantern.exporters.iso_exporter import IsoXmlHtmlExporter
from lantern.exporters.records_exporter import RecordsExporter
from lantern.exporters.site_exporter import SiteExporter, SiteIndexExporter, SitePagesExporter, SiteResourcesExporter
from lantern.models.item.catalogue import AdditionalInfoTab, ItemCatalogue
from lantern.models.item.catalogue.elements import Dates as ItemCatDates
from lantern.models.item.catalogue.elements import Identifiers as ItemCatIdentifiers
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record import Record
from lantern.models.record.elements.common import Date, Dates, Identifier, Identifiers
from lantern.models.record.enums import HierarchyLevelCode
from lantern.models.record.summary import RecordSummary
from tests.resources.exporters.fake_exporter import FakeExporter, FakeResourceExporter
from tests.resources.stores.fake_records_store import FakeRecordsStore


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


def _record_config_minimal_iso() -> dict:
    """
    Minimal record configuration (ISO).

    Minimal record that will validate against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema.

    Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return {
        "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
        "hierarchy_level": "dataset",
        "metadata": {
            "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
            "date_stamp": "2014-06-30",
        },
        "identification": {
            "title": {"value": "x"},
            "dates": {"creation": "2014-06-30"},
            "abstract": "x",
        },
    }


@pytest.fixture()
def fx_record_config_minimal_iso() -> dict:
    """
    Minimal record configuration (ISO).

    Minimal record that will validate against the BAS Metadata Library ISO 19115:2003 / 19115-2:2009 v4 schema.

    Types must be safe to encode as JSON.
    """
    return _record_config_minimal_iso()


def _record_config_minimal_item(base_config: dict) -> dict:
    """
    Minimal record configuration (Item).

    Minimal record that can be used with an ItemBase. Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    config = deepcopy(base_config)
    config["file_identifier"] = "x"
    return config


@pytest.fixture()
def fx_record_config_minimal_item(fx_record_config_minimal_iso: dict) -> dict:
    """Minimal record configuration (Item)."""
    return _record_config_minimal_item(fx_record_config_minimal_iso)


@pytest.fixture()
def fx_record_config_minimal_magic_preset(fx_record_config_minimal_item: dict) -> dict:
    """
    Minimal record configuration (MAGIC Preset).

    Minimal record that can create a valid RecordMagicDiscoveryV1 instance. Does not include properties the preset will
    configure automatically (such as identifiers, contacts, domain consistencies).

    Types must be safe to encode as JSON.
    """
    return deepcopy(fx_record_config_minimal_item)


def _record_config_minimal_item_catalogue(base_config: dict) -> dict:
    """
    Minimal record configuration (ItemCatalogue).

    Minimal record that can be used with an ItemCatalogue. Types must be safe to encode as JSON.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    config = deepcopy(base_config)
    config["identification"]["contacts"] = deepcopy(config["metadata"]["contacts"])
    config["identification"]["contacts"][0]["email"] = "x"
    config["identification"]["identifiers"] = [
        {
            "identifier": config["file_identifier"],
            "href": f"https://data.bas.ac.uk/items/{_record_config_minimal_item}",
            "namespace": "data.bas.ac.uk",
        }
    ]

    return config


@pytest.fixture()
def fx_record_config_minimal_item_catalogue(fx_record_config_minimal_item: dict) -> dict:
    """Minimal record configuration (ItemCatalogue)."""
    return _record_config_minimal_item_catalogue(fx_record_config_minimal_item)


@pytest.fixture()
def fx_record_minimal_iso(fx_record_config_minimal_iso: dict) -> Record:
    """Minimal record instance (ISO)."""
    return Record.loads(fx_record_config_minimal_iso)


@pytest.fixture()
def fx_record_minimal_item(fx_record_config_minimal_item: dict) -> Record:
    """Minimal record instance (Item)."""
    return Record.loads(fx_record_config_minimal_item)


@pytest.fixture()
def fx_record_minimal_item_catalogue(fx_record_config_minimal_item_catalogue: dict) -> Record:
    """Minimal record instance (ItemCatalogue)."""
    return Record.loads(fx_record_config_minimal_item_catalogue)


@pytest.fixture()
def fx_record_minimal_item_catalogue_physical_map(fx_record_config_minimal_item_catalogue: dict) -> Record:
    """Minimal record instance (ItemCataloguePhysicalMap)."""
    config = deepcopy(fx_record_config_minimal_item_catalogue)
    config["hierarchy_level"] = HierarchyLevelCode.PAPER_MAP_PRODUCT.value
    config["identification"]["aggregations"] = [
        {
            "identifier": {"identifier": "x", "href": "x", "namespace": "x"},
            "association_type": "isComposedOf",
            "initiative_type": "paperMap",
        }
    ]
    return Record.loads(config)


@pytest.fixture()
def fx_record_summary_minimal_item(fx_record_minimal_item_catalogue: Record) -> RecordSummary:
    """Minimal record summary instance (Item)."""
    return RecordSummary.loads(fx_record_minimal_item_catalogue)


def _get_record(identifier: str) -> Record:
    """
    Minimal record lookup method.

    Standalone method to allow use outside of fixtures.
    """
    config = deepcopy(_record_config_minimal_iso())
    config["file_identifier"] = identifier
    return Record.loads(config)


@pytest.fixture()
def fx_get_record() -> callable:
    """Minimal record lookup method."""
    return _get_record


def _get_record_summary(identifier: str) -> RecordSummary:
    """
    Minimal record summary lookup method.

    Standalone method to allow use outside of fixtures.
    """
    date_ = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
    return RecordSummary(
        file_identifier=identifier,
        hierarchy_level=HierarchyLevelCode.PRODUCT,
        date_stamp=date_.date,
        title="x",
        creation=date_,
    )


@pytest.fixture()
def fx_get_record_summary() -> callable:
    """Minimal record summary lookup method."""
    return _get_record_summary


@pytest.fixture()
def fx_item_cat_info_tab_minimal() -> AdditionalInfoTab:
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
    )


def _item_catalogue_min() -> ItemCatalogue:
    """
    ItemCatalogue based on minimal catalogue record.

    Standalone method to allow use outside of fixtures in test parametrisation.
    """
    return ItemCatalogue(
        config=Config(),
        record=Record.loads(
            _record_config_minimal_item_catalogue(_record_config_minimal_item(_record_config_minimal_iso()))
        ),
        get_record_summary=_get_record_summary,
    )


@pytest.fixture()
def fx_item_catalogue_min(
    fx_config: Config, fx_record_minimal_item_catalogue: Record, fx_get_record_summary: callable
) -> ItemCatalogue:
    """ItemCatalogue based on minimal catalogue record."""
    return ItemCatalogue(
        config=fx_config,
        record=fx_record_minimal_item_catalogue,
        get_record_summary=fx_get_record_summary,
    )


@pytest.fixture()
def fx_item_catalogue_min_physical_map(
    fx_config: Config,
    fx_record_minimal_item_catalogue_physical_map: Record,
    fx_get_record: callable,
    fx_get_record_summary: callable,
) -> ItemCataloguePhysicalMap:
    """ItemCataloguePhysicalMap based on minimal catalogue record for a physical map."""
    return ItemCataloguePhysicalMap(
        config=fx_config,
        record=fx_record_minimal_item_catalogue_physical_map,
        get_record=fx_get_record,
        get_record_summary=fx_get_record_summary,
    )


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

    return FakeExporter(config=mock_config, logger=fx_logger, s3=fx_s3_client)


@pytest.fixture()
def fx_exporter_resource_base(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_exporter_base: Exporter,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_record_minimal_item: Record,
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

    return FakeResourceExporter(
        config=mock_config,
        logger=fx_logger,
        s3=fx_s3_client,
        record=fx_record_minimal_item,
        export_base=output_path.joinpath("x"),
        export_name="x.txt",
    )


@pytest.fixture()
def fx_exporter_iso_xml_html(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_record_minimal_item: Record,
) -> Exporter:
    """ISO 19115 XML as HTML exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        base_path = Path(tmp_path)
        exports_path = base_path.joinpath("exports")
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=base_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    return IsoXmlHtmlExporter(
        config=mock_config,
        logger=fx_logger,
        s3=fx_s3_client,
        record=fx_record_minimal_item,
        export_base=exports_path,
    )


@pytest.fixture()
def fx_exporter_html(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_record_minimal_item_catalogue: Record,
) -> HtmlExporter:
    """HTML exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")

    return HtmlExporter(
        config=mock_config,
        logger=fx_logger,
        s3=fx_s3_client,
        record=fx_record_minimal_item_catalogue,
        export_base=output_path,
        get_record=_get_record,
        get_record_summary=_get_record_summary,
    )


@pytest.fixture()
def fx_exporter_html_alias(
    mocker: MockerFixture,
    fx_logger: logging.Logger,
    fx_s3_bucket_name: str,
    fx_s3_client: S3Client,
    fx_record_minimal_item_catalogue: Record,
) -> HtmlAliasesExporter:
    """HTML alias exporter with a mocked config and S3 client."""
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    fx_record_minimal_item_catalogue.identification.identifiers.append(
        Identifier(identifier="x", href="https://data.bas.ac.uk/datasets/x", namespace="alias.data.bas.ac.uk")
    )

    return HtmlAliasesExporter(
        config=mock_config,
        logger=fx_logger,
        s3=fx_s3_client,
        record=fx_record_minimal_item_catalogue,
        site_base=output_path,
    )


@pytest.fixture()
def fx_exporter_records(
    mocker: MockerFixture, fx_logger: logging.Logger, fx_s3_bucket_name: str, fx_s3_client: S3Client
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
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")

    return RecordsExporter(config=mock_config, logger=fx_logger, s3=fx_s3_client)


@pytest.fixture()
def fx_exporter_records_pop(
    fx_exporter_records: RecordsExporter, fx_record_minimal_item_catalogue: Record
) -> RecordsExporter:
    """Site records exporter populated with a single record."""
    summary = RecordSummary.loads(fx_record_minimal_item_catalogue)
    fx_exporter_records.loads(summaries=[summary], records=[fx_record_minimal_item_catalogue])
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

    return SiteResourcesExporter(config=mock_config, logger=fx_logger, s3=fx_s3_client)


@pytest.fixture()
def fx_exporter_site_index(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_logger: logging.Logger, fx_s3_client: S3Client
) -> SiteIndexExporter:
    """
    Site index exporter (empty).

    With:
    - a mocked config and S3 client
    - a minimal sample record
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)

    return SiteIndexExporter(config=mock_config, s3=fx_s3_client, logger=fx_logger)


@pytest.fixture()
def fx_exporter_site_index_pop(
    fx_exporter_site_index: SiteIndexExporter, fx_record_minimal_item_catalogue: Record
) -> SiteIndexExporter:
    """Site index exporter populated with a single record summary."""
    fx_record_minimal_item_catalogue.identification.identifiers.append(
        Identifier(identifier="x", href="https://data.bas.ac.uk/datasets/x", namespace="alias.data.bas.ac.uk")
    )
    records = [fx_record_minimal_item_catalogue]
    summaries = [RecordSummary.loads(fx_record_minimal_item_catalogue)]
    fx_exporter_site_index.loads(summaries=summaries, records=records)
    return fx_exporter_site_index


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

    return SitePagesExporter(config=mock_config, s3=fx_s3_client, logger=fx_logger)


@pytest.fixture()
def fx_exporter_site(
    mocker: MockerFixture, fx_s3_bucket_name: str, fx_logger: logging.Logger, fx_s3_client: S3Client
) -> SiteExporter:
    """
    Site exporter (empty records).

    With:
    - a mocked config and S3 client
    - a minimal sample record
    """
    with TemporaryDirectory() as tmp_path:
        output_path = Path(tmp_path)
    mock_config = mocker.Mock()
    type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
    type(mock_config).AWS_S3_BUCKET = PropertyMock(return_value=fx_s3_bucket_name)
    type(mock_config).TEMPLATES_ITEM_MAPS_ENDPOINT = PropertyMock(return_value="x")
    type(mock_config).TEMPLATES_ITEM_CONTACT_ENDPOINT = PropertyMock(return_value="x")

    return SiteExporter(config=mock_config, s3=fx_s3_client, logger=fx_logger)


@pytest.fixture(scope="module")
def fx_exporter_static_site(module_mocker: MockerFixture) -> TemporaryDirectory:
    """
    Build static site and export to a temp directory.

    Module scoped for performance. Means usual fixtures for config and S3Client can't be used and are duplicated.
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

    with mock_aws():
        s3_client = S3Client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_ID,
            aws_secret_access_key=config.AWS_ACCESS_SECRET,
            region_name="eu-west-1",
        )

    store = FakeRecordsStore(logger=logger)
    store.populate()
    exporter = SiteExporter(config=config, s3=s3_client, logger=logger)
    exporter.loads(summaries=store.summaries, records=store.records)
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
