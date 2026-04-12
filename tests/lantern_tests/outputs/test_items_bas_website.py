import json
import logging
from copy import deepcopy
from pathlib import Path

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata

from lantern.lib.metadata_library.models.record.elements.common import Constraint, Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.stores.base import SelectRecordsProtocol
from tests.conftest import _admin_meta_keys, _revision_config_min


class TestItemsBasWebsiteOutput:
    """Test BAS Public Website search items output."""

    def test_init(
        self,
        fx_logger: logging.Logger,
        fx_export_meta: ExportMeta,
        fx_select_records: SelectRecordsProtocol,
    ):
        """Can create a BAS website search output."""
        output = ItemsBasWebsiteOutput(logger=fx_logger, meta=fx_export_meta, select_records=fx_select_records)
        assert isinstance(output, ItemsBasWebsiteOutput)

    @staticmethod
    def _make_record_open(record: Record) -> None:
        """Update record to be open access."""
        # access permissions (authoritative)
        admin_meta = AdministrationMetadata(
            id=record.file_identifier, metadata_permissions=[OPEN_ACCESS], resource_permissions=[OPEN_ACCESS]
        )
        set_admin(keys=_admin_meta_keys(), record=record, admin_meta=admin_meta)
        # access constraints (informative)
        record.identification.constraints.append(
            Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
        )

    @staticmethod
    def _make_record_supersede(record: Record, identifier: str) -> None:
        """Update record to supersed another."""
        record.identification.aggregations.append(
            Aggregation(
                identifier=Identifier(identifier=identifier, namespace=CATALOGUE_NAMESPACE),
                association_type=AggregationAssociationCode.REVISION_OF,
            )
        )

    @staticmethod
    def _get_record_in_scope(identifier: str) -> RecordRevision:
        """
        Record lookup method for testing the in_scope_items method.

        Returns a record based on a given identifier. Allows controls over whether the record is considered in-scope.
        """
        record = RecordRevision.loads(deepcopy(_revision_config_min()))
        record.file_identifier = identifier

        if identifier == "in_scope":
            TestItemsBasWebsiteOutput._make_record_open(record)
            TestItemsBasWebsiteOutput._make_record_supersede(record, "out_scope_superseded")

        return record

    @staticmethod
    def _get_records_in_scope() -> list[RecordRevision]:
        """
        Wrapper for _get_record_in_scope.

        Generates a set of in and out of scope records with fixed, descriptive, identifiers.
        """
        identifiers = {"out_scope_superseded", "out_scope_not_open", "in_scope"}
        return [TestItemsBasWebsiteOutput._get_record_in_scope(identifier=id_) for id_ in identifiers]

    def test_in_scope_items(self, fx_records_bas_website_output: ItemsBasWebsiteOutput):
        """Can select items in-scope for inclusion in website search."""
        fx_records_bas_website_output._select_records = self._get_records_in_scope

        results = fx_records_bas_website_output._in_scope_items
        assert len(results) == 1
        assert results[0].resource_id == "in_scope"

    def test_content(self, fx_records_bas_website_output: ItemsBasWebsiteOutput):
        """Can generate site content items."""
        build_ref = "x"
        fx_records_bas_website_output._select_records = self._get_records_in_scope
        fx_records_bas_website_output._meta.build_repo_ref = build_ref

        results = fx_records_bas_website_output.content
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SiteContent)
        data = json.loads(result.content)
        assert len(data) > 0
        assert result.path == Path("-/public-website-search/items.json")
        assert result.media_type == "application/json"
        assert result.object_meta == {"build_ref": build_ref}
