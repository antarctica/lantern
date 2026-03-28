import functools
import logging
import time
from collections.abc import Callable
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import ALIAS_NAMESPACE
from lantern.models.record.record import Record
from lantern.stores.gitlab import GitLabSource, GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore


def init_gitlab_store(
    logger: logging.Logger,
    config: Config,
    branch: str | None = None,
    path: Path | None = None,
    cached: bool = False,
    frozen: bool = False,
) -> GitLabStore | GitLabCachedStore:
    """
    Initialise a GitLab store from app Config.

    Store is not cached by default to allow switching between branches efficiently.
    Store is not frozen by default to allow fetching changes before processing.
    """
    if not cached and frozen:
        msg = "Cannot create a frozen GitLab store without caching."
        raise ValueError(msg) from None

    branch_ = branch or config.STORE_GITLAB_BRANCH
    source = GitLabSource(endpoint=config.STORE_GITLAB_ENDPOINT, project=config.STORE_GITLAB_PROJECT_ID, ref=branch_)

    if not cached:
        return GitLabStore(logger=logger, source=source, access_token=config.STORE_GITLAB_TOKEN)

    return GitLabCachedStore(
        logger=logger,
        source=source,
        access_token=config.STORE_GITLAB_TOKEN,
        parallel_jobs=config.PARALLEL_JOBS,
        cache_dir=path if path else config.STORE_GITLAB_CACHE_PATH,
        frozen=frozen,
    )


def get_record_aliases(record: Record) -> list[Identifier]:
    """Get optional aliases for record as relative file paths / S3 keys."""
    return record.identification.identifiers.filter(namespace=ALIAS_NAMESPACE)


def get_jinja_env() -> Environment:
    """Get Jinja environment with app templates."""
    _loader = PackageLoader("lantern", "resources/templates")
    return Environment(loader=_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)


def prettify_html(html: str) -> str:
    """
    Prettify HTML string, removing any empty lines.

    Without very careful whitespace control, Jinja templates quickly look messy where conditionals and other logic are
    used. Whilst this doesn't strictly matter, it is nicer if output looks well-formed by removing empty lines.

    This gives a 'flat' structure when viewed as source. Browser dev tools will reformat this into a tree structure.
    The `prettify()` method is not used as it splits all elements onto new lines, which causes layout/spacing bugs.
    """
    return str(BeautifulSoup(html, parser="html.parser", features="lxml"))


def time_task(label: str) -> Callable:
    """
    Time a task and log duration.

    Uses a temporary app logger.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            start = time.monotonic()
            result = func(*args, **kwargs)
            logger = logging.getLogger("app")
            logger.setLevel(logging.INFO)
            logger.info(f"{label} took {round(time.monotonic() - start)} seconds")
            return result

        return wrapper

    return decorator
