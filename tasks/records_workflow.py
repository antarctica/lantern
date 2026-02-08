import functools
import logging
import re
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import inquirer
from gitlab.exceptions import GitlabGetError
from mypy_boto3_s3 import S3Client
from tasks._config import ExtraConfig
from tasks._record_utils import init, init_store, parse_records
from tasks.records_import import clean as import_clean
from tasks.records_import import load as import_load
from tasks.records_import import push as import_push
from tasks.records_zap import clean_input_path as zap_clean_input_path
from tasks.records_zap import dump_records as zap_dump_records
from tasks.records_zap import parse_records as zap_parse_records
from tasks.records_zap import process_records as zap_process_records

from lantern.config import Config
from lantern.exporters.site import SiteExporter
from lantern.exporters.verification import VerificationExporter
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin
from lantern.models.record.revision import RecordRevision
from lantern.models.site import ExportMeta
from lantern.models.verification.types import VerificationContext
from lantern.stores.gitlab import CommitResults, GitLabStore
from lantern.stores.gitlab_cache import GitLabCachedStore
from lantern.utils import get_jinja_env, get_record_aliases


class OutputCommentItem:
    """Snippet for each record processed by the workflow."""

    def __init__(self, meta: ExportMeta, base_url: str, record: RecordRevision) -> None:
        self._meta = meta
        self._base_url = base_url
        self._record = record

    @property
    def _item_url(self) -> str:
        """Canonical URL to item."""
        return f"{self._base_url}/items/{self._record.file_identifier}"

    @property
    def _trusted_item_url(self) -> str:
        """Canonical URL to item."""
        return f"{self._base_url}/-/items/{self._record.file_identifier}"

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
        """Aliases for record."""
        return [f"{self._base_url}/{alias.identifier}" for alias in get_record_aliases(self._record)]

    @property
    def data(self) -> dict[str, str]:
        """Data for Jinja template."""
        return {
            "type": self._record.hierarchy_level.value,
            "title": self._record.identification.title,
            "item_url": self._item_url,
            "trusted_item_url": self._trusted_item_url,
            "alias_urls": ", ".join(self._aliases),
            "revision_link": self._revision_link,
        }


class OutputComment:
    """Output comment for a GitLab issue."""

    def __init__(
        self,
        logger: logging.Logger,
        config: Config,
        store: GitLabStore,
        base_url: str,
        commit: CommitResults,
        merge_url: str | None,
        issue_url: str | None,
    ) -> None:
        self._logger = logger
        self._config = config
        self._store = store
        self._base_url = base_url
        self._commit = commit
        self._merge_url = merge_url
        self._issue_url = issue_url
        self._meta = ExportMeta.from_config_store(
            config=config, store=store, build_repo_ref=store.head_commit if store.head_commit else "-"
        )

    @property
    def _records(self) -> list[RecordRevision]:
        """New/updated records from the commit."""
        identifiers = set(self._commit.new_identifiers + self._commit.updated_identifiers)
        return self._store.select(file_identifiers=identifiers)

    @property
    def _items(self) -> list[OutputCommentItem]:
        """Generated snippets for each record."""
        return [OutputCommentItem(meta=self._meta, base_url=self._base_url, record=record) for record in self._records]

    @property
    def _context(self) -> dict[str, str | list[dict[str, str]]]:
        """Data for Jinja template."""
        count = len(self._records)
        return {
            "count": str(count),
            "count_label": "records" if count != 1 else "record",
            "commit_url": f"{self._config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/commit/{self._commit.commit}",
            "merge_url": self._merge_url,
            "items": [item.data for item in self._items],
        }  # ty:ignore[invalid-return-type]

    @property
    def _template(self) -> str:
        """Jinja template."""
        return """
{{ count }} {{ count_label }} published to testing in commit {{commit_url}}{% if merge_url %} as part of changeset {{merge_url}}{% endif %}:

{% for item in items %}
- {{ item.title }} ({{ item.type }})
  {% if item.alias_urls %}
  - 🔗 {{ item.alias_urls }}
  {% endif %}
  - 🌏 {{ item.item_url }}
  - 🔒 {{ item.trusted_item_url }}
  - 💾️ {{ item.revision_link }}
{% endfor %}

_This comment was left automatically by the Lantern Experiment's [Interactive record publishing workflow](https://github.com/antarctica/lantern/blob/main/docs/usage.md#interactive-record-publishing-workflow)._
        """

    def render(self) -> str:
        """Render jinja template as comment body."""
        jinja = get_jinja_env()
        return jinja.from_string(self._template).render(**self._context)

    def post(self) -> None:
        """Post comment to GitLab issue."""
        if not self._issue_url:
            self._logger.warning("Cannot post comment, no issue URL set.")

        match = re.match(r"https?://[^/]+/(.+?)/-/issues/(\d+)", self._issue_url)  # ty:ignore[no-matching-overload]
        if not match:
            msg = f"Invalid GitLab issue URL: {self._issue_url}"
            raise ValueError(msg) from None
        project_path = match.group(1)  # "felnne/xdsz"
        issue_iid = int(match.group(2))  # 1

        try:
            # noinspection PyProtectedMember
            project = self._store._client.projects.get(project_path)
        except GitlabGetError:
            msg = f"Cannot access GitLab project at path: {project_path}"
            raise ValueError(msg) from None
        issue = project.issues.get(issue_iid)
        issue.notes.create({"body": self.render()})


