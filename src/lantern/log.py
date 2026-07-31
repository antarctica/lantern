import logging
from importlib.metadata import version

import sentry_sdk


def init(logging_level: int) -> None:
    """Initialise application logging."""
    logging.basicConfig(
        level=logging_level, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()]
    )
    logging.getLogger("lantern").setLevel(logging_level)


def init_sentry() -> None:
    """Initialise Sentry SDK, if enabled."""
    from lantern.config import Config  # avoid circular imports  # noqa: PLC0415

    config = Config()
    sentry_sdk.init(
        dsn=config.SENTRY_DSN if config.ENABLE_FEATURE_SENTRY else "",
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        release=version("lantern"),
        environment=config.SENTRY_ENVIRONMENT,
    )
