import logging
from unittest.mock import MagicMock

import pytest
from gitlab import GitlabGetError
from gitlab.client import Gitlab
from gitlab.v4.objects import Project as GitlabProject
from gitlab.v4.objects import ProjectIssue as GitlabIssue
from gitlab.v4.objects import ProjectMergeRequest as GitlabMergeRequest
from pytest_mock import MockerFixture

from lantern.config import Config
from lantern.models.record.record import Record
from lantern.models.repository import GitUpsertContext, GitUpsertResults
from lantern.repositories.bas import (
    BasRepository,
    IssueNotFoundError,
    MergeRequestNotFoundError,
    ProtectedGitBranchError,
)
from lantern.stores.gitlab import CommitResults, GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore


class TestBasRepository:
    """Test BAS data catalogue repository."""

    def test_init(self, fx_logger: logging.Logger, fx_config: Config):
        """Can create a BAS repository instance."""
        repo = BasRepository(logger=fx_logger, config=fx_config)
        assert isinstance(repo, BasRepository)

    def test_gitlab_client(self, fx_bas_repo: BasRepository):
        """Can get GitLab client."""
        client = fx_bas_repo._gitlab_client
        assert isinstance(client, Gitlab)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_gitlab_project(self, fx_bas_repo: BasRepository):
        """Can get GitLab project for records store project/repo."""
        project = fx_bas_repo._gitlab_project
        assert isinstance(project, GitlabProject)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_gitlab_project_url(self, fx_bas_repo: BasRepository):
        """Can get GitLab project for records store project/repo."""
        url = fx_bas_repo.gitlab_project_url
        assert isinstance(url, str)

    def test_gitlab_default_branch(self, fx_bas_repo: BasRepository, fx_config: Config):
        """Can get GitLab default branch for records store project/repo."""
        branch = fx_bas_repo.gitlab_default_branch
        assert branch == fx_config.STORE_GITLAB_DEFAULT_BRANCH

    @pytest.mark.parametrize(
        "url",
        [
            "https://gitlab.example.com/group/project",
            "https://gitlab.example.com/group/project/-/merge_requests/123",
            "https://gitlab.example.com/group/project/-/issues/123?x=x",
        ],
    )
    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_gitlab_project_by_url(self, fx_bas_repo: BasRepository, url: str):
        """Can get GitLab project by URL."""
        project = fx_bas_repo._get_gitlab_project_by_url(url)
        assert isinstance(project, GitlabProject)

    def test_get_gitlab_project_by_url_invalid(self, fx_bas_repo: BasRepository):
        """Cannot get GitLab project by URL with an invalid URL."""
        url = "/-/x"
        with pytest.raises(ValueError, match=rf"Invalid GitLab project URL: {url}"):
            fx_bas_repo._get_gitlab_project_by_url(url)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_get_gitlab_project_by_url_unknown(self, fx_bas_repo: BasRepository):
        """Cannot get an unknown (or unavailable) GitLab project by URL."""
        project_path = "invalid/project"
        url = f"https://gitlab.example.com/{project_path}"
        with pytest.raises(ValueError, match=rf"Project '{project_path}' not found - check token has access."):
            fx_bas_repo._get_gitlab_project_by_url(url)

    @pytest.mark.cov
    def test_get_gitlab_project_by_url_error(self, mocker: MockerFixture, fx_bas_repo: BasRepository):
        """Cannot get a GitLab project by URL when an error occurs."""
        mocker.patch.object(fx_bas_repo, "_gitlab_client").projects.get.side_effect = GitlabGetError(response_code=500)

        with pytest.raises(GitlabGetError):
            fx_bas_repo._get_gitlab_project_by_url("https://gitlab.example.com/invalid/project")

    @pytest.mark.parametrize("branch", [None, "x"])
    @pytest.mark.parametrize("cached", [False, True])
    def test_make_gitlab_store(
        self, mocker: MockerFixture, fx_bas_repo: BasRepository, fx_config: Config, branch: str | None, cached: bool
    ):
        """Can get GitLab store for records store project/repo."""
        expected_branch = branch if branch else fx_config.STORE_GITLAB_DEFAULT_BRANCH

        real_from_gitlab_store = GitLabCachedStore.from_gitlab_store

        def _from_gitlab_store(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            """Override creating a cached store to mock the freeze method, to avoid fetching from the repository."""
            instance = real_from_gitlab_store(*args, **kwargs)
            mocker.patch.object(instance, "freeze")
            return instance

        mocker.patch(
            "lantern.repositories.bas.GitLabCachedStore.from_gitlab_store",
            side_effect=_from_gitlab_store,
        )

        store = fx_bas_repo._make_gitlab_store(branch=branch, cached=cached)

        assert isinstance(store, GitLabStore)
        assert store._source.ref == expected_branch

        if cached:
            assert isinstance(store, GitLabCachedStore)
            assert store._cache._path.name == expected_branch

    @pytest.mark.cov()
    def test_make_gitlab_store_frozen_conflict(self, fx_bas_repo: BasRepository):
        """Cannot get frozen GitLab Store without caching."""
        with pytest.raises(ValueError, match=r"Cannot create a frozen GitLab store without caching."):
            fx_bas_repo._make_gitlab_store(cached=False, frozen=True)

    def test_get_gitlab_mr_id_by_url(self, fx_bas_repo: BasRepository):
        """Can get GitLab merge request identifier from a URL."""
        merge = 123
        url = f"https://gitlab.example.com/group/project/-/merge_requests/{merge}"
        mr_id = fx_bas_repo._get_gitlab_merge_id_by_url(url)
        assert mr_id == merge

    def test_get_gitlab_mr_id_by_url_invalid(self, fx_bas_repo: BasRepository):
        """Cannot get GitLab merge request identifier from an invalid URL."""
        url = "x"
        with pytest.raises(ValueError, match=rf"Invalid GitLab merge request URL: {url}"):
            fx_bas_repo._get_gitlab_merge_id_by_url(url)

    def test_get_gitlab_issue_id_by_url(self, fx_bas_repo: BasRepository):
        """Can get GitLab issue identifier from a URL."""
        issue = 123
        url = f"https://gitlab.example.com/group/project/-/issues/{issue}"
        issue_id = fx_bas_repo._get_gitlab_issue_id_by_url(url)
        assert issue_id == issue

    def test_get_gitlab_issue_id_by_url_invalid(self, fx_bas_repo: BasRepository):
        """Cannot get GitLab issue identifier from an invalid URL."""
        url = "x"
        with pytest.raises(ValueError, match=rf"Invalid GitLab issue URL: {url}"):
            fx_bas_repo._get_gitlab_issue_id_by_url(url)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_select_merge_requests(self, fx_bas_repo: BasRepository):
        """Can get GitLab merge requests for records store project/repo."""
        merges = fx_bas_repo.select_merge_requests()
        assert len(merges) == 1
        assert isinstance(merges[0], GitlabMergeRequest)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_select_merge_request(self, fx_bas_repo: BasRepository):
        """Can get GitLab merge request by URL from records store project/repo."""
        url = "https://gitlab.example.com/group/project/-/merge_requests/123"
        merge = fx_bas_repo.select_merge_request(url=url)
        assert isinstance(merge, GitlabMergeRequest)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_select_merge_request_unknown(self, fx_bas_repo: BasRepository):
        """Cannot get an unknown (or unavailable) merge request from a GitLab project."""
        url = "https://gitlab.example.com/group/project/-/merge_requests/999"
        with pytest.raises(MergeRequestNotFoundError):
            fx_bas_repo.select_merge_request(url=url)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_create_merge_request(self, fx_bas_repo: BasRepository):
        """Cannot create a merge request within the records store project/repo."""
        merge = fx_bas_repo.create_merge_request(source_branch="y", target_branch="x", title="x", description="x")
        assert isinstance(merge, GitlabMergeRequest)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_select_issue(self, fx_bas_repo: BasRepository):
        """Can get GitLab merge request by URL from records store project/repo."""
        url = "https://gitlab.example.com/group/project/-/issues/123"
        merge = fx_bas_repo.select_issue(url=url)
        assert isinstance(merge, GitlabIssue)

    @pytest.mark.vcr
    @pytest.mark.block_network
    def test_select_issue_unknown(self, fx_bas_repo: BasRepository):
        """Cannot get an unknown (or unavailable) issue from a GitLab project."""
        url = "https://gitlab.example.com/group/project/-/issues/999"
        with pytest.raises(IssueNotFoundError):
            fx_bas_repo.select_issue(url=url)

    def test_select(self, fx_bas_repo_cached_store_pop: BasRepository):
        """Cannot select any/some records from records store project/repo."""
        records = fx_bas_repo_cached_store_pop.select()
        assert len(records) == 1

    def test_select_one(self, fx_bas_repo_cached_store_pop: BasRepository):
        """Cannot select a record from records store project/repo."""
        record = fx_bas_repo_cached_store_pop.select_one(file_identifier="a1b2c3")
        assert record is not None

    def test_upsert(self, mocker: MockerFixture, fx_bas_repo: BasRepository, fx_record_model_min: Record):
        """Can upsert a record in the records store project/repo."""
        branch = "x"
        commit = "abc123"
        file_id = "a1b2c3"

        mock_store = MagicMock(spec=GitLabStore)
        mock_store.push.return_value = CommitResults(
            branch=branch, commit=commit, changes={"create": [file_id], "update": []}, actions=[{"action": "create"}]
        )
        mocker.patch.object(fx_bas_repo, "_make_gitlab_store", return_value=mock_store)

        context = GitUpsertContext(title="x", message="x", author_name="x", author_email="x", branch=branch)
        expected = GitUpsertResults(branch=branch, commit=commit, new_identifiers=[file_id], updated_identifiers=[])

        results = fx_bas_repo.upsert(records=[fx_record_model_min], context=context)
        assert results == expected

    @pytest.mark.cov()
    def test_upsert_default_branch(self, fx_bas_repo: BasRepository, fx_config: Config, fx_record_model_min: Record):
        """Cannot upsert a record in the default branch of the records store project/repo."""
        context = GitUpsertContext(
            title="x", message="x", author_name="x", author_email="x", branch=fx_config.STORE_GITLAB_DEFAULT_BRANCH
        )
        with pytest.raises(ProtectedGitBranchError):
            fx_bas_repo.upsert(records=[fx_record_model_min], context=context)
