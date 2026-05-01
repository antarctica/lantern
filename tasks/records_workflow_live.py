# Publish records to live site

import logging
import re
import shutil
import sys
from pathlib import Path
from textwrap import dedent

import inquirer
from pathvalidate import sanitize_filepath
from tasks._config import ExtraConfig
from tasks._shared import confirm, init, ping_host, time_task
from tasks.records_invalidate import get_record_invalidation_keys
from tasks.records_workflow_testing import OutputCommentItem
from tasks.records_workflow_testing import _export as export
from tasks.records_workflow_testing import _verify as verify
from tasks.site_invalidate import get_cf_distribution_id, invalidate_keys

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta, SiteEnvironment
from lantern.utils import get_jinja_env


class OutputCommentIssue:
    """Output comment for a GitLab issue."""

    def __init__(
        self,
        config: Config,
        cat: BasCatalogue,
        env: SiteEnvironment,
        branch: str,
        issue_url: str,
        identifiers: set[str],
    ) -> None:
        self._cat = cat
        self._branch = branch
        self._issue_url = issue_url
        self._identifiers = identifiers

        self._meta = ExportMeta.from_config(config=config, env=env)
        self._jinja = get_jinja_env()

    @property
    def _records(self) -> list[RecordRevision]:
        """Records from changeset."""
        return self._cat.repo.select(branch=self._branch, file_identifiers=self._identifiers)

    @property
    def _items(self) -> list[OutputCommentItem]:
        """Generated snippets for each record."""
        return [OutputCommentItem(meta=self._meta, record=record) for record in self._records]

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
        return dedent("""\
            Hello,

            Some catalogue records related to this issue have been published live:

            {% for item in items %}
            {{ item }}

            {% endfor %}

            See the [updating records](https://github.com/antarctica/lantern/blob/main/docs/usage.md#update-records) documentation for how to revise these items in the future.

            _This comment was left automatically by the Lantern Experiment's [Interactive record publishing workflow](https://github.com/antarctica/lantern/blob/main/docs/usage.md#interactive-record-publishing-workflow)._

            _This comment was left by a bot user that does not monitor replies. Contact @/felnne for support._
         """)

    def render(self) -> str:
        """Render jinja template as comment body."""
        return self._jinja.from_string(self._template).render(**self._context)

    def post(self) -> None:
        """Post comment to GitLab issue."""
        issue = self._cat.repo.select_issue(self._issue_url)
        issue.notes.create({"body": self.render()})


@time_task(label="Changeset")
def _changeset(logger: logging.Logger, cat: BasCatalogue) -> tuple[str, str, str]:
    """
    Select a changeset and check it is ready to be published live.

    For convenience, open merge requests in the store project are offered as a suggestion for in-progress changesets.

    Returns selected merge request, its branch and associated issue.
    """
    merge_requests = cat.repo.select_merge_requests(state="opened")
    options = [(mr.title.replace("Records publishing changeset: ", ""), mr.web_url) for mr in merge_requests]
    mr_url = inquirer.list_input(message="Changeset", choices=options)
    mr = cat.repo.select_merge_request(url=mr_url)
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
    logger.info(f"Changeset branch: '{branch}'.")

    return branch, mr.web_url, issue_url


@time_task(label="Changeset")
def _merge_request(logger: logging.Logger, cat: BasCatalogue, merge_url: str) -> set[str]:
    """Merge a merge request for a changeset and return a list of identifiers for records it contained."""
    mr = cat.repo.select_merge_request(url=merge_url)
    logger.info(f"MR set to '{mr.web_url}'.")
    mr.merge(should_remove_source_branch=True)

    ids = {Path(d["new_path"]).stem for diff_ in mr.diffs.list() for d in mr.diffs.get(diff_.id).diffs}
    logger.info(f"{len(ids)} records in changeset.")
    return ids


