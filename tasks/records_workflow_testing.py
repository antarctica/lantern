# Publish records to testing site

import json
import logging
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent

import inquirer
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._shared import confirm, init, ping_host, time_task
from tasks.records_build import export
from tasks.records_check import check
from tasks.records_import import clean as import_clean
from tasks.records_import import get_default_author, get_git_commit_context
from tasks.records_import import load as import_load
from tasks.records_import import push as import_push
from tasks.records_zap import clean_input_path as zap_clean_input_path
from tasks.records_zap import dump_records as zap_dump_records
from tasks.records_zap import parse_zap_records as zap_parse_records
from tasks.records_zap import process_zap_records as zap_process_records

from lantern.catalogues.bas import BasCatalogue
from lantern.config import Config
from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin
from lantern.models.record.revision import RecordRevision
from lantern.models.repository import GitUpsertResults
from lantern.models.site import ExportMeta, SiteEnvironment
from lantern.outputs.base import OutputBase
from lantern.outputs.item_html import ItemAliasesOutput, ItemCatalogueOutput
from lantern.outputs.items_bas_website import ItemsBasWebsiteOutput
from lantern.outputs.record_iso import RecordIsoHtmlOutput, RecordIsoJsonOutput, RecordIsoXmlOutput
from lantern.outputs.records_waf import RecordsWafOutput
from lantern.outputs.site_health import SiteHealthOutput
from lantern.outputs.site_index import SiteIndexOutput
from lantern.stores.gitlab import CommitResults
from lantern.utils import get_jinja_env, get_record_aliases


def _changeset_branch(issue: str) -> str:
    """Create branch name from GitLab issue URL."""
    conventional_ref = f"{issue.split('/')[-5]}/{issue.split('/')[-4]}#{issue.split('/')[-1]}"  # MAGIC/foo#123
    branch_safe_ref = conventional_ref.replace("#", ".")  # MAGIC/foo.123
    return f"changeset/{branch_safe_ref}"


class OutputCommentItem:
    """Snippet for each record processed by the workflow."""

    def __init__(self, meta: ExportMeta, record: RecordRevision) -> None:
        self._meta = meta
        self._record = record

    @property
    def _item_url(self) -> str:
        """Canonical URL to item."""
        return f"{self._meta.base_url}/items/{self._record.file_identifier}"

    @property
    def _trusted_item_url(self) -> str:
        """Canonical URL to item."""
        return f"{self._meta.base_url}/-/items/{self._record.file_identifier}"

    @property
    def _revision_url(self) -> str:
        """URL to record revision config in records repo."""
        repo = self._meta.build_repo_base_url
        fid = self._record.file_identifier
        rev = self._record.file_revision
        return f"{repo}/-/blob/{rev}/records/{fid[:2]}/{fid[2:4]}/{fid}.json"

    @property
    def _revision_link(self) -> str:
        """Markdown link to record revision config in records repo."""
        return f"[Record config for revision]({self._revision_url})"

    @property
    def _aliases(self) -> list[str]:
        """Optional aliases for record."""
        return [f"{self._meta.base_url}/{alias.identifier}" for alias in get_record_aliases(self._record)]

    @property
    def _context(self) -> dict[str, str]:
        """Data for Jinja template."""
        return {
            "type": self._record.hierarchy_level.value,
            "title": self._record.identification.title,
            "item_url": self._item_url,
            "trusted_item_url": self._trusted_item_url,
            "alias_urls": ", ".join(self._aliases),
            "revision_link": self._revision_link,
        }

    @property
    def _template(self) -> str:
        """Jinja template."""
        return dedent("""\
            {{ title }} ({{ type }})
            {% if alias_urls %}
            - 🔗 {{ alias_urls }}
            {% endif %}
            - 🌏 {{ item_url }}
            - 🔒 {{ trusted_item_url }}
            - 💾️ {{ revision_link }}
         """)

    def render(self) -> str:
        """Render jinja template as comment body."""
        jinja = get_jinja_env()
        return jinja.from_string(self._template).render(**self._context)


