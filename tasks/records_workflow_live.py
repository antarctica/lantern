import logging
import re
import sys
from pathlib import Path

import inquirer
from mypy_boto3_s3 import S3Client
from tasks._config import ExtraConfig
from tasks._record_utils import confirm, init, init_store, ping_host, time_task
from tasks.records_workflow_testing import (
    OutputCommentItem,
    build,
    gitlab_project_issue_from_url,
    gitlab_project_mr_from_url,
    verify,
)

from lantern.config import Config
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.stores.gitlab import GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import get_jinja_env


class OutputCommentIssue:
    """Output comment for a GitLab issue."""

    def __init__(
        self, config: Config, store: GitLabStore, base_url: str, issue_url: str, identifiers: set[str]
    ) -> None:
        self._store = store
        self._base_url = base_url
        self._issue_url = issue_url
        self._identifiers = identifiers

        self._meta = ExportMeta.from_config_store(
            config=config, store=store, build_repo_ref=store.head_commit if store.head_commit else "-"
        )
        self._jinja = get_jinja_env()

    @property
    def _records(self) -> list[RecordRevision]:
        """Records from changeset."""
        return self._store.select(file_identifiers=self._identifiers)

    @property
    def _items(self) -> list[OutputCommentItem]:
        """Generated snippets for each record."""
        return [OutputCommentItem(meta=self._meta, base_url=self._base_url, record=record) for record in self._records]

    @property
    def _context(self) -> dict[str, str | list[str]]:
        """Data for Jinja template."""
        count = len(self._records)
        return {
            "count": str(count),
            "count_label": "records" if count != 1 else "record",
            "items": [item.render() for item in self._items],
        }

    @property
    def _template(self) -> str:
        """Jinja template for issue."""
        return """
Records published live:

{% for item in items %}
{{ item }}
{% endfor %}

See the [updating records](https://github.com/antarctica/lantern/blob/main/docs/usage.md#update-records) documentation for how to revise these items if needed in future.

_This comment was left automatically by the Lantern Experiment's [Interactive record publishing workflow](https://github.com/antarctica/lantern/blob/main/docs/usage.md#interactive-record-publishing-workflow). This comment was left by a bot user that does not monitor replies._
        """

    def render(self) -> str:
        """Render jinja template as comment body."""
        return self._jinja.from_string(self._template).render(**self._context)

    def post(self) -> None:
        """Post comment to GitLab issue."""
        issue = gitlab_project_issue_from_url(gitlab=self._store._client, issue_url=self._issue_url)
        issue.notes.create({"body": self.render()})


@time_task(label="Changeset")
def _changeset(logger: logging.Logger, config: Config, store: GitLabStore) -> tuple[GitLabStore, str, str]:
    """
    Select a changeset and check it is ready to be published live.

    Returns a GitLab store using the changeset branch and the related merge request / issue URLs.

    For convenience, open merge requests in the store project are offered as a suggestion for in-progress changesets.
    """
    merge_requests = store._project.mergerequests.list(state="opened")
    options = [(mr.title.replace("Records publishing changeset: ", ""), mr.iid) for mr in merge_requests]
    mr_id = inquirer.list_input(message="Changeset", choices=options)
    if not isinstance(mr_id, int):
        msg = "Merge request must be set for a changeset."
        raise TypeError(msg) from None
    mr = store._project.mergerequests.get(mr_id)
    logger.info(f"MR set to '{mr.web_url}'.")

    if mr.draft:
        msg = "Merge request is still a draft, aborting."
        raise ValueError(msg) from None
    if not mr.approvals.get().approved:
        msg = "Merge request has not been approved, aborting."
        raise ValueError(msg) from None

    # can't use `mr.related_issues()` as it was introduced in GL 17.1.
    issues = re.findall(r"https?://[^/]+/[^/\s]+/[^/\s]+/-/issues/\d+", mr.description or "")
    if len(issues) != 1:
        msg = "Only a single related issue is currently supported, aborting."
        raise ValueError(msg) from None
    issue_url = issues[0]
    logger.info(f"Related issue: '{issue_url}'.")

    branch = mr.source_branch
    logger.info(f"Using changeset branch: '{branch}'")
    store: GitLabCachedStore = init_store(logger=logger, config=config, branch=branch, cached=True)  # ty:ignore[invalid-assignment]

    return store, mr.web_url, issue_url


