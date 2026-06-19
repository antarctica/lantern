import logging
from collections.abc import Collection
from uuid import uuid4

from mypy_boto3_cloudfront import CloudFrontClient
from mypy_boto3_cloudfront.type_defs import InvalidationBatchTypeDef

from lantern.exporters.base import ExporterBase
from lantern.models.site import SiteContent


class CloudFrontExporter(ExporterBase):
    """(AWS) CloudFront exporter (invalidator)."""

    def __init__(self, logger: logging.Logger, cloudfront: CloudFrontClient, distribution: str) -> None:
        super().__init__(logger=logger, name="S3")
        self._cf = cloudfront
        self._distribution = distribution

        if not self._distribution:
            msg = "No distribution specified"
            raise ValueError(msg) from None

    def _invalidate_keys(self, keys: list[str]) -> None:
        """Create and execute CloudFront invalidation for selected keys."""
        caller_ref = str(uuid4())
        self._logger.info(f"Creating CloudFront invalidation for distribution {self._distribution}")
        self._logger.debug(keys)

        job: InvalidationBatchTypeDef = {"CallerReference": caller_ref, "Paths": {"Quantity": len(keys), "Items": keys}}
        response = self._cf.create_invalidation(DistributionId=self._distribution, InvalidationBatch=job)
        invalidation_id = response["Invalidation"]["Id"]
        self._logger.info(f"Invalidation created: {invalidation_id}")

        waiter = self._cf.get_waiter("invalidation_completed")
        self._logger.info("Waiting for invalidation to complete ...")
        waiter.wait(
            DistributionId=self._distribution, Id=invalidation_id, WaiterConfig={"Delay": 10, "MaxAttempts": 60}
        )
        self._logger.info("Invalidation completed.")

    def invalidate(self, keys: list[str]) -> None:
        """
        Invalidate specified keys in distribution.

        Groups keys into batches of 150 to comply with AWS quotas.
        """
        if not keys:
            msg = "No keys to invalidate."
            raise ValueError(msg) from None

        batches: list[list[str]] = [keys[i : i + 150] for i in range(0, len(keys), 150)]
        batch_count = len(batches)
        self._logger.info(f"Invalidating {len(keys)} keys in {batch_count} 150-max key batches")
        for i, batch in enumerate(batches):
            self._logger.info(f"Invalidating batch {i + 1} of {batch_count}")
            self._invalidate_keys(batch)

    def export(self, content: Collection[SiteContent]) -> None:
        """Not applicable for CloudFront."""
        raise NotImplementedError() from None
