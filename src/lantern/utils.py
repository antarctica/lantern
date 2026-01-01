import logging

from boto3 import client as S3Client  # noqa: N812
from mypy_boto3_s3 import S3Client as S3ClientT

from lantern.config import Config
from lantern.stores.gitlab import GitLabSource
from lantern.stores.gitlab_cache import GitLabCachedStore


def init_gitlab_store(
    logger: logging.Logger, config: Config, branch: str | None = None, frozen: bool = False
) -> GitLabCachedStore:
    """Initialise a GitLab store from app Config."""
    branch_ = branch or config.STORE_GITLAB_BRANCH
    source = GitLabSource(endpoint=config.STORE_GITLAB_ENDPOINT, project=config.STORE_GITLAB_PROJECT_ID, ref=branch_)

    return GitLabCachedStore(
        logger=logger,
        source=source,
        access_token=config.STORE_GITLAB_TOKEN,
        parallel_jobs=config.PARALLEL_JOBS,
        cache_dir=config.STORE_GITLAB_CACHE_PATH,
        frozen=frozen,
    )


def init_s3_client(config: Config) -> S3ClientT:
    """Initialise an S3 client from app Config."""
    return S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