@time_task(label="Changeset")
def _merge_request(logger: logging.Logger, store: GitLabStore, merge_url: str) -> set[str]:
    """Merge a merge request for a changeset and return a list of identifiers for records it contained."""
    mr = gitlab_project_mr_from_url(gitlab=store._client, mr_url=merge_url)
    logger.info(f"MR set to '{mr.web_url}'.")

    ids = {Path(d["new_path"]).stem for diff_ in mr.diffs.list() for d in mr.diffs.get(diff_.id).diffs}
    logger.info(f"{len(ids)} records in changeset.")

    mr.merge(should_remove_source_branch=True)

    return ids


@time_task(label="Build")
def _build(
    logger: logging.Logger, config: ExtraConfig, store: GitLabCachedStore, s3: S3Client, identifiers: set[str]
) -> None:
    """Build items for committed records."""
    build(logger=logger, config=config, store=store, s3=s3, identifiers=identifiers)


@time_task(label="Verify")
def _verify(
    logger: logging.Logger, config: Config, store: GitLabStore, s3: S3Client, base_url: str, identifiers: set[str]
) -> None:
    """Verify items for committed records."""
    verify(logger=logger, config=config, store=store, s3=s3, base_url=base_url, identifiers=identifiers)


@time_task(label="Output")
def _output(
    logger: logging.Logger, config: Config, store: GitLabStore, base_url: str, issue_url: str, identifiers: set[str]
) -> None:
    """Add comments to GitLab issue."""
    issue_comment = OutputCommentIssue(
        config=config, store=store, base_url=base_url, issue_url=issue_url, identifiers=identifiers
    )
    print(issue_comment.render())
    confirm(logger, "Post comment above to GitLab issue?")
    issue_comment.post()
    logger.info(f"Comment posted to: {issue_url}")


@time_task(label="Workflow")
def main() -> None:
    """
    Entrypoint.

    This task initially uses a non-cached store to merge the changeset (into main), then a cached store for building.

    This workflow is known to be inefficient in terms of how changed records are parsed as identifiers from diffs, then
    later loaded from the store to allow output comments to be generated.
    """
    logger, config, store, s3 = init(cached_store=True)
    base_url = "https://data.bas.ac.uk"
    live_bucket = "lantern.data.bas.ac.uk"

    if live_bucket != config.AWS_S3_BUCKET:
        logger.error("No. Non-live bucket selected.")
        sys.exit(1)
    if config.TRUSTED_UPLOAD_HOST:
        logger.info("Checking connectivity to trusted upload host.")
        ping_host(config.TRUSTED_UPLOAD_HOST)
    if not config.STORE_GITLAB_CACHE_PATH.exists():
        logger.error("GitLab cache does not exist, build will fail. Run `task cache-init` first.")
        sys.exit(1)

    print("\nThis script is for publishing records previewed in the testing site to the live site.")
    print("It combines the 'build-' and 'verify-' records dev tasks with some workflow logic.")

    # select a changeset
    cs_store, merge_url, issue_url = _changeset(logger=logger, config=config, store=store)

    # merge changeset and get record identifiers
    identifiers = _merge_request(logger=logger, store=cs_store, merge_url=merge_url)

    # build and verify records
    _build(logger=logger, config=config, store=store, s3=s3, identifiers=identifiers)
    _verify(logger=logger, config=config, store=store, s3=s3, base_url=base_url, identifiers=identifiers)

    # generate output comments
    _output(logger=logger, config=config, store=store, base_url=base_url, issue_url=issue_url, identifiers=identifiers)


if __name__ == "__main__":
    main()