@time_task(label="Export")
def _export(
    logger: logging.Logger, config: ExtraConfig, cat: BasCatalogue, env: SiteEnvironment, identifiers: set[str]
) -> None:
    """
    Export items for committed records.

    Records are invalidated in case they have been previously published and currently cached.
    """
    cf_id = get_cf_distribution_id(iac_cwd=Path("./resources/envs"), cf_id="site_cf_id")
    export(cat=cat, env=env, branch=cat.repo.gitlab_default_branch, identifiers=identifiers)
    invalidate_keys(logger=logger, config=config, distribution_id=cf_id, keys=get_record_invalidation_keys(identifiers))


@time_task(label="Verify")
def _verify(cat: BasCatalogue, env: SiteEnvironment, identifiers: set[str], checks_base_path: Path) -> Path:
    """Verify items for committed records."""
    return verify(
        cat=cat,
        env=env,
        branch=cat.repo.gitlab_default_branch,
        identifiers=identifiers,
        checks_base_path=checks_base_path,
    )


@time_task(label="Output")
def _output(
    logger: logging.Logger,
    cat: BasCatalogue,
    config: Config,
    env: SiteEnvironment,
    branch: str,
    issue_url: str,
    identifiers: set[str],
) -> None:
    """Add comments to GitLab issue."""
    issue_comment = OutputCommentIssue(
        config=config, cat=cat, env=env, branch=branch, issue_url=issue_url, identifiers=identifiers
    )
    print(issue_comment.render())
    confirm(logger, f"Post comment above to {issue_url}?")
    issue_comment.post()


@time_task(label="Clean")
def _clean(logger: logging.Logger, config: Config, branch: str) -> None:
    """Clean up changeset cache."""
    cache_path = config.STORE_GITLAB_CACHE_PATH / sanitize_filepath(branch)
    if cache_path.exists():
        logger.info(f"Cleaning up cache for {branch} at {cache_path.resolve()} ...")
        shutil.rmtree(cache_path)
    # remove any empty directories between config.STORE_GITLAB_CACHE_PATH and cache_path
    for parent in cache_path.parents:
        if parent == config.STORE_GITLAB_CACHE_PATH:
            break
        try:
            parent.rmdir()
        except OSError:
            break


@time_task(label="Workflow")
def main() -> None:
    """
    Entrypoint.

    This task initially uses a non-cached store to merge the changeset (into main), then a cached store for building.

    This workflow is known to be inefficient in terms of how changed records are parsed as identifiers from diffs, then
    later loaded from the store to allow output comments to be generated.
    """
    env: SiteEnvironment = "live"
    logger, config, catalogue = init()
    checks_base_path = Path("./workflow_results/live")

    logger.info("Checking connectivity to trusted upload host.")
    ping_host(config.SITE_TRUSTED_RSYNC_HOST)
    if not config.STORE_GITLAB_CACHE_PATH.exists():
        logger.error("GitLab cache does not exist, build will fail. Run `task cache-init` first.")
        sys.exit(1)

    print("\nThis script is for publishing records previewed in the testing site to the live site.")
    print("It combines the 'build-' and 'verify-' records dev tasks with some workflow logic.")

    # select a changeset
    branch, merge_url, issue_url = _changeset(logger=logger, cat=catalogue)

    # merge changeset and get record identifiers
    identifiers = _merge_request(logger=logger, cat=catalogue, merge_url=merge_url)

    # build and verify records
    _export(logger=logger, config=config, cat=catalogue, env=env, identifiers=identifiers)
    checks_path = _verify(cat=catalogue, env=env, identifiers=identifiers, checks_base_path=checks_base_path)

    # clean up changeset related files
    _clean(logger=logger, config=config, branch=branch)

    # generate output comments
    _output(
        logger=logger,
        config=config,
        cat=catalogue,
        env=env,
        branch=catalogue.repo.gitlab_default_branch,
        issue_url=issue_url,
        identifiers=identifiers,
    )

    logger.info("Testing records workflow exited normally.")
    logger.info(f"Checks data: {checks_path.resolve()}")


if __name__ == "__main__":
    main()
