import json
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from lantern.config import Config
from lantern.lib.metadata_library.models.record.elements.common import Date
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
from lantern.models.item.base.elements import Link
from lantern.models.item.catalogue.elements import FormattedDate
from lantern.stores.gitlab import GitLabStore


@dataclass(kw_only=True)
class OpenGraphMeta:
    """
    OpenGraph metadata for page link previews and unfurling in social media sites, chat clients, etc.

    See https://ogp.me/ for details.

    `published_at` should be an ISO 8601 formatted date string (assumed to be returned by `FormattedDate.datetime`)
    """

    locale: str = field(default="en_GB", metadata={"name": "og:locale"})
    site_name: str = field(default="BAS Data Catalogue", metadata={"name": "og:site_name"})
    type_: str = field(default="article", metadata={"name": "og:type"})
    title: str = field(metadata={"name": "og:title"})
    url: str = field(metadata={"name": "og:url"})
    description: str | None = field(default=None, metadata={"name": "og:description"})
    image: str | None = field(default=None, metadata={"name": "og:image"})
    published_at: str | None = field(default=None, metadata={"name": "og:article:published_time"})

    def dumps(self) -> dict[str, str]:
        """Compiled tags."""
        tags = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value:
                tags[f.metadata["name"]] = value
        return tags


@dataclass(kw_only=True)
class SchemaOrgAuthor:
    """Schema.org metadata for an author (Person or Organization)."""

    type_: Literal["Person", "Organization"] = field(metadata={"name": "@type"})
    name: str = field(metadata={"name": "name"})
    url: str | None = field(default=None, metadata={"name": "url"})

    def dumps(self) -> dict[str, str]:
        """Compiled metadata."""
        items = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value:
                items[f.metadata["name"]] = value
        return items


@dataclass(kw_only=True)
class SchemaOrgMeta:
    """
    Schema.org metadata for page link previews and unfurling in social media sites, chat clients, etc.

    Support is limited to item link unfurling in Microsoft Teams.
    See https://learn.microsoft.com/en-us/microsoftteams/platform/messaging-extensions/how-to/micro-capabilities-for-website-links?tabs=article
    """

    context: Literal["https://schema.org/"] = field(default="https://schema.org/", metadata={"name": "@context"})
    type_: Literal["Article"] = field(default="Article", metadata={"name": "@type"})
    name: str = field(default="BAS Data Catalogue", metadata={"name": "name"})
    headline: str = field(metadata={"name": "headline"})
    url: str = field(metadata={"name": "url"})
    description: str | None = field(default=None, metadata={"name": "description"})
    image: str | None = field(default=None, metadata={"name": "image"})
    creator: list[SchemaOrgAuthor] | None = field(default_factory=list, metadata={"name": "creator"})

    def _dumps(self) -> dict[str, str]:
        """Compiled metadata."""
        doc = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, str):
                doc[f.metadata["name"]] = value
            elif isinstance(value, list) and value:
                doc[f.metadata["name"]] = [v.dumps() for v in value if hasattr(v, "dumps")]
        return doc

    def __str__(self) -> str:
        """String representation for script tag."""
        return json.dumps(self._dumps(), indent=2)


@dataclass
class SitePageMeta:
    """Metadata for a static site page."""

    title: str
    url: str
    description: str | None = None
    inc_meta: bool = True

    @property
    def open_graph(self) -> OpenGraphMeta | None:
        """Optional OpenGraph metadata."""
        if not self.inc_meta:
            return None
        return OpenGraphMeta(title=self.title, url=self.url, description=self.description)

    @property
    def schema_org(self) -> SchemaOrgMeta | None:
        """Optional Schema.org metadata."""
        if not self.inc_meta:
            return None
        return SchemaOrgMeta(type_="Article", headline=self.title, url=self.url, description=self.description)


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
    - fallback_email: email address used when JS feedback widget can't be shown
    - build_repo_ref: optional commit reference of a working copy associated with the build
    - build_repo_base_url: optional URL to a remote the `build_repo_ref` reference exists within
    - html_open_graph: optional Open Graph metadata
    - html_schema_org: optional URL to Schema.org metadata
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
    html_open_graph: OpenGraphMeta | None = None
    html_schema_org: SchemaOrgMeta | None = None
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

    @property
    def html_open_graph_tags(self) -> dict[str, str] | None:
        """Compiled Open Graph tags for HTML head."""
        if not self.html_open_graph:
            return None
        return self.html_open_graph.dumps()

    @property
    def html_schema_org_content(self) -> str | None:
        """Schema.org script content."""
        if not self.html_schema_org:
            return None
        return str(self.html_schema_org)

    def apply_page_meta(self, page_meta: SitePageMeta) -> None:
        """Merge static page metadata."""
        self.html_title = page_meta.title
        self.html_description = page_meta.description
        self.html_open_graph = page_meta.open_graph
        self.html_schema_org = page_meta.schema_org

    @classmethod
    def from_config_store(cls, config: Config, store: GitLabStore | None = None, **kwargs: Any) -> "SiteMeta":
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
            **{  # ty: ignore[invalid-argument-type]
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
    - admin_meta_keys: keys accessing administration metadata in records
    - trusted: whether sensitive information can be shown in public site output
    """

    export_path: Path
    s3_bucket: str
    parallel_jobs: int
    admin_meta_keys: AdministrationKeys | None
    trusted: bool = False

    @property
    def site_metadata(self) -> SiteMeta:
        """Metadata without export-specific properties."""
        _site_meta = {}
        for site_field in fields(SiteMeta):
            _site_meta[site_field.name] = getattr(self, site_field.name)
        return SiteMeta(**_site_meta)  # ty: ignore[missing-argument]

    @classmethod
    def from_config_store(
        cls,
        config: Config,
        store: GitLabStore | None = None,
        **kwargs: bool | int | str | dict | Path | datetime | AdministrationKeys | None,
    ) -> "ExportMeta":
        """
        Create an Export Metadata instance from an app Config instance, optional GitLab Store and additional properties.

        In addition to the properties provided by parent `from_config_store()`, the config instance provides values for:
        - export_path: from EXPORT_PATH
        - s3_bucket: from AWS_S3_BUCKET
        - parallel_jobs: from PARALLEL_JOBS
        - admin_meta_keys: from ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE and ADMIN_METADATA_SIGNING_KEY_PUBLIC
        """
        site_kwargs = {k: v for k, v in kwargs.items() if k in {f.name for f in fields(SiteMeta)}}
        super_meta = asdict(SiteMeta.from_config_store(config, store, **site_kwargs))

        return cls(
            **{  # ty: ignore[invalid-argument-type]
                **super_meta,
                "export_path": config.EXPORT_PATH,
                "s3_bucket": config.AWS_S3_BUCKET,
                "parallel_jobs": config.PARALLEL_JOBS,
                "admin_meta_keys": config.ADMIN_METADATA_KEYS,
                **kwargs,
            }
        )