class OutputCommentMergeRequest:
    """Output comment for a GitLab merge request."""

    def __init__(
        self,
        config: Config,
        cat: BasCatalogue,
        env: SiteEnvironment,
        branch: str,
        commit: CommitResults,
        merge_url: str,
    ) -> None:
        self._cat = cat
        self._branch = branch
        self._commit = commit
        self._merge_url = merge_url
        self._meta = ExportMeta.from_config(config=config, env=env)
        self._jinja = get_jinja_env()

    @property
    def _records(self) -> list[RecordRevision]:
        """New/updated records from the commit."""
        identifiers = set(self._commit.new_identifiers + self._commit.updated_identifiers)
        return self._cat.repo.select(branch=self._branch, file_identifiers=identifiers)

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
        """Jinja template for merge request."""
        return dedent("""\
            {{ count }} {{ count_label }} published to testing:

            {% for item in items %}
            {{ item }}

            {% endfor %}

            If these items look ok and you are the nominated reviewer:

            - mark any threads as resolved
            - approve the merge request - but do not merge it or change it from being a draft

            Otherwise:

            - start or continue threads to track each problem (use the drop-down on the comment button to create a thread)

            _This comment was left automatically by the Lantern Experiment's [Interactive record publishing workflow](https://github.com/antarctica/lantern/blob/main/docs/usage.md#interactive-record-publishing-workflow)._

            _This comment was left by a bot user that does not monitor replies. Contact @/felnne for support._
         """)

    def render(self) -> str:
        """Render jinja template as comment body."""
        return self._jinja.from_string(self._template).render(**self._context)

    def post(self) -> None:
        """Post comment to merge request."""
        mr = self._cat.repo.select_merge_request(url=self._merge_url)
        mr.notes.create({"body": self.render()})


