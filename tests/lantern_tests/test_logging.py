import logging

import pytest

from lantern.log import init as init_logging
from lantern.log import init_sentry


@pytest.mark.cov()
class TestLogging:
    """Test app logging."""

    def test_logging(self, caplog: pytest.LogCaptureFixture):
        """Can use app logger."""
        init_logging()
        init_sentry()
        logger = logging.getLogger("app")
        logger.setLevel(logging.DEBUG)

        expected = "x"
        logger.debug(expected)
        assert expected in caplog.text
