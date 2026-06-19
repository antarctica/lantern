import logging

import pytest
from mypy_boto3_cloudfront import CloudFrontClient
from pytest_mock import MockerFixture

from lantern.exporters.cloudfront import CloudFrontExporter


class TestCloudFrontExporter:
    """Test AWS CloudFront exporter."""

    def test_init(self, fx_logger: logging.Logger, fx_cf_client: CloudFrontClient, fx_cf_distribution_id: str):
        """Can create a local exporter."""
        cf = CloudFrontExporter(logger=fx_logger, cloudfront=fx_cf_client, distribution="x")
        assert isinstance(cf, CloudFrontExporter)

        # check underlying mock CloudFront distribution exists
        distributions = cf._cf.list_distributions()["DistributionList"]
        assert len(distributions["Items"]) == 1
        assert distributions["Items"][0]["Status"] == "Deployed"
        # check ID is retrieved correctly
        assert fx_cf_distribution_id == distributions["Items"][0]["Id"]

    @pytest.mark.cov()
    def test_init_no_dist(self, fx_logger: logging.Logger, fx_cf_client: CloudFrontClient, fx_cf_distribution_id: str):
        """Cannot create a local exporter without a distribution ID."""
        with pytest.raises(ValueError, match=r"No distribution specified"):
            _ = CloudFrontExporter(logger=fx_logger, cloudfront=fx_cf_client, distribution="")

    @pytest.mark.parametrize(("keys", "batches"), [(1, 1), (200, 2)])
    def test_invalidate(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockerFixture,
        fx_cf_exporter: CloudFrontExporter,
        keys: int,
        batches: int,
    ):
        """Can invalidate keys in batches."""
        mocker.patch.object(fx_cf_exporter._cf, "get_waiter", return_value=mocker.MagicMock())
        fx_cf_exporter.invalidate(keys=["/x" for _ in range(keys)])
        assert f"Invalidating {keys} keys in {batches} 150-max key batches" in caplog.text
        assert f"Invalidating batch 1 of {batches}" in caplog.text

    def test_invalidate_no_keys(self, fx_cf_exporter: CloudFrontExporter):
        """Cannot invalidate too few keys."""
        with pytest.raises(ValueError, match=r"No keys to invalidate."):
            fx_cf_exporter.invalidate(keys=[])

    def test_export(self, fx_cf_exporter: CloudFrontExporter):
        """Cannot call unsupported method."""
        with pytest.raises(NotImplementedError):
            fx_cf_exporter.export(content=[])
