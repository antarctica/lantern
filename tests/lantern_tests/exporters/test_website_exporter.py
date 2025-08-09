import json
import logging
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock

from bs4 import BeautifulSoup
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.exporters.website import WebsiteSearchExporter
from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation, Constraint
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.models.item.website.search import ItemWebsiteSearch


class TestWebsiteSearchExporter:
    """Test public website search exporter."""

    def test_init(self, mocker: MockerFixture, fx_logger: logging.Logger):
        """Can create an Exporter."""
        with TemporaryDirectory() as tmp_path:
            output_path = Path(tmp_path)
        s3_client = mocker.MagicMock()
        mock_config = mocker.Mock()
        type(mock_config).EXPORT_PATH = PropertyMock(return_value=output_path)

        exporter = WebsiteSearchExporter(config=mock_config, s3=s3_client, logger=fx_logger)

        assert isinstance(exporter, WebsiteSearchExporter)
        assert exporter.name == "Public Website search results"
        assert len(exporter._records) == 0

    def test_loads(self, fx_exporter_website_search: WebsiteSearchExporter, fx_record_minimal_item: Record):
        """Can load records."""
        records = [fx_record_minimal_item]
        fx_exporter_website_search.loads(records=records)
        assert len(fx_exporter_website_search._records) == len(records)

    def test_get_superseded_records(
        self, fx_exporter_website_search: WebsiteSearchExporter, fx_record_minimal_item: Record
    ):
        """Can determine superseded records."""
        successor = deepcopy(fx_record_minimal_item)
        successor.file_identifier = "y"
        successor.identification.aggregations.append(
            Aggregation(
                identifier=Identifier(identifier=fx_record_minimal_item.file_identifier, namespace="data.bas.ac.uk"),
                association_type=AggregationAssociationCode.REVISION_OF,
            )
        )

        results = fx_exporter_website_search._get_superseded_records(records=[fx_record_minimal_item, successor])
        assert results == [fx_record_minimal_item.file_identifier]

    def test_filter_items(
        self, fx_config: Config, fx_exporter_website_search: WebsiteSearchExporter, fx_record_minimal_item: Record
    ):
        """Can filter in-scope items."""
        out_scope_superseded = deepcopy(fx_record_minimal_item)

        out_scope_not_open = deepcopy(fx_record_minimal_item)
        out_scope_not_open.file_identifier = "y"

        in_scope = deepcopy(fx_record_minimal_item)
        in_scope.file_identifier = "z"
        in_scope.identification.constraints.append(
            Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED)
        )
        in_scope.identification.aggregations.append(
            Aggregation(
                identifier=Identifier(identifier=out_scope_superseded.file_identifier, namespace="data.bas.ac.uk"),
                association_type=AggregationAssociationCode.REVISION_OF,
            )
        )

        items = [
            ItemWebsiteSearch(record=record, source=fx_config.NAME, base_url="x")
            for record in [out_scope_superseded, out_scope_not_open, in_scope]
        ]
        results = fx_exporter_website_search._filter_items(items=items)
        assert len(results) == 1
        assert results[0].resource_id == in_scope.file_identifier

    def test_dumps(self, fx_exporter_website_search_pop: WebsiteSearchExporter):
        """Can dump search items."""
        result = fx_exporter_website_search_pop._dumps()
        items = json.loads(result)
        assert len(items) > 0

    def test_dumps_mockup(self, fx_exporter_website_search_pop: WebsiteSearchExporter):
        """Can dump mockup web page."""
        html = BeautifulSoup(fx_exporter_website_search_pop._dumps_mockup(), parser="html.parser", features="lxml")
        assert "html" in str(html)

    def test_export(self, fx_exporter_website_search_pop: WebsiteSearchExporter):
        """Can export search items a local file."""
        site_path = fx_exporter_website_search_pop._config.EXPORT_PATH
        expected = [
            site_path.joinpath("-", "public-website-search", "items.json"),
            site_path.joinpath("-", "public-website-search", "mockup.html"),
        ]

        fx_exporter_website_search_pop.export()

        result = list(fx_exporter_website_search_pop._config.EXPORT_PATH.glob("**/*.*"))
        for path in result:
            assert path in expected

    def test_publish(self, fx_exporter_website_search_pop: WebsiteSearchExporter, fx_s3_bucket_name: str):
        """Can publish site index to S3."""
        site_path = fx_exporter_website_search_pop._config.EXPORT_PATH
        keys = ["-/public-website-search/items.json", "-/public-website-search/mockup.html"]

        fx_exporter_website_search_pop.publish()

        for key in keys:
            output = fx_exporter_website_search_pop._s3_utils._s3.get_object(
                Bucket=fx_s3_bucket_name,
                Key=fx_exporter_website_search_pop._s3_utils.calc_key(site_path.joinpath(key)),
            )
            assert output["ResponseMetadata"]["HTTPStatusCode"] == 200
