# Lantern - Exporters

Exporters create the catalogue [Static Site](/docs/architecture.md#static-site). They can be broadly split into:

- [Resource Exporters](#resource-exporters) - which create derived outputs of individual
  [Records](/docs/data-model.md#records) and [Items](/docs/data-model.md#items)
- [Resources Exporters](#resources-exporters) - which create outputs based on all or selected
  [Records](/docs/data-model.md#records) and [Items](/docs/data-model.md#items)
- [Other Exporters](#other-exporters) - which round out and/or coordinate the static site

## Exporters usage

All exporters implement a [Common Interface](#exporter-classes) supporting:

- exporting to a local path using `export()`
- and/or publishing to a remote service (typically [AWS S3](/docs/architecture.md#amazon-s3)) using `publish()`

Exporters that access Records use a callable from a [Store](/docs/architecture.md#stores) to select single or multiple
Records as needed. A `selected_identifiers` property MAY control which Records are output, for partial site builds.

### Trusted publishing

Access to [Administrative Metadata](/docs/data-model.md#item-administrative-metadata) (such as the admin tab of
[Catalogue Item](/docs/data-model.md#catalogue-items) outputs) is controlled by the `trusted`
[Export](/docs/data-model.md#export-metadata) flag, which defaults to false (disabled).

> [!CAUTION]
> Access control MUST be used for any outputs created where the `trusted` flag is true.

## Exporters configuration

Exporters use these options from the app `lantern.Config` class:

- `BASE_URL`: root URL for the static site, used to generate fully qualified links to content
- `EXPORT_PATH`: base path for all local outputs, will be created if it does not exist
- `AWS_ACCESS_ID`: credential for AWS IAM principle, MUST have permissions to manage content in the S3 bucket
- `AWS_ACCESS_SECRET`: corresponding secret for the `AWS_ACCESS_ID` credential
- `AWS_S3_BUCKET`: AWS S3 bucket for published content, MUST exist and will be wholly managed by this application
- `TRUSTED_UPLOAD_HOST`: Optional remote host for [Trusted Publishing](#trusted-publishing) content
- `TRUSTED_UPLOAD_PATH`: base local or remote path for [Trusted Publishing](#trusted-publishing) content
- `PUBLIC_WEBSITE_ENDPOINT`: WordPress API endpoint for the public website search exporter
- `PUBLIC_WEBSITE_POST_TYPE`: custom WordPress post type for the public website search exporter
- `PUBLIC_WEBSITE_USERNAME`: WordPress user credential for the public website search exporter
- `PUBLIC_WEBSITE_PASSWORD`: WordPress application password for the public website search exporter
- `VERIFY_SHAREPOINT_PROXY_ENDPOINT`: the [SharePoint Proxy](/docs/monitoring.md#verification-sharepoint-proxy) endpoint

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

See the [Infrastructure](/docs/infrastructure.md#exporters) docs for credentials used by exporters.

In most cases, these properties are accessed indirectly via an [Export Metadata](/docs/data-model.md#export-metadata)
instance, which provides additional context such as the build time and associated commit for exported content.

> [!IMPORTANT]
> Per-user AWS IAM credentials, with suitable, limited, permissions to manage items in the referenced bucket, SHOULD be
> used over common credentials.

## Exporter classes

All exporters inherit from the `lantern.exporters.base.Exporter` abstract base class and MUST implement its minimal
public interface to:

- define an exporter name
- export information to a local path
- publish information to a remote S3 bucket

## Resource exporters

Resource exporters inherit from `lantern.exporters.base.ResourceExporter` to create outputs for individual
[Records](/docs/data-model.md#records) or [Items](/docs/data-model.md#items).

When published to S3, [user-defined](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html#UserMetadata)
object metadata includes the `file_identifier` and `file_revision` from the relevant
[Record Revision](/docs/data-model.md#record-revisions).

### JSON resource exporter

`lantern.exporters.json.JsonExporter`

Simple exporter outputting Records as JSON files (using the BAS ISO 19115 schema). Intended for internal consumption
within the BAS metadata ecosystem.

### XML resource exporter

`lantern.exporters.xml.IsoXmlExporter`

Simple exporter outputting Records as ISO 19139 XML files. Intended for interoperability for use across wider providers
and tools.

### XML HTML resource exporter

`lantern.exporters.xml.IsoXmlHtmlExporter`

Extends the [XML Resource Exporter](#xml-resource-exporter) outputting Records as HTML pages with minimal formatting
by applying an XSLT transformation. Intended for easier review of ISO metadata by humans.

> [!NOTE]
> The XSLT transformation is applied server side, outputting the resulting HTML, to avoid problems with client side
> transformations.

### HTML resource exporter

`lantern.exporters.records.HtmlExporter`

More complex exporter outputting Records as [Catalogue Item](/docs/data-model.md#catalogue-items) HTML pages. Uses
[Site Templates](/docs/site.md#item-templates) for consumption by (human) end-users.

Uses a [Store](/docs/architecture.md#stores) select record callable to generate item summaries for related records, and
an `_item_class()` method to determine if a [Special Catalogue Item](/docs/data-model.md#special-catalogue-items) class
should be used for a Record.

### HTML aliases resource exporter

`lantern.exporters.records.HtmlAliasesExporter`

Simple exporter outputting minimal HTML redirect pages for [Item Aliases](/docs/data-model.md#item-aliases) in Records.

Uses a `<meta http-equiv="refresh">` tag in each page.

When published to S3, also uses the `x-amz-website-redirect-location`
[Object Redirect](https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata)
header for efficiency.

## Resources exporters

Resources exporters typically inherit from `lantern.exporters.base.ResourcesExporter` to create outputs for all
[Records](/docs/data-model.md#records) or [Items](/docs/data-model.md#items).

> [!NOTE]
> These exporters do not support partial record selections, as they produce single outputs containing or referencing
> all Records or Items, which could omit previously generated, non-selected (but still valid), items in partial builds.

### Web Accessible Folder resource exporter

`lantern.exporters.waf.WebAccessibleFolderExporter`

Outputs a [Web Accessible Folder (WAF)](/docs/access.md#web-accessible-folder) (WAF) endpoint.

Formed of a directory with a basic, unstyled, HTML index page linking to ISO 19139 encoded
[Records](/docs/data-model.md#records) output by the [XML Resource Exporter](#xml-resource-exporter).

### Site index exporter

`lantern.exporters.site.SiteIndexExporter`

Outputs a styled HTML page linking to [Items](/docs/data-model.md#items) and
[Item Aliases](/docs/data-model.md#item-aliases) output by the [HTML Exporter](#html-resource-exporter) and
[HTML Aliases Exporter](#html-aliases-resource-exporter).

> [!NOTE]
> This page is intended as a basic, internal, reference to site content - not a proper, public, homepage.

### Public Website search exporter

`lantern.exporters.website.WebsiteSearchExporter`

Outputs a listing of 'BAS Public Website Catalogue Sync API' resources. Intended to allow users to discover
[Selected Items](#public-website-search-criteria) within the [BAS Public Website](https://www.bas.ac.uk).

These resources consist of:

- information about each item (title, thumbnail, etc.)
- meta information for the Sync API (revision, status, etc.)

> [!NOTE]
> This Sync API is an aggregator for items across BAS Data Catalogues and is maintained outside of this project. It is
> configured to include items from this exporter via the published items listing.

#### Public Website search criteria

The public website is not intended as another catalogue of resources, and should only include more significant items
relevant to the public. Items meeting all these criteria are deemed relevant:

1. unrestricted (contain an `unrestricted` access constraint)
   - directing users to Items they can't access is not helpful
2. not superseded by another Item (are not the subject of a `RevisionOf` aggregation in another Item)
   - we don't want to confuse users by showing multiple versions of the same resource

## Other exporters

Other exporters inherit from `lantern.exporters.base.Exporter` to create non-record/item related outputs, or to
coordinate other exporters.

### Records resource exporter

`lantern.exporters.records.RecordsExporter`

Coordinates [Resource Exporters](#resource-exporters) for all or selected [Records](/docs/data-model.md#records).

Uses a set of parallel processing workers to process `{record}:{exporter}` jobs (per record and exporter) for better
performance. Singletons are used to share resources (such as a Store) between jobs in each worker. This requires
passing a [Config](/docs/config.md) object.

### Site resources exporter

`lantern.exporters.site.SiteResourcesExporter`

Copies [CSS](/docs/site.md#styling), [JavaScript](/docs/site.md#scripts), fonts, images (for favicons) and text files
(for [Monitoring](/docs/monitoring.md)) from the internal `lantern.exporters.resources` module into the static site.

Jinja2 templates are used for including variables in JavaScript files.

### Site API exporter

> [!WARNING]
> This exporter is experimental.

`lantern.exporters.site.SiteApiExporter`

Outputs:

- a [RFC 9727 API Catalog](https://datatracker.ietf.org/doc/html/rfc9727)
- a raw [OpenAPI](/docs/site.md#openapi-definition) JSON document
- interactive documentation based on this definition built using
  [Scalar](https://guides.scalar.com/scalar/scalar-api-references)

The API Catalog is rendered from a simple Python dict. The OpenAPI definition and documentation are rendered from Jinja
templates.

### Site health exporter

`lantern.exporters.site.SiteHealthExporter`

Outputs:

- a [Draft API Health Check](https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check)

The health check is rendered from a Python dict.

### Site pages exporter

`lantern.exporters.site.SitePagesExporter`

Outputs a set of HTML pages using [Site Templates](/docs/site.md#item-templates) for:

- 404 error page
- legal policies (accessibility, copyright, cookies and privacy)
- content formatting guide (for abstracts, etc.)

Sharing previews, similar to [Item Pages](/docs/site.md#item-sharing-previews), are enabled via
`lantern.models.site.SitePageMeta` instances with manually defined values.

### Site exporter

`lantern.exporters.site.SiteExporter`

Coordinates other exporters to create complete static site, including a [Records Exporter](#records-resource-exporter).
which can be optionally limited to a set of selected record identifiers for partial site builds.

### Verification exporter

`lantern.exporters.verification.VerificationExporter`

Generates and runs a set of [Tasks](/docs/data-model.md#verification-jobs) run in parallel for
[Site Verification Checks](/docs/monitoring.md#verification-checks), then processes their results to output a
[Verification Report](/docs/monitoring.md#verification-report).
