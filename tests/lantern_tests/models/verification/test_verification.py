from lantern.models.verification.enums import VerificationResult, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext


class TestVerificationJob:
    """Test verification job."""

    def test_init(self):
        """Can create a verification job with minimal properties."""
        context: VerificationContext = {
            "BASE_URL": "x",
            "SHAREPOINT_PROXY_ENDPOINT": "x",
        }
        job = VerificationJob(type=VerificationType.ITEM_PAGES, url="x", context=context)

        assert isinstance(job, VerificationJob)
        assert job.type == VerificationType.ITEM_PAGES
        assert job.url == "x"
        assert job.result == VerificationResult.PENDING
        assert isinstance(job.params, dict)
        assert isinstance(job.context, dict)
        assert isinstance(job.data, dict)