def _time_task(label: str) -> Callable:
    """Time a task and log duration."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202,
            start = datetime.now(tz=UTC)
            result = func(*args, **kwargs)
            end = datetime.now(tz=UTC)
            print(f"{label} took {round((end - start).total_seconds())} seconds")
            return result

        return wrapper

    return decorator


def _confirm(logger: logging.Logger, message: str) -> None:
    """Confirm user wants to proceed."""
    answers = inquirer.prompt(
        [
            inquirer.Confirm(name="confirm", message=message, default=True),
        ]
    )
    if not answers["confirm"]:
        logger.info("Cancelled by the user.")
        sys.exit(1)


def _changeset_branch_name(issue: str) -> str:
    """Create branch name from GitLab issue URL."""
    conventional_ref = f"{issue.split('/')[-5]}/{issue.split('/')[-4]}#{issue.split('/')[-1]}"  # MAGIC/foo#123
    branch_safe_ref = conventional_ref.replace("#", ".")  # MAGIC/foo.123
    return f"changeset/{branch_safe_ref}"


def _changeset_branch(logger: logging.Logger, issue: str | None, default: str) -> str:
    """Select branch name from optional GitLab issue URL."""
    if not issue:
        logger.info("No GitLab issue selected, skipping changeset creation and using default branch")
        return default
    return _changeset_branch_name(issue=issue)


@_time_task(label="Zap ⚡️")
def _zap(logger: logging.Logger, store: GitLabStore, admin_keys: AdministrationKeys, import_path: Path) -> None:
    """
    Load and process Zap ⚡️ authored records (`zap-records` task).

    Processed records are dumped to import directory, replacing and removing initial files.
    Processed records will include any collections these records appear within.
    """
    logger.info(f"Loading Zap authored records from: '{import_path.resolve()}'")
    record_paths = zap_parse_records(logger=logger, input_path=import_path)
    records = [record_path[0] for record_path in record_paths]

    logger.debug(f"Found {len(records)} Zap authored records to process.")
    if not records:
        logger.info("No Zap records to process, skipping.")
        return

    records.extend(zap_process_records(logger=logger, records=records, store=store, admin_keys=admin_keys))
    zap_dump_records(logger=logger, records=records, output_path=import_path)
    zap_clean_input_path(input_record_paths=record_paths, processed_ids=[r.file_identifier for r in records])  # ty:ignore[invalid-argument-type]


@_time_task(label="Changeset")
def _changeset(
    logger: logging.Logger, config: Config, keys: AdministrationKeys, import_path: Path
) -> tuple[GitLabCachedStore, str | None]:
    """
    Create, or use an existing changeset, to relate a set of commits for some records based on a GitLab issue.

    Returns a suitable, cached, store to use, either using a changeset branch or the Config default.

    For convenience, GitLab issues listed in admin metadata are offered as a suggestion for a changeset branch.

    A cached store is used as a workaround for a race condition when switching to a new branch. Exiting records return
    a 404 when fetched, causing updated records to be inaccurately marked as additions in commits which GitLab rejects.
    """
    records = [record_path[0] for record_path in list(parse_records(logger=logger, search_path=import_path))]
    record_issues = {"<NONE>"}
    for record in records:
        admin = get_admin(keys=keys, record=record)
        if admin:
            record_issues = record_issues.union(admin.gitlab_issues)
    record_issues.add("<OTHER>")

    print(
        "\nEnsure GitLab issue selected is where changeset should be linked (e.g. Helpdesk vs. Mapping Coordination)."
    )
    issue = inquirer.prompt([inquirer.List("issue", message="Issue URL", choices=record_issues)])["issue"]
    print(issue)
    if issue == "<NONE>":
        issue = None
    elif issue == "<OTHER>":
        issue = inquirer.prompt([inquirer.Text(name="url", message="Issue URL", default="<NONE>")])["url"]
        if issue == "<NONE>":
            issue = None

    branch = _changeset_branch(logger=logger, issue=issue, default=config.STORE_GITLAB_BRANCH)
    store = init_store(logger=logger, config=config, branch=branch, cached=True)
    logger.info(f"Using changeset branch: '{store._source.ref}'")
    return store, issue  # ty:ignore[invalid-return-type]


@_time_task(label="Import")
def _import(logger: logging.Logger, config: Config, store: GitLabStore, import_path: Path) -> CommitResults | None:
    """Import records."""
    records = import_load(logger=logger, input_path=import_path)
    if len(records) == 0:
        return None
    commit = import_push(logger=logger, config=config, store=store, records=list(records.values()))
    import_clean(logger=logger, records=records, commit=commit)
    return commit


@_time_task(label="Merge request")
def _merge_request(logger: logging.Logger, store: GitLabStore, issue_href: str | None) -> str | None:
    """
    Ensure merge request exists for changeset if used.

    Branches are always merged into `main`.
    """
    if issue_href is None:
        logger.info("No changeset provided, skipping merge-request creation.")
        return None

    # check for existing MR
    mr = store._project.mergerequests.list(state="opened", source_branch=store._source.ref)
    if mr:
        logger.info("Merge request exists for changeset")
        return mr[0].web_url

    # create MR
    logger.info("Creating merge request for changeset")
    mr = store._project.mergerequests.create(
        {
            "source_branch": store._source.ref,
            "target_branch": "main",
            "title": f"Records publishing changeset: {store._source.ref}",
            "description": f"Created for records related to {issue_href}.\n\nCreated by the experimental MAGIC Lantern interactive records publishing workflow.",
        }
    )
    logger.info(f"Merge request created: {mr.web_url}")
    return mr.web_url


@_time_task(label="Build")
def _build(
    logger: logging.Logger, config: ExtraConfig, store: GitLabCachedStore, s3: S3Client, identifiers: set[str]
) -> None:
    """Build items for committed records."""
    meta = ExportMeta.from_config_store(
        config=config, store=store, build_repo_ref=store.head_commit if store.head_commit else "-"
    )
    site = SiteExporter(config=config, meta=meta, logger=logger, s3=s3, store=store, selected_identifiers=identifiers)
    logger.info("Freezing store.")
    store._frozen = True
    store._cache._frozen = True
    logger.info(f"Publishing {len(identifiers)} records.")
    site.publish()


@_time_task(label="Verify")
def _verify(
    logger: logging.Logger, config: Config, store: GitLabStore, s3: S3Client, base_url: str, identifiers: set[str]
) -> None:
    """Verify items for committed records."""
    logger.info(f"Verifying {len(identifiers)} records.")
    context: VerificationContext = {
        "BASE_URL": base_url,
        "SHAREPOINT_PROXY_ENDPOINT": config.VERIFY_SHAREPOINT_PROXY_ENDPOINT,
        "SAN_PROXY_ENDPOINT": config.VERIFY_SAN_PROXY_ENDPOINT,
    }
    meta = ExportMeta.from_config_store(
        config=config, store=store, build_repo_ref=store.head_commit if store.head_commit else "-"
    )
    exporter = VerificationExporter(
        logger=logger, meta=meta, s3=s3, context=context, select_records=store.select, selected_identifiers=identifiers
    )
    exporter.run()
    exporter.export()
    logger.info(f"Verification complete, result: {exporter.report.data['pass_fail']}.")
    logger.info("See local export for report.")


@_time_task(label="Output")
def _output(
    logger: logging.Logger,
    config: Config,
    store: GitLabStore,
    base_url: str,
    commit: CommitResults,
    merge_url: str | None,
    issue_url: str | None,
) -> None:
    """Output comment for GitLab issue."""
    comment = OutputComment(
        logger=logger,
        config=config,
        store=store,
        base_url=base_url,
        commit=commit,
        merge_url=merge_url,
        issue_url=issue_url,
    )
    print(comment.render())
    if not issue_url:
        logger.info("No GitLab issue set, skipping commenting on issue.")
        return
    _confirm(logger, "Post comment above to GitLab issue?")
    comment.post()
    logger.info(f"Comment posted to {issue_url}.")


@_time_task(label="Workflow")
def main() -> None:
    """
    Entrypoint.

    This task uses a non-cached GitLab store as it's likely to be pushing to a new branch for a changeset, and operating
    on a limited number of records.
    """
    logger, config, store, s3 = init()
    admin_keys = config.ADMIN_METADATA_KEYS_RW
    import_path = Path("./import")
    base_url = "https://data-testing.data.bas.ac.uk"
    testing_bucket = "add-catalogue-integration.data.bas.ac.uk"

    if testing_bucket != config.AWS_S3_BUCKET:
        logger.error("No. Non-testing bucket selected.")
        sys.exit(1)

    print("\nThis script is for adding or updating records in the Catalogue.")
    print("It combines the 'zap-' 'import-', 'build-' and 'verify-' records dev tasks with some workflow logic.")
    print(f"\nTo begin, stage records for import in '{import_path.resolve()}'.")
    print("TIP! See the 'records-clone', 'records-select' and/or 'records-load' tasks if useful.")
    _confirm(logger, "Are records staged in import directory?")

    # process any zap authored records
    _zap(logger=logger, store=store, admin_keys=admin_keys, import_path=import_path)
    records = import_load(logger=logger, input_path=import_path)
    if len(records) < 1:
        logger.info("No valid records to commit, exiting.")
        sys.exit(0)

    # open a changeset if needed
    store, issue_url = _changeset(logger=logger, config=config, keys=admin_keys, import_path=import_path)

    # import records and create merge request if needed
    commit = _import(logger=logger, config=config, store=store, import_path=import_path)
    if commit is None:
        logger.warning("No records were loaded, exiting.")
        sys.exit(0)
    merge_url = _merge_request(logger=logger, store=store, issue_href=issue_url)
    identifiers = set(commit.new_identifiers + commit.updated_identifiers)
    if len(identifiers) == 0:
        logger.warning("No records were imported, exiting.")
        sys.exit(0)

    # build and verify records
    _build(logger=logger, config=config, store=store, s3=s3, identifiers=identifiers)
    _verify(logger=logger, config=config, store=store, s3=s3, base_url=base_url, identifiers=identifiers)

    # generate output comment
    _output(
        logger=logger,
        config=config,
        store=store,
        base_url=base_url,
        merge_url=merge_url,
        issue_url=issue_url,
        commit=commit,
    )


if __name__ == "__main__":
    main()
