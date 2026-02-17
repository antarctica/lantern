import json
import logging
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from pytest_mock import MockerFixture

from lantern.exporters.website import WebsiteSearchExporter
from lantern.lib.metadata_library.models.record.elements.common import Constraint, Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from tests.conftest import _admin_meta_keys, _revision_config_min, _select_records_open


class TestWebsiteSearchExporter:
    """Test public website search exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)
        meta = ExportMeta.from_config_store(config=mock_config, store=None, build_repo_ref="83fake48")

        exporter = WebsiteSearchExporter(meta=meta, s3=s3_client, logger=fx_logger, select_records=_select_records_open)

        assert isinstance(exporter, WebsiteSearchExporter)
        assert exporter.name == "BAS Public Website Search Results"

    def test_get_superseded_records(
        self, fx_exporter_website_search: WebsiteSearchExporter, fx_revision_model_min: RecordRevision
    ):
        """Can determine superseded records."""
        successor = deepcopy(fx_revision_model_min)
        successor.file_identifier = "y"
        successor.identification.aggregations.append(
            Aggregation(
                identifier=Identifier(identifier=fx_revision_model_min.file_identifier, namespace="data.bas.ac.uk"),
                association_type=AggregationAssociationCode.REVISION_OF,
            )
        )

        results = fx_exporter_website_search._get_superseded_records(records=[fx_revision_model_min, successor])
        assert results == [fx_revision_model_min.file_identifier]

    @staticmethod
    def _get_record_in_scope(identifier: str) -> RecordRevision:
        """Record lookup method for testing in_scope_items method."""
        record = RecordRevision.loads(deepcopy(_revision_config_min()))
        record.file_identifier = identifier

        if identifier == "in_scope":
            # access permissions
            admin_meta = AdministrationMetadata(
                id=record.file_identifier, metadata_permissions=[OPEN_ACCESS], resource_permissions=[OPEN_ACCESS]
            )
            set_admin(keys=_admin_meta_keys(), record=record, admin_meta=admin_meta)
            # constraint
            record.identification.constraints.append(
                Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
            )

            record.identification.aggregations.append(
                Aggregation(
                    identifier=Identifier(identifier="out_scope_superseded", namespace="data.bas.ac.uk"),
                    association_type=AggregationAssociationCode.REVISION_OF,
                )
            )

        return record

    @staticmethod
    def _get_records_in_scope(file_identifiers: set[str] | None = None) -> list[RecordRevision]:
        """Wrapper for _get_record_in_scope."""
        identifiers = {"out_scope_superseded", "out_scope_not_open", "in_scope"}
        return [TestWebsiteSearchExporter._get_record_in_scope(identifier=id_) for id_ in identifiers]

    def test_in_scope_items(self, fx_exporter_website_search: WebsiteSearchExporter):
        """Can select items in-scope for inclusion in website search."""
        fx_exporter_website_search._select_records = self._get_records_in_scope

        results = fx_exporter_website_search._in_scope_items
        assert len(results) == 1
        assert results[0].resource_id == "in_scope"

    def test_dumps(self, fx_exporter_website_search_sel: WebsiteSearchExporter):
        """Can dump search items."""
        result = fx_exporter_website_search_sel._dumps()
        items = json.loads(result)
        assert len(items) > 0

    def test_export(self, fx_exporter_website_search_sel: WebsiteSearchExporter):
        """Can export search items to a local file."""
        site_path = fx_exporter_website_search_sel._meta.export_path
        expected = site_path.joinpath("-", "public-website-search", "items.json")

        fx_exporter_website_search_sel.export()

        assert expected.exists()

    def test_publish(self, fx_exporter_website_search_sel: WebsiteSearchExporter, fx_s3_bucket_name: str):
        """Can publish site items to S3."""
        site_path = fx_exporter_website_search_sel._meta.export_path
        expected = "-/public-website-search/items.json"

        fx_exporter_website_search_sel.publish()

        output = fx_exporter_website_search_sel._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=fx_exporter_website_search_sel._s3_utils.calc_key(site_path.joinpath(expected)),
        )
        assert output["ResponseMetadata"]["HTTPStatusCode"] == 200
