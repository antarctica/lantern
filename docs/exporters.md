# Lantern - Exporters

Exporters create the catalogue [Static Site](/docs/architecture.md#static-site). They can broadly be split into:

- [Resource Exporters](#resource-exporters) - which create derived outputs of [Records](/docs/data-model.md#records) and
  [Items](/docs/data-model.md#items)
- [Site Exporters](#site-exporters) - which assemble and/or round out the static site with additional content

## Exporters usage

All exporters implement a [Common Interface](#exporter-classes) supporting:

- exporting to a local path using `export()`
- and/or publishing to a remote service (typically [AWS S3](/docs/architecture.md#amazon-s3)) using `publish()`

Exporters that access Records use a callable from a [Store](/docs/architecture.md#stores) to get Records by file
identifier as needed. A `selected_identifiers` property typically controls which Records are output to allow for full
or partial site builds.

> [!TIP]
> The [Site Exporter](#site-exporter) sets selected identifiers in relevant (sub-)exporters via the `select()` method.

## Exporters configuration

Exporters use these options from the app `lantern.Config` class:

- `BASE_URL`: root URL for the static site, used to generate fully qualified links to content
- `EXPORT_PATH`: base path for all local outputs, will be created if it does not exist
- `AWS_ACCESS_ID`: credential for AWS IAM principle, MUST have permissions to manage content in the S3 bucket
- `AWS_ACCESS_SECRET`: corresponding secret for the `AWS_ACCESS_ID` credential
- `AWS_S3_BUCKET`: AWS S3 bucket for published content, MUST exist and will be wholly managed by this application
- `PUBLIC_WEBSITE_ENDPOINT`: WordPress API endpoint for the public website search exporter
- `PUBLIC_WEBSITE_POST_TYPE`: custom WordPress post type for the public website search exporter
- `PUBLIC_WEBSITE_USERNAME`: WordPress user credential for the public website search exporter
- `PUBLIC_WEBSITE_PASSWORD`: WordPress application password for the public website search exporter
- `VERIFY_SHAREPOINT_PROXY_ENDPOINT`: the [SharePoint Proxy](/docs/monitoring.md#verification-sharepoint-proxy) endpoint

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

See the [Infrastructure](/docs/infrastructure.md#exporters) docs for credentials used by exporters.

In most cases, these properties are accessed indirectly via an [Exporter Metadata](/docs/data-model.md#exporter-metadata)
instance, which provides additional context such as the build time and associated commit for exported content.

> [!IMPORTANT]
> For auditing and to follow best practice, per-user IAM credentials, with suitable, limited, permissions to manage
> items in the referenced bucket, SHOULD be used over common credentials.

## Exporter classes

All exporters inherit from the `lantern.exporters.base.Exporter` abstract base class and MUST implement its minimal
public interface to:

- define an exporter name
- export information to a local path
- publish information to a remote S3 bucket

## Resource exporters

Resource exporters create format specific outputs derived from [Records](/docs/data-model.md#records) or
[Items](/docs/data-model.md#items). Exporters inherit from either:

- `lantern.exporters.base.ResourcesExporter` where the exporter processes multiple Records or Items
- `lantern.exporters.base.ResourceExporter` where the exporter processes a single Record or Item

The `ResourcesExporter` base class includes a `selected_identifiers` property to set which Records/Items to process.

When published to S3, user-defined object metadata is set to indicate the `file_identifier` and `file_revision` of the
relevant [Record Revision](/docs/data-model.md#record-revisions).

### JSON resource exporter

`lantern.exporters.json.JsonExporter`

Outputs a Record as a JSON file. Intended for internal consumption within the BAS metadata ecosystem.

### XML resource exporter

`lantern.exporters.xml.IsoXmlExporter`

Outputs a Record as a ISO 19139 XML file. Intended for interoperability for use across other providers and tools.

### XML HTML resource exporter

`lantern.exporters.xml.IsoXmlHtmlExporter`

Outputs an HTML page with minimal styling for a ISO 19139 XML document from the [XML Exporter](#xml-resource-exporter)
by applying an XSLT transformation. Intended for easier review of ISO metadata by humans.

> [!NOTE]
> This exporter applies the XSLT transformation server side, exporting the resulting HTML, rather than performing the
> transformation client side which proved unreliable.

### HTML resource exporter

`lantern.exporters.records.HtmlExporter`

Outputs a [Catalogue Item](/docs/data-model.md#catalogue-items) as an HTML page using the
[Site Templates](/docs/site.md#item-templates) for use by humans.

The `_item_class()` method determines if a [Special Catalogue Item](/docs/data-model.md#special-catalogue-items) class
should be used for each Record.

### HTML aliases resource exporter

`lantern.exporters.records.HtmlAliasesExporter`

Outputs minimal HTML redirect pages for [Item Aliases](/docs/data-model.md#item-aliases) in a Record.

For efficiency, when published to S3, the `x-amz-website-redirect-location`
[Object Redirect](https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata)
header is added to each redirect page.

In other cases, or as a general fallback, a `<meta http-equiv="refresh">` tag in each page performs the redirect.

### Records resource exporter

`lantern.exporters.records.RecordsExporter`

Coordinates other [Resource Exporters](#resource-exporters) for selected [Records](/docs/data-model.md#records).

Internally, the records exporter generates a set of individual jobs (per record and exporter) which are processed in
parallel using a worker pool for better performance.

This exporter requires a [Config](/docs/config.md) object to access credentials for standalone AWS S3 client instances
used in parallel processing.

## Site exporters

Site exporters complete the static site by including static resources such as CSS files, pages such as legal policies
and outputs that look across multiple Records.

### Site exporter

`lantern.exporters.site.SiteExporter`

Generates a complete static site by combining outputs from the
[Records Exporter](#records-resource-exporter) and other [Site Exporters](#site-exporters).

The `select()` method controls which [Records](/docs/data-model.md#records) to include.

### Site resources exporter

`lantern.exporters.site.SiteResourcesExporter`

Copies CSS files, web fonts, images (e.g. favicons) and text files (for [Monitoring](/docs/monitoring.md)) from the
internal `lantern.exporters.resources` package.

### Site index exporter

`lantern.exporters.site.SiteIndexExporter`

Generates a basic index page with links to all [Items](/docs/data-model.md#items) and
[Item Aliases](/docs/data-model.md#item-aliases) in the static site.

> [!CAUTION]
> This is intended as a quick reference to site content, not a proper, public, homepage.

### Site pages exporter

`lantern.exporters.site.SitePagesExporter`

Generates static pages using [Site Templates](/docs/site.md#item-templates) for:

- 404 error page
- legal policies (accessibility, copyright, cookies and privacy)
- content formatting guide (for abstracts, etc.)

### Public Website search exporter

`lantern.exporters.website.WebsiteSearchExporter`

> [!IMPORTANT]
> This exporter is experimental. Its implementation may change significantly without warning.

Generates a listing of 'BAS Public Website Catalogue Sync API' resources. Intended to allow users to discover
[Selected Items](#public-website-search-criteria) within the [BAS Public Website](https://www.bas.ac.uk).

These resources consist of:

- information about each item (title, thumbnail, etc.)
- meta information for the Sync API (revision, status, etc.)

This Sync API is an aggregator for items across BAS Data Catalogues and is maintained outside of this project. It is
configured to include items from this exporter via the published items listing.

#### Public Website search criteria

The public website is not intended as another catalogue of resources, and should only include more significant items
relevant to the public. Items meeting all these criteria are deemed relevant:

1. unrestricted (contain an `unrestricted` access constraint)
   - directing users to Items they can't access is not helpful
2. not superseded by another Item (are not the subject of a `RevisionOf` aggregation in another Item)
   - we don't want to confuse users by showing multiple versions of the same resource

## Other exporters

### Verification exporter

`lantern.exporters.verification.VerificationExporter`

Generates and runs a set of [Site Verification Tasks](/docs/data-model.md#verification-jobs) for
[Site Verification Checks](/docs/monitoring.md#verification-checks) and processes their results into a
[Verification Report](/docs/monitoring.md#verification-report).

Internally, the verification exporter generates a set of individual jobs (per check) which are processed in parallel
using a worker pool for better performance.
