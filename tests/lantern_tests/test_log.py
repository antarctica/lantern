import logging

import pytest

from lantern.log import init as init_logging
from lantern.log import init_sentry


@pytest.mark.cov()
class TestLogging:
    """Test app logging."""

    def test_logging(self, caplog: pytest.LogCaptureFixture):
        """Can use app logger."""
        warn = "a"
        debug = "b"
        init_logging(logging.WARNING)
        logger = logging.getLogger("app")
        logger.warning(warn)
        logger.debug(debug)
        assert warn in caplog.text
        assert debug not in caplog.text

        warn2 = "c"
        debug2 = "d"
        init_logging(logging.DEBUG)
        logger2 = logging.getLogger("app")
        logger2.warning(warn2)
        logger2.debug(debug2)
        assert warn2 in caplog.text
        assert debug2 in caplog.text

        # ensure app logger config does not affect other loggers
        debug_other = "x"
        logger_other = logging.getLogger(debug_other)
        logger_other.debug(debug_other)
        assert debug_other not in caplog.text

    @pytest.mark.cov()
    def test_sentry(self):
        """Can initialize Sentry SDK."""
        init_sentry()
