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

- `BASE_URL`: root URL for the static site, used to generate fully qualified links to content
- `EXPORT_PATH`: base path for all local outputs, will be created if it does not exist
- `AWS_ACCESS_ID`: credential for AWS IAM principle, MUST have permissions to manage content in the S3 bucket
- `AWS_ACCESS_SECRET`: corresponding secret for the `AWS_ACCESS_ID` credential
- `AWS_S3_BUCKET`: AWS S3 bucket for published content, MUST exist and will be wholly managed by this application
- `PUBLIC_WEBSITE_ENDPOINT`: WordPress API endpoint for the public website search exporter
- `PUBLIC_WEBSITE_POST_TYPE`: custom WordPress post type for the public website search exporter
- `PUBLIC_WEBSITE_USERNAME`: WordPress user credential for the public website search exporter
- `PUBLIC_WEBSITE_PASSWORD`: WordPress application password for the public website search exporter

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

When published to S3, user metadata is set to indicate the `file_identifier` and `file_revision` of the relevant
[Record Revision](/docs/data-model.md#record-revisions).

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

Combines the outputs of all [Resource Exporters](#resource-exporters) for a set of Records.

The `loads()` method dynamically sets which [Records](/docs/data-model.md#records) to include.

## Site exporters

Site exporters complete the static site by including static resources such as CSS files, pages such as legal policies
and outputs that look across multiple Records.

### Site exporter

`lantern.exporters.site.SiteExporter`

Generates a complete static site by combining outputs from the
[Records Exporter](#records-resource-exporter) and other [Site Exporters](#site-exporters).

The `loads()` method dynamically sets which [Records](/docs/data-model.md#records) to include.

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
- legal policies (accessibility, copyright, cookies and privacy)
- content formatting guide (for abstracts, etc.)

### Public Website search exporter

`lantern.exporters.website.WebsiteSearchExporter`

<!-- pyml disable md028 -->
> [!IMPORTANT]
> This exporter is experimental. Its implementation may change significantly without warning.

> [!IMPORTANT]
> This exporter depends on an external service (WordPress) and does not support local exporting.
<!-- pyml enable md028 -->

Populates a WordPress website with information on items using a custom post type via the WordPress REST API. Intended
to allow users to search for [Selected Items](#public-website-search-criteria) within the
[BAS Public Website](https://www.bas.ac.uk) to aid discovery.

A WordPress plugin is required to register this custom post type and its [Schema](#public-website-search-schema). A
WordPress theme is available to demonstrate how this exporter could work. See the
[Setup](/docs/setup.md#public-website-search) documentation for more information.

#### Public Website search criteria

The public website is not intended as another catalogue of resources, and should only include more significant items
relevant to the public. Items meeting all these criteria are deemed relevant:

1. unrestricted (contain an `unrestricted` access constraint)
   - directing users to Items they can't access is not helpful
2. not superseded by another Item (are not the subject of a `RevisionOf` aggregation in another Item)
   - we don't want to confuse users by showing multiple versions of the same resource

#### Public Website search schema

The WordPress custom post consists of these fields:

<!-- pyml disable md013 -->
| WordPress Field    | Kind | Item Property                  | Type   | Required | Description                                                 |
|--------------------|------|--------------------------------|--------|----------|-------------------------------------------------------------|
| `title`            | Core | `title_plain`                  | String | Yes      | -                                                           |
| `content`          | Core | `summary_html`                 | String | Yes      | Includes HTML formatting                                    |
| `file_identifier`  | Meta | `file_identifier`              | String | Yes      | -                                                           |
| `file_revision`    | Meta | `file_revision`                | String | Yes      | -                                                           |
| `href`             | Meta | `href`                         | String | Yes      | Fully qualified URL to the catalogue item page              |
| `hierarchy_level`  | Meta | `hierarchy_level`              | String | Yes      | ResourceTypeLabel value (field needs renaming)              |
| `publication_date` | Meta | `_record.identification.dates` | String | Yes      | One of revision/publication/creation (field needs renaming) |
| `edition`          | Meta | `edition`                      | String | No       | -                                                           |
| `href_thumbnail`   | Meta | `overview_graphic`             | String | No       | URL to a thumbnail image (if available)                     |
| `source`           | Meta | -                              | String | Yes      | Static identifier for catalogue application (`lantern`)     |
<!-- pyml enable md013 -->
