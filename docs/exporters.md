# Lantern - Exporters

Exporters create the catalogue [Static Site](/docs/architecture.md#static-site). They provide a consistent public
interface to output information to a local path and/or to a remote AWS S3 bucket (for local debugging and external
access respectively).

Exporters can be split into:

- [Resource Exporters](#resource-exporters) - which create derived outputs of [Records](/docs/data-model.md#records)
  and [Items](/docs/data-model.md#items)
- [Site Exporters](#site-exporters) - which assemble and round out the static site

## Exporters configuration

Exporters use these options from the app `lantern.Config` class:

- `EXPORT_PATH`: base path for all local outputs, will be created if it does not exist
- `AWS_ACCESS_ID`: credential for AWS IAM principle, MUST have permissions to manage content in the S3 bucket
- `AWS_ACCESS_SECRET`: corresponding secret for the `AWS_ACCESS_ID` credential
- `AWS_S3_BUCKET`: AWS S3 bucket for published content, MUST exist and will be wholly managed by this application

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

See the [Infrastructure](/docs/infrastructure.md#exporters) docs for credentials used by exporters.

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
[Items](/docs/data-model.md#items). Resource exporters inherit from the `lantern.exporters.base.ResourceExporter` base
class.

### JSON resource exporter

Outputs a Record as a JSON file. Intended for internal consumption within the BAS metadata ecosystem.

### XML resource exporter

Outputs a Record as a ISO 19139 XML file. Intended for interoperability for use across other providers and tools.

### XML HTML resource exporter

Outputs an HTML page with minimal styling for a ISO 19139 XML document from the [XML Exporter](#xml-resource-exporter)
by applying an XSLT transformation. Intended for easier review of ISO metadata by humans.

> [!NOTE]
> This exporter applies the XSLT transformation server side, exporting the resulting HTML, rather than performing the
> transformation client side which proved unreliable.

### HTML resource exporter

Outputs a [Catalogue Item](/docs/data-model.md#catalogue-items) as an HTML page using the
[Site Templates](/docs/site.md#item-templates) for use by humans.

The `_item_class()` method determines if a [Special Catalogue Item](/docs/data-model.md#special-catalogue-items) class
should be used for each Record.

### HTML aliases resource exporter

Outputs minimal HTML redirect pages for [Item Aliases](/docs/data-model.md#item-aliases) in a Record.

For efficiency, when published to S3, the `x-amz-website-redirect-location`
[Object Redirect](https://docs.aws.amazon.com/AmazonS3/latest/userguide/how-to-page-redirect.html#redirect-requests-object-metadata)
header is added to each redirect page.

In other cases, or as a general fallback, a `<meta http-equiv="refresh">` tag in each page performs the redirect.

### Records resource exporter

Combines the outputs of all [Resource Exporters](#resource-exporters) for a set of Records and Record Summaries.

The `loads()` method is used to dynamically set the loaded Records and Record Summaries.

## Site exporters

Site exporters assemble the static site from [Resource Exporters](#resource-exporters), static resources such as CSS
files and general pages such as legal pages.

### Site resources exporter

`lantern.exporters.site.SiteResourcesExporter`

Copies CSS files, web fonts, images (e.g. favicons) and text files (for [Monitoring](/docs/monitoring.md)) from the
internal `lantern.exporters.resources` package.

### Site index exporter

`lantern.exporters.site.SiteIndexExporter`

Generates a basic index page with minimal styling and links to all [Records](/docs/data-model.md#records),
[Items](/docs/data-model.md#items) and [Item Aliases](/docs/data-model.md#item-aliases) in the static site.

> [!CAUTION]
> This isn't intended as a proper, public, homepage, more for quick access to site content when developing.

### Site pages exporter

`lantern.exporters.site.SitePagesExporter`

Generates static pages using [Site Templates](/docs/site.md#item-templates) for:

- 404 error page
- legal policies (copyright, cookies and privacy)

### Site exporter

`lantern.exporters.site.SiteExporter`

Generates a complete static site from a set of Records and Record Summaries by combining the outputs of the
[Records Resource Exporter](#records-resource-exporter) and other [Site Exporters](#site-exporters).

The `loads()` method is used to dynamically set the loaded Records and Record Summaries.