class OutputCommentIssue:
    """Output comment for a GitLab issue."""

    def __init__(self, cat: BasCatalogue, merge_url: str, issue_url: str) -> None:
        self._cat = cat
        self._merge_url = merge_url
        self._issue_url = issue_url
        self._jinja = get_jinja_env()

    @property
    def _context(self) -> dict[str, str]:
        """Data for Jinja template."""
        return {
            "merge_url": self._merge_url,
        }

    @property
    def _template(self) -> str:
        """Jinja template for issue."""
        return dedent("""\
            Hello,

            Some catalogue records have been published to testing in a changeset linked to this issue.

            See this merge request for more information and how to proceed with publishing: {{merge_url}}

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


@time_task(label="Zap ⚡️")
def _zap(logger: logging.Logger, cat: BasCatalogue, admin_keys: AdministrationKeys, import_path: Path) -> None:
    """
    Load and process Zap ⚡️ authored records (`zap-records` task).

    Processed records are dumped to import directory, replacing and removing initial files.
    Processed records will include any collections these records appear within.
    """
    logger.info(f"Loading Zap authored records from: '{import_path.resolve()}'")
    record_paths = zap_parse_records(logger=logger, admin_keys=admin_keys, input_path=import_path)
    records = [record_path[0] for record_path in record_paths]

    logger.debug(f"Found {len(records)} Zap authored records to process.")
    if not records:
        logger.info("No Zap records to process, skipping.")
        return

    product_types = [
        HierarchyLevelCode.PRODUCT,
        HierarchyLevelCode.MAP_PRODUCT,
        HierarchyLevelCode.PAPER_MAP_PRODUCT,
        HierarchyLevelCode.WEB_MAP_PRODUCT,
    ]
    for record in records:
        if record.hierarchy_level != HierarchyLevelCode.PRODUCT:
            continue
        print(f"Confirm product (sub-)type for record [{record.file_identifier}] '{record.identification.title}'")
        ptype = inquirer.list_input(message="Product type", choices=product_types)
        record.hierarchy_level = HierarchyLevelCode(ptype)
        logger.info(f"Hierarchy level set to '{record.hierarchy_level}' for record [{record.file_identifier}].")

    records.extend(zap_process_records(logger=logger, records=records, catalogue=cat, admin_keys=admin_keys))
    zap_dump_records(logger=logger, records=records, output_path=import_path)
    zap_clean_input_path(input_record_paths=record_paths, processed_ids=[r.file_identifier for r in records])


@time_task(label="Changeset")
def _changeset(logger: logging.Logger, keys: AdministrationKeys, records: dict[Path, Record]) -> tuple[str, str]:
    """
    Get branch for a new or existing changeset.

    Changesets are a branch of commits related to a GitLab issue, typically based on issues in administration metadata.

    Returns a selected issue and corresponding branch name based on a local naming convention.
    """
    record_issues = {"<OTHER>"}
    for record in records.values():
        admin = get_admin(keys=keys, record=record)
        if admin:
            record_issues = record_issues.union(admin.gitlab_issues)

    issue = inquirer.list_input(message="Issue URL", choices=sorted(record_issues))
    if issue == "<OTHER>":
        issue = inquirer.text(message="Issue URL")
    if not isinstance(issue, str):
        msg = "Issue must be set for a changeset."
        raise TypeError(msg) from None
    logger.info(f"Issue set to '{issue}'.")

    branch = _changeset_branch(issue=issue)
    return issue, branch


@time_task(label="Import")
def _import(logger: logging.Logger, cat: BasCatalogue, import_path: Path, branch: str) -> GitUpsertResults | None:
    """Load and commit records."""
    records = import_load(logger=logger, import_path=import_path)
    if len(records) == 0:
        return None

    commit_context = get_git_commit_context(branch=branch)
    results = import_push(logger=logger, cat=cat, records=list(records.values()), commit_context=commit_context)
    import_clean(logger=logger, records=records, results=results)
    return results


@time_task(label="Merge request")
def _merge_request(logger: logging.Logger, cat: BasCatalogue, issue_href: str, branch: str) -> tuple[str, bool]:
    """
    Ensure merge request exists for changeset.

    Returns the merge request URL and whether the MR is new (True) or pre-existing (False).

    Branches are always merged into `main`.
    """
    # check for existing MR
    mr = cat.repo.select_merge_requests(branch=branch)
    if mr:
        logger.info("Merge request exists for changeset")
        return mr[0].web_url, False

    # create MR
    logger.info("Creating merge request for changeset")
    email = get_default_author()[1]
    user = f"@{email.split('@')[0]}" if email else None
    answers = inquirer.prompt(
        [
            inquirer.Text("assignee", message="MR Assignee", default=user),
            inquirer.Text("reviewer", message="MR Reviewer", default="@"),
        ]
    )
    title = f"Records publishing changeset: {branch}"
    description_lines = [
        f"Created for records related to {issue_href}.",
        "Created by the experimental MAGIC Lantern [Interactive record publishing workflow](https://github.com/antarctica/lantern/blob/main/docs/usage.md#interactive-record-publishing-workflow).",
        "/draft",
        f"/assign {answers['assignee']}",
        f"/assign_reviewer {answers['reviewer']}",
    ]
    description = "\n\n".join(description_lines)

    mr = cat.repo.create_merge_request(
        source_branch=branch, target_branch=cat.repo.gitlab_default_branch, title=title, description=description
    )
    logger.info(f"Merge request created: {mr.web_url}")
    return mr.web_url, True


@time_task(label="Export")
def _export(cat: BasCatalogue, env: SiteEnvironment, branch: str, identifiers: set[str]) -> None:
    """
    Export items for committed records.

    Outputs limited to record specific (individual) and global that include records, classes, not API or site resources.
    """
    outputs: list[type[OutputBase]] = [
        SiteIndexOutput,
        SiteHealthOutput,
        RecordsWafOutput,
        ItemsBasWebsiteOutput,
        ItemCatalogueOutput,
        ItemAliasesOutput,
        RecordIsoJsonOutput,
        RecordIsoXmlOutput,
        RecordIsoHtmlOutput,
    ]
    export(cat=cat, env=env, target="remote", branch=branch, identifiers=identifiers, outputs=outputs)


@time_task(label="Verify")
def _verify(
    cat: BasCatalogue, env: SiteEnvironment, branch: str, identifiers: set[str], checks_base_path: Path
) -> Path:
    """Verify items for committed records."""
    check(cat=cat, env=env, target="local", branch=branch, identifiers=identifiers, local_path=checks_base_path)
    # clean up verification output
    with checks_base_path.joinpath("-/checks/data.json").open() as f:
        data = json.load(f)
    shutil.rmtree(checks_base_path.joinpath("-"), ignore_errors=True)
    suffix = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z").replace(":", "-")
    data_path = checks_base_path / f"checks-data_{suffix}.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open(mode="w") as f:
        json.dump(data, f, indent=2)
    return data_path


@time_task(label="Output")
def _output(
    logger: logging.Logger,
    config: Config,
    cat: BasCatalogue,
    env: SiteEnvironment,
    branch: str,
    commit: CommitResults,
    issue_url: str,
    merge_url: str,
    merge_new: bool,
) -> None:
    """Add comments to GitLab merge request and, if MR is new, issue."""
    mr_comment = OutputCommentMergeRequest(
        config=config, cat=cat, env=env, branch=branch, commit=commit, merge_url=merge_url
    )
    print(mr_comment.render())
    confirm(logger, f"Post comment above to '{merge_url}?")
    mr_comment.post()

    if not merge_new:
        return
    issue_comment = OutputCommentIssue(cat=cat, merge_url=merge_url, issue_url=issue_url)
    print(issue_comment.render())
    confirm(logger, f"Post comment above to '{issue_url}'?")
    issue_comment.post()


@time_task(label="Workflow")
def main() -> None:
    """
    Entrypoint.

    This task uses a non-cached GitLab store as it will be pushing to a new branch for a changeset, and likely
    operating on a limited number of records.
    """
    logger, config, catalogue = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW
    env: SiteEnvironment = "testing"
    import_path = Path("./import")
    checks_base_path = Path("./checks/testing")

    logger.info("Checking connectivity to trusted upload host.")
    ping_host(config.SITE_TRUSTED_RSYNC_HOST)

    print("\nThis script is for adding or updating records and previewing them in the testing site.")
    print("It combines the 'zap-', 'import-', 'build-' and 'verify-' records dev tasks with some workflow logic.")
    print(f"\nTo begin, stage records for import in '{import_path.resolve()}'.")
    print("TIP! See the 'records-select' and/or 'records-clone' tasks if useful.")
    confirm(logger, "Are records staged in import directory?")

    # load records, pre-processing any Zap ⚡️ authored records
    _zap(logger=logger, cat=catalogue, admin_keys=admin_keys, import_path=import_path)
    records = import_load(logger=logger, import_path=import_path)
    if len(records) < 1:
        logger.info("No valid records to commit, exiting.")
        sys.exit(0)

    # open or reuse changeset
    issue_url, branch = _changeset(logger=logger, keys=admin_keys, records=records)

    # commit records
    commit = _import(logger=logger, cat=catalogue, import_path=import_path, branch=branch)
    if commit is None:
        logger.warning("No records were loaded, exiting.")
        sys.exit(0)
    identifiers = set(commit.new_identifiers + commit.updated_identifiers)
    if len(identifiers) == 0:
        logger.warning("No records were imported, exiting.")
        sys.exit(0)

    # create a merge request if needed
    merge_url, merge_new = _merge_request(logger=logger, cat=catalogue, issue_href=issue_url, branch=branch)

    # build and verify records
    _export(cat=catalogue, env=env, branch=branch, identifiers=identifiers)
    checks_path = _verify(
        cat=catalogue, env=env, branch=branch, identifiers=identifiers, checks_base_path=checks_base_path
    )

    # generate output comments
    _output(
        logger=logger,
        config=config,
        cat=catalogue,
        env=env,
        branch=branch,
        commit=commit,
        issue_url=issue_url,
        merge_url=merge_url,
        merge_new=merge_new,
    )

    logger.info("Testing records workflow exited normally.")
    logger.info(f"Checks data: {checks_path.resolve()}")


if __name__ == "__main__":
    main()
