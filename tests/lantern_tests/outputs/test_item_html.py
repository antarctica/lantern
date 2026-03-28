import logging
from pathlib import Path

import pytest

from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent, SiteRedirect
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.stores.base import SelectRecordProtocol


class TestItemCatalogueOutput:
    """Test catalogue item HTML output."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_revision_model_min: RecordRevision,
        fx_select_record: SelectRecordProtocol,
    ):
        """Can create an item HTML output."""
        output = ItemCatalogueOutput(
            logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min, select_record=fx_select_record
        )
        assert isinstance(output, ItemCatalogueOutput)
        assert output.name == "Item Catalogue HTML"

    @pytest.mark.cov()
    @pytest.mark.parametrize("expected", [ItemCatalogue, ItemCataloguePhysicalMap])
    def test_item_class(
        self, fx_item_output: ItemCatalogueOutput, fx_item_config_min_physical_map: dict, expected: type[ItemCatalogue]
    ):
        """Can select correct catalogue item class based on record."""
        if expected == ItemCataloguePhysicalMap:
            fx_item_output._record = RecordRevision.loads(fx_item_config_min_physical_map)

        result = fx_item_output._item_class()
        assert result == expected

    def test_outputs(
        self,
        fx_item_output: ItemCatalogueOutput,
        fx_export_meta: ExportMeta,
        fx_revision_model_min: RecordRevision,
    ):
        """Can generate site content items."""
        results = fx_item_output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        assert "<!DOCTYPE html>" in result.content
        assert result.path == Path(f"items/{fx_revision_model_min.file_identifier}/index.html")
        assert result.media_type == "text/html"
        assert result.object_meta == {
            "build_key": fx_export_meta.build_key,
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
        }


class TestItemAliasesOutput:
    """Test item aliases HTML output."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_revision_model_min: RecordRevision,
        fx_select_record: SelectRecordProtocol,
    ):
        """Can create alias outputs for an item."""
        output = ItemAliasesOutput(logger=fx_logger, meta=fx_export_meta, record=fx_revision_model_min)
        assert isinstance(output, ItemAliasesOutput)
        assert output.name == "Item Aliases"

    def test_get_identifiers(self, fx_item_aliases_output: ItemAliasesOutput):
        """Can process any alias identifiers in record."""
        fx_item_aliases_output._record.identification.identifiers.append(
            Identifier(identifier="x", href=f"https://{CATALOGUE_NAMESPACE}/datasets/x", namespace=ALIAS_NAMESPACE)
        )

    def test_outputs(self, fx_item_aliases_output: ItemAliasesOutput, fx_revision_model_min: RecordRevision):
        """Can generate site redirect items."""
        alias = "datasets/x"
        target = "x"
        fx_item_aliases_output._record.identification.identifiers.append(
            Identifier(identifier=target, href=f"https://{CATALOGUE_NAMESPACE}/{alias}", namespace=ALIAS_NAMESPACE)
        )

        results = fx_item_aliases_output.outputs
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteRedirect)
        assert result.path == Path("datasets/x/index.html")
        assert result.redirect == f"https://example.com/items/{target}/"
        assert result.object_meta == {
            "file_identifier": fx_revision_model_min.file_identifier,
            "file_revision": fx_revision_model_min.file_revision,
        }
