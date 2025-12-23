import logging

from boto3 import client as S3Client  # noqa: N812
from mypy_boto3_s3 import S3Client as S3ClientT

from lantern.config import Config
from lantern.stores.gitlab import GitLabStore


def init_gitlab_store(logger: logging.Logger, config: Config, branch: str | None = None) -> GitLabStore:
    """Initialise a GitLab store from app Config."""
    branch_ = branch or config.STORE_GITLAB_BRANCH
    return GitLabStore(
        logger=logger,
        parallel_jobs=config.PARALLEL_JOBS,
        endpoint=config.STORE_GITLAB_ENDPOINT,
        access_token=config.STORE_GITLAB_TOKEN,
        project_id=config.STORE_GITLAB_PROJECT_ID,
        branch=branch_,
        cache_path=config.STORE_GITLAB_CACHE_PATH,
    )


def init_s3_client(config: Config) -> S3ClientT:
    """Initialise an S3 client from app Config."""
    return S3Client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_ID,
        aws_secret_access_key=config.AWS_ACCESS_SECRET,
        region_name="eu-west-1",
    )
