import logging
from pathlib import Path

from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tests.resources.admin_keys import test_keys
from tests.resources.catalogues.fake_catalogue import FakeCatalogue

from lantern.config import Config as ConfigBase
from lantern.log import init as init_logging


class Config(ConfigBase):
    """Config with test keys."""

    @property
    def ADMIN_METADATA_KEYS(self) -> AdministrationKeys:  # noqa: N802
        """Administration metadata keys."""
        return test_keys()


def main() -> None:
    """Entrypoint."""
    identifiers = set()
    path = Path("export")
    purge = False

    config = Config()
    init_logging(config.LOG_LEVEL)
    logger = logging.getLogger("app")
    logger.info("Initialising")

    cat = FakeCatalogue(logger=logger, config=config, base_path=path)

    if purge:
        cat.purge()
    cat.export(identifiers=identifiers)


if __name__ == "__main__":
    main()
