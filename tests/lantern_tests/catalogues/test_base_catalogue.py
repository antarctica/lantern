import logging
from collections.abc import Callable
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory
from typing import Final

import pytest

from lantern.catalogues.base import CatalogueBase
from lantern.config import Config
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
        cat = FakeCatalogue(logger=fx_logger, config=fx_config, base_path=tmp_path)
        assert isinstance(cat, CatalogueBase)

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
        fx_fake_catalogue: FakeCatalogue,
        values: list[Callable[..., OutputBase]] | None,
        expected: tuple[list[Callable[..., OutputBase]], list[Callable[..., OutputBase]]],
    ):
        """Can sort selected output classes into individual and global types, or return all classes."""
        results = fx_fake_catalogue._group_output_classes(values)
        assert results == expected

    def test_export(self, fx_fake_catalogue: FakeCatalogue):
        """
        Can export static site.

        Note: Performs an actual export so takes a few seconds.
        """
        export_path: Path = fx_fake_catalogue._path
        fx_fake_catalogue.export(identifiers={"3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"})  # product min
        assert export_path.joinpath("favicon.ico").exists()

    def test_check(self, fx_fake_catalogue: FakeCatalogue, fx_exporter_static_server: Popen):
        """
        Can check catalogue contents.

        Performs a real export and check of a test record using a local server (as per e2e tests). This server
        contains all test records which takes a few seconds to build.

        Note: Uses the minimal product test record ('3c77ffae-6aa0-4c26-bc34-5521dbf4bf23') rather the check record
        (`cf80b941-3de6-4a04-8f5a-a2349c1e3ae0`) because it has external distribution options with fake values that
        trip up the test.
        """
        identifiers = {"3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"}  # minimal product test record
        fx_fake_catalogue._meta.base_url = "http://localhost:8123"
        fx_fake_catalogue.export(identifiers)
        export_path: Path = fx_fake_catalogue._path

        fx_fake_catalogue.check(identifiers)
        assert export_path.joinpath("-/checks/data.json").exists()

    def test_purge(self, fx_fake_catalogue: FakeCatalogue):
        """Can purge export target."""
        identifiers = {"3c77ffae-6aa0-4c26-bc34-5521dbf4bf23"}  # minimal product test record
        export_path: Path = fx_fake_catalogue._path
        fx_fake_catalogue.export(identifiers)
        assert export_path.joinpath("favicon.ico").exists()

        fx_fake_catalogue.purge()
        assert not export_path.joinpath("favicon.ico").exists()
