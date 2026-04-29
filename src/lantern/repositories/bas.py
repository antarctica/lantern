import logging
import re
from collections.abc import Collection
from functools import cached_property
from typing import Any
from urllib.parse import urlparse

from gitlab import Gitlab, GitlabGetError
from gitlab.v4.objects import Project as GitlabProject
from gitlab.v4.objects import ProjectIssue as GitlabIssue
from gitlab.v4.objects import ProjectMergeRequest as GitlabMergeRequest
from pathvalidate import sanitize_filepath

from lantern.config import Config
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.repository import GitUpsertContext, GitUpsertResults
from lantern.repositories.base import RepositoryBase
from lantern.stores.gitlab import GitLabSource, GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore


class ProtectedGitBranchError(Exception):
    """Raised when trying to commit directly to a protected branch in a Git like store."""

    pass


class MergeRequestNotFoundError(Exception):
    """Raised when trying to get a merge request from a GitLab project that doesn't exist."""

    pass


class IssueNotFoundError(Exception):
    """Raised when trying to get an issue from a GitLab project that doesn't exist."""

    pass


class BasRepository(RepositoryBase):
    """
    Gitlab based repository for the BAS Data Catalogue.

    Wrapper around GitLab stores plus partial support for Merge Requests and issues for publishing workflows.
    """

    def __init__(self, logger: logging.Logger, config: Config) -> None:
        super().__init__(logger)
        self._config = config

    @cached_property
    def _gitlab_client(self) -> Gitlab:
        """
        GitLab client.

        For instance containing the record store project/repo.
        """
        return Gitlab(url=self._config.STORE_GITLAB_ENDPOINT, private_token=self._config.STORE_GITLAB_TOKEN)

    @cached_property
    def _gitlab_project(self) -> GitlabProject:
        """GitLab project acting as record store."""
        return self._gitlab_client.projects.get(self._config.STORE_GITLAB_PROJECT_ID)

    @cached_property
    def gitlab_project_url(self) -> str:
        """URL to GitLab project acting as record store."""
        return self._gitlab_project.web_url

    @property
    def gitlab_default_branch(self) -> str:
        """Default branch for GitLab store project/repo."""
        return self._config.STORE_GITLAB_DEFAULT_BRANCH

    def _get_gitlab_project_by_url(self, url: str) -> GitlabProject:
        """
        Initialise a GitLab project from a URL.

        Intended for getting non-default projects. Uses the same GitLab endpoint/instance and access token. Therefore,
        ensure this credential is granted suitable permissions to the target project (minimum reporter).
        """
        path = urlparse(url).path
        # split off any GitLab UI suffix (/-/merge_requests/..., /-/issues/..., etc.)
        project_path = path.split("/-/", 1)[0].strip("/")
        self._logger.debug(project_path)
        if not project_path:
            msg = f"Invalid GitLab project URL: {url}"
            raise ValueError(msg) from None

        try:
            return self._gitlab_client.projects.get(project_path)
        except GitlabGetError as e:
            if e.response_code == 404:
                msg = f"Project '{project_path}' not found - check token has access."
                raise ValueError(msg) from e
            raise

    def _make_gitlab_store(
        self, branch: str | None = None, cached: bool = False, frozen: bool = False
    ) -> GitLabStore | GitLabCachedStore:
        """
        Initialise an optionally cached/frozen GitLab store, with selected or default branch.

        Generated store is not cached by default to allow switching between branches efficiently.
        Where frozen, the store's cache is proactively refreshed once to ensure present and current, then frozen.
        """
        if not cached and frozen:
            msg = "Cannot create a frozen GitLab store without caching."
            raise ValueError(msg) from None

        source = GitLabSource(
            endpoint=self._config.STORE_GITLAB_ENDPOINT,
            project=self._config.STORE_GITLAB_PROJECT_ID,
            ref=branch or self._config.STORE_GITLAB_DEFAULT_BRANCH,
        )

        store = GitLabStore(logger=self._logger, source=source, access_token=self._config.STORE_GITLAB_TOKEN)
        if not cached:
            return store

        cache_path = self._config.STORE_GITLAB_CACHE_PATH / sanitize_filepath(source.ref)
        cached_store = GitLabCachedStore.from_gitlab_store(
            store=store, parallel_jobs=self._config.PARALLEL_JOBS, cache_dir=cache_path
        )
        cached_store.freeze()
        return cached_store

    @staticmethod
    def _get_gitlab_merge_id_by_url(url: str) -> int:
        """Get GitLab merge request identifier from a URL."""
        match = re.search(r"/-/merge_requests/(\d+)(?:/|$)", urlparse(url).path or "")
        if not match:
            msg = f"Invalid GitLab merge request URL: {url}"
            raise ValueError(msg) from None
        return int(match.group(1))

    @staticmethod
    def _get_gitlab_issue_id_by_url(url: str) -> int:
        """Get GitLab issue identifier from a URL."""
        match = re.search(r"/-/issues/(\d+)(?:/|$)", urlparse(url).path or "")
        if not match:
            msg = f"Invalid GitLab issue URL: {url}"
            raise ValueError(msg) from None
        return int(match.group(1))

    def select_merge_requests(self, state: str = "opened", branch: str | None = None) -> list[GitlabMergeRequest]:
        """
        Return some or all GitLab merge requests for default GitLab project.

        Filtered to open requests by default, optionally filtered by a source branch.
        """
        return self._gitlab_project.mergerequests.list(state=state, source_branch=branch)

    def select_merge_request(self, url: str) -> GitlabMergeRequest:
        """
        Return a specific merge request from the default GitLab project.

        Or raise a `MergeRequestNotFoundError` exception.
        """
        mr_id = self._get_gitlab_merge_id_by_url(url)
        try:
            return self._gitlab_project.mergerequests.get(mr_id)
        except GitlabGetError:
            msg = f"Could not get merge request for: {url}"
            raise MergeRequestNotFoundError(msg) from None

    def create_merge_request(
        self, source_branch: str, target_branch: str, title: str, description: str
    ) -> GitlabMergeRequest:
        """Create a merge request in the default GitLab project."""
        return self._gitlab_project.mergerequests.create(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
            }
        )

    def select_issue(self, url: str) -> GitlabIssue:
        """Return a specific issue from a GitLab project specified by URL or raise a `IssueNotFoundError` exception."""
        project = self._get_gitlab_project_by_url(url)
        issue_id = self._get_gitlab_issue_id_by_url(url)
        try:
            return project.issues.get(issue_id)
        except GitlabGetError:
            msg = f"Could not get issue for: {url}"
            raise IssueNotFoundError(msg) from None

    def select(
        self, file_identifiers: set[str] | None = None, branch: str | None = None, cached: bool = True
    ) -> list[RecordRevision]:
        """
        Return some or all records.

        Defaults to all records in the default branch of a cached store.

        Raises a `RecordsNotFoundError` exception if any selected records are not found.

        Proxy to a cached by default GitLab store. If cached, store is automatically frozen after being refreshed.
        """
        store = self._make_gitlab_store(branch=branch, cached=cached, frozen=bool(cached))
        return store.select(file_identifiers)

    def select_one(self, file_identifier: str, branch: str | None = None, cached: bool = True) -> RecordRevision:
        """
        Return a specific record or raise a `RecordNotFoundError` exception.

        Defaults to the default branch of a cached store.

        Where this method is called frequently, consider set `cached` to `True` for better performance.

        Proxy to a cached by default GitLab store. If cached, store is automatically frozen after being refreshed.
        """
        store = self._make_gitlab_store(branch=branch, cached=cached, frozen=bool(cached))
        return store.select_one(file_identifier)

    def upsert(self, records: Collection[Record], context: GitUpsertContext, **kwargs: Any) -> GitUpsertResults:
        """
        Persist new or existing records.

        Proxy to GitLab store.
        """
        default_branch = self._config.STORE_GITLAB_DEFAULT_BRANCH
        if context.branch == default_branch:
            # Avoid rejection from branch protection rules.
            msg = f"Cannot commit to default branch ('{default_branch}')."
            raise ProtectedGitBranchError(msg) from None

        store = self._make_gitlab_store(branch=context.branch)
        results = store.push(
            records=records,
            title=context.title,
            message=context.message,
            author=(context.author_name, context.author_email),
        )
        return GitUpsertResults(
            branch=results.branch,
            commit=results.commit,
            new_identifiers=results.new_identifiers,
            updated_identifiers=results.updated_identifiers,
        )
