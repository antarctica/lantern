import logging
from importlib.metadata import version

import sentry_sdk


def init(logging_level: int) -> None:
    """Initialize application logging."""
    # noinspection SpellCheckingInspection
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("app")
    logger.setLevel(logging_level)


def init_sentry() -> None:
    """Initialise Sentry SDK, if enabled."""
    # can't import Config normally due to circular imports
    from lantern.config import Config

    config = Config()

    dsn = config.SENTRY_DSN
    disabled = not config.ENABLE_FEATURE_SENTRY
    if disabled:  # pragma: no branch
        dsn = ""  # empty DSN disables Sentry

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,  # 10%
        profiles_sample_rate=0.1,  # 10%
        release=version("lantern"),
        environment=config.SENTRY_ENVIRONMENT,
    )
