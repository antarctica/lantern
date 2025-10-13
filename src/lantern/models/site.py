from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.models.item.base.elements import Link
from lantern.models.item.catalogue.elements import FormattedDate
from lantern.stores.gitlab import GitLabStore


@dataclass(kw_only=True)
class SiteMeta:
    """
    Common metadata needed for building catalogue static site.

    - base_url: endpoint needed to construct absolute URLs (e.g. 'https://example.com')
    - build_key: cache busting value
    - html_title: HTML head title value (will be combined with site name)
    - sentry_src: Sentry CDN URL
    - plausible_domain: Plausible Analytics site identifier
    - embedded_maps_endpoint: BAS Embedded Maps Service endpoint
    - items_enquires_endpoint: endpoint for item enquiries form
    - items_enquires_turnstile_key: site key for item enquiries Cloudflare Turnstile widget
    - generator: name of application and source of records
    - version: version of application
    - build_time: time the build was triggered
    - fallback_email: email address used when Sentry feedback is unavailable
    - build_repo_ref: optional commit reference of a working copy associated with the build
    - build_repo_base_url: optional URL to a remote the `build_repo_ref` reference exists within
    - html_open_graph: optional Open Graph metadata
    - html_schema_org: optional Schema.org metadata
    - html_description: optional description meta tag
    """

    base_url: str
    build_key: str
    html_title: str
    sentry_src: str
    plausible_domain: str
    embedded_maps_endpoint: str
    items_enquires_endpoint: str
    items_enquires_turnstile_key: str
    generator: str
    version: str
    build_time: datetime = field(default_factory=lambda: datetime.now(tz=UTC).replace(microsecond=0))
    fallback_email: str = "magic@bas.ac.uk"
    build_repo_ref: str | None = None
    build_repo_base_url: str | None = None
    html_open_graph: dict = field(default_factory=dict)
    html_schema_org: str | None = None
    html_description: str | None = None

    @property
    def html_title_suffixed(self) -> str:
        """HTML title with site name."""
        return f"{self.html_title} | BAS Data Catalogue"

    @property
    def build_ref(self) -> Link | None:
        """
        Build link to commit associated with build in remote repository, if available.

        Uses short ref as link value.

        Assumes associated repo is hosted using a GitLab instance.
        """
        if self.build_repo_ref and self.build_repo_base_url:
            return Link(
                value=self.build_repo_ref[:8],
                href=f"{self.build_repo_base_url}/-/commit/{self.build_repo_ref}",
                external=True,
            )
        return None

    @property
    def build_time_fmt(self) -> FormattedDate:
        """Build time as formatted date for templates."""
        return FormattedDate.from_rec_date(Date(date=datetime.fromisoformat(self.build_time.isoformat())))

    @classmethod
    def from_config_store(
        cls, config: Config, store: GitLabStore | None = None, **kwargs: datetime | dict | str
    ) -> "SiteMeta":
        """
        Create a Site Metadata instance from an app Config instance, optional GitLab Store and additional properties.

        The Config instance provides values for:
        - base_url
        - build_key
        - sentry_src
        - plausible_domain
        - embedded_maps_domain
        - items_enquires_endpoint
        - items_enquires_turnstile_key
        - generator
        - build_repo_base_url
        - version

        The optional GitLab Store provides values for:
        - build_repo_ref

        Initial (blank) values are set for:
        - html_title
        """
        build_ref = None
        if isinstance(store, GitLabStore):
            build_ref = store.head_commit

        return cls(
            **{
                "base_url": config.BASE_URL,
                "build_key": config.TEMPLATES_CACHE_BUST_VALUE,
                "sentry_src": config.TEMPLATES_SENTRY_SRC,
                "plausible_domain": config.TEMPLATES_PLAUSIBLE_DOMAIN,
                "embedded_maps_endpoint": config.TEMPLATES_ITEM_MAPS_ENDPOINT,
                "items_enquires_endpoint": config.TEMPLATES_ITEM_CONTACT_ENDPOINT,
                "items_enquires_turnstile_key": config.TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY,
                "generator": config.NAME,
                "version": config.VERSION,
                "build_repo_ref": build_ref,
                "build_repo_base_url": config.TEMPLATES_ITEM_VERSIONS_ENDPOINT,
                "html_title": "",
                **kwargs,
            }
        )


@dataclass(kw_only=True)
class ExportMeta(SiteMeta):
    """
    Metadata needed for exporters.

    Extends SiteMetadata with additional properties from app config:

    - export_path: base path for local site output
    - s3_bucket: S3 bucket name for published site output
    - parallel_jobs: number of jobs to run in parallel
    """

    export_path: Path
    s3_bucket: str
    parallel_jobs: int

    @property
    def site_metadata(self) -> SiteMeta:
        """Metadata without export-specific properties."""
        meta = asdict(self)
        meta.pop("export_path", None)
        meta.pop("s3_bucket", None)
        meta.pop("parallel_jobs", None)
        return SiteMeta(**meta)  # ty: ignore[missing-argument]

    @classmethod
    def from_config_store(
        cls, config: Config, store: GitLabStore | None = None, **kwargs: datetime | dict | str
    ) -> "ExportMeta":
        """
        Create an Export Metadata instance from an app Config instance, optional GitLab Store and additional properties.

        In addition to the properties provided by parent `from_config_store()`, the config instance provides values for:
        - export_path: from EXPORT_PATH
        - s3_bucket: from AWS_S3_BUCKET
        - parallel_jobs: from PARALLEL_JOBS
        """
        super_meta = asdict(SiteMeta.from_config_store(config, store, **kwargs))

        return cls(
            **{
                **super_meta,
                "export_path": config.EXPORT_PATH,
                "s3_bucket": config.AWS_S3_BUCKET,
                "parallel_jobs": config.PARALLEL_JOBS,
                **kwargs,
            }
        )
