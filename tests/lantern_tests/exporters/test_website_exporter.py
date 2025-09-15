import json
import logging
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from pytest_mock import MockerFixture

from lantern.exporters.website import WebsiteSearchExporter
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation, Constraint
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.models.record.revision import RecordRevision
from tests.conftest import _get_record_open, _revision_config_min


class TestWebsiteSearchExporter:
    """Test public website search exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)

        exporter = WebsiteSearchExporter(
            config=mock_config, s3=s3_client, logger=fx_logger, get_record=_get_record_open
        )

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

    def test_in_scope_items(self, fx_exporter_website_search: WebsiteSearchExporter):
        """Can select items in-scope for inclusion in website search."""
        fx_exporter_website_search._get_record = self._get_record_in_scope
        fx_exporter_website_search.selected_identifiers = {"out_scope_superseded", "out_scope_not_open", "in_scope"}

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
        site_path = fx_exporter_website_search_sel._config.EXPORT_PATH
        expected = site_path.joinpath("-", "public-website-search", "items.json")

        fx_exporter_website_search_sel.export()

        assert expected.exists()

    def test_publish(self, fx_exporter_website_search_sel: WebsiteSearchExporter, fx_s3_bucket_name: str):
        """Can publish site items to S3."""
        site_path = fx_exporter_website_search_sel._config.EXPORT_PATH
        expected = "-/public-website-search/items.json"

        fx_exporter_website_search_sel.publish()

        output = fx_exporter_website_search_sel._s3_utils._s3.get_object(
            Bucket=fx_s3_bucket_name,
            Key=fx_exporter_website_search_sel._s3_utils.calc_key(site_path.joinpath(expected)),
        )
        assert output["ResponseMetadata"]["HTTPStatusCode"] == 200
