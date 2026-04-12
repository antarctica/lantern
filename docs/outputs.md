# Lantern - Outputs

Outputs create the contents of a [Catalogue](/docs/architecture.md#catalogues).

They are used in [Sites](/docs/architecture.md#sites) as the source of [Content](/docs/models.md#static-site-content)
passed to [Exporters](/docs/architecture.md#exporters). Outputs also generate [Checks](/docs/monitoring.md#site-checks)
for the contents they produce.

Output classes can be broadly split into:

- individual, record related, outputs (items, etc.)
- global, record related, outputs (indexes, etc.)
- global, non-record related, outputs (supporting pages, styles, scripts, etc.)

## Outputs configuration

> [!NOTE]
> [Config](/docs/config.md) options for Outputs SHOULD be accessed via
> [Site Metadata](/docs/models.md#static-site-metadata) rather than directly.

## Output classes

All outputs inherit from the `lantern.outputs.base.OutputBase` abstract base class and MUST implement its minimal
public interface to:

- define an output name
- generate a list of [`SiteContent`](/docs/models.md#static-site-content) items
- generate a corresponding list of [`Check`](/docs/monitoring.md#site-checks) items to verify for this content

Outputs at the site level SHOULD inherit from the `lantern.outputs.base.OutputSite` abstract base, which includes a
[Site Templates](/docs/site.md#templates) instance for rendering content. These outputs *SHOULD* also include
[Content Metadata](/docs/models.md#static-site-content-metadata) for the site
[Cache Busting](/docs/site.md#cache-busting) value in their content items.

Outputs processing single [Records](/docs/models.md#records) SHOULD inherit from the
`lantern.outputs.base.OutputRecord` abstract base which includes:

- a [Store](/docs/architecture.md#stores) single record access callable
- a `strip_admin` property to control whether
  [Administration Metadata](/docs/models.md#item-administrative-metadata) should be included as part of
  [Trusted Publishing](/docs/architecture.md#trusted-publishing).

These outputs *SHOULD* include [Content Metadata](/docs/models.md#static-site-content-metadata) for the
[Record](/docs/models.md#records) file and revision identifier in their content items.

Outputs processing multiple Records SHOULD inherit from the `lantern.outputs.base.OutputRecords` abstract base which
includes a [Store](/docs/architecture.md#stores) multi record access callable. These outputs *SHOULD* include
[Content Metadata](/docs/models.md#static-site-content-metadata) for a value representing the state/version of the
[Store](/docs/architecture.md#stores) in their content items (e.g. the head revision for a Git based store).

> [!NOTE]
> The `OutputRecords` base class does not include an equivalent `strip_admin` property because these classes are only
> expected to use limited properties from Records (e.g. titles and summaries to build an index). Outputs that use whole
> records SHOUL implement a similar control.

## Site resources output

`lantern.outputs.site_resources.SiteResourcesOutput`

Outputs:

- [CSS](/docs/site.md#styling), [JavaScript](/docs/site.md#scripts), fonts, images (for favicons) and text files
  (for [Monitoring](/docs/monitoring.md)) from the internal `lantern.exporters.resources` module

Jinja2 templates are used for including variables in JavaScript files.

Checks are generated for a limited subset of these resources as indicative tests.

## Site pages output

`lantern.outputs.site_pages.SitePagesOutput`

Outputs HTML pages using [Site Templates](/docs/site.md#item-templates) for:

- 404 error page
- legal policies (accessibility, copyright, cookies and privacy)
- content formatting guide (for abstracts, etc.)
- physical maps purchasing guide

Sharing previews, similar to [Item Pages](/docs/site.md#item-sharing-previews), are enabled via
[Static Site Page Meta](/docs/models.md#static-site-page-meta) with manually defined values.

An additional check for a URL known not to exist is generated to check the 404 handler.

## Site health output

`lantern.outputs.site_health.SiteHealthOutput`

Outputs:

- a [Draft API Health Check](https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check) including a check
  counting the number of Records in the configured Store, rendered from a Python dict

## Site API output

`lantern.outputs.site_health.SiteApiOutput`

> [!WARNING]
> This exporter is experimental.

Outputs:

- a [RFC 9727 API Catalog](https://datatracker.ietf.org/doc/html/rfc9727)
- a raw [OpenAPI](/docs/site.md#openapi-definition) JSON document
- interactive documentation based on this definition built using
  [Scalar](https://guides.scalar.com/scalar/scalar-api-references)

The API Catalog is rendered from a simple Python dict. The OpenAPI definition and documentation are rendered from Jinja
templates.

## Site index output

`lantern.outputs.site_index.SiteIndexOutput`

Outputs:

- a page linking to [Items](/docs/models.md#items) and [Item Aliases](/docs/models.md#item-aliases) formatted using
  [Site Templates](/docs/site.md#page-templates)

> [!NOTE]
> This page is intended as a basic, internal, reference to site content - not a proper, public, homepage.

## Checks output

`lantern.outputs.checks.ChecksOutput`

Processes a set of pre-executed checks into:

- [JSON Data](/docs/monitoring.md#site-checks-data)
- a [HTML Report](/docs/monitoring.md#site-checks-report).

> [!NOTE]
> This output does not generate checks for these content items.

## Catalogue item output

`lantern.outputs.item_html.ItemCatalogueOutput`

Outputs:

- a [Record](/docs/models.md#records) as a [Catalogue Item](/docs/models.md#catalogue-items) HTML pages using
  [Site Templates](/docs/site.md#item-templates)

Intended for consumption by (human) end-users.

Uses a [Store](/docs/architecture.md#stores) select record callable to generate item summaries for related records, and
an `_item_class()` method to determine if a [Special Catalogue Item](/docs/models.md#special-catalogue-items) class
should be used for a Record.

Supports [Trusted Publishing](/docs/architecture.md#trusted-publishing) to include
[Administrative Metadata](/docs/models.md#item-administrative-metadata) in an additional item template tab.

## Catalogue item aliases output

`lantern.outputs.item_html.ItemAliasesOutput`

Outputs:

- [Site Redirects](/docs/models.md#static-site-redirects) for any [Item Aliases](/docs/models.md#item-aliases)
  in a [Record](/docs/models.md#records)

## ISO 19115 record JSON output

`lantern.outputs.record_iso.RecordIsoJsonOutput`

Outputs:

- [Records](/docs/models.md#records) as JSON files using the BAS ISO 19115 schema

Intended for internal consumption within the BAS metadata ecosystem.

## ISO 19115 record XML output

`lantern.outputs.record_iso.RecordIsoXmlOutput`

Outputs:

- [Records](/docs/models.md#records) as ISO 19139 XML files using the BAS ISO 19115 schema

Intended for interoperability for use across wider providers and tools.

> [!NOTE]
> This output includes checks for the [Contents](/docs/models.md#record-checks) of records, such as linked downloads.

## ISO 19115 record HTML output

`lantern.outputs.record_iso.RecordIsoHtmlOutput`

Outputs:

- [Records](/docs/models.md#records) as ISO 19139 XML files with a minimal XSLT transformation applied to format
  present the record as a simple HTML structure

Intended for easier review of ISO metadata by humans.

> [!NOTE]
> The XSLT transformation is applied server side, outputting the resulting HTML/XML to avoid problems with client side
> transformations.

## Web Accessible Folder output

`lantern.outputs.records_waf.RecordsWafOutput`

Outputs:

- a basic, unstyled, [Web Accessible Folder (WAF)](/docs/access.md#web-accessible-folder) (WAF) endpoint linking to ISO
  19139 encoded [Records](/docs/models.md#records) generated by the [Record XML](#iso-19115-record-xml-output) Output

## BAS public website search output

`lantern.outputs.items_bas_website.ItemsBasWebsiteOutput`

Outputs:

- a listing of 'BAS Public Website Catalogue Sync API' resources

Intended to allow users to discover [Selected Items](#public-website-search-criteria) within the
[BAS Public Website](https://www.bas.ac.uk).

These resources consist of:

- information about each item (title, thumbnail, etc.)
- meta information for the Sync API (revision, status, etc.)

> [!NOTE]
> This Sync API is an aggregator for items across BAS Data Catalogues and is maintained outside of this project. It is
> configured to include items from this exporter via the published items listing.
>
> See the [Import 🛡️](https://gitlab.data.bas.ac.uk/uk-pdc/data-infrastructure/pdc-di-scripts/-/blob/master/bas_pdc/import_website_search_records.py)
> and [Export 🛡️](https://gitlab.data.bas.ac.uk/uk-pdc/data-infrastructure/pdc-di-scripts/-/blob/master/bas_pdc/export_website_search_records.py)
> scripts for more information.

### Public Website search criteria

The BAS public website is not intended as another catalogue of resources, and should only include more significant
items relevant to the public. Items meeting all of these criteria are deemed relevant and included:

1. are unrestricted (as [Item Access Levels](/docs/models.md#item-access-levels))
   - as directing users to Items they can't access is not helpful
2. are not superseded by another Item (are not the subject of a `RevisionOf` aggregation in another Item)
   - as we don't want to confuse users by showing multiple versions of the same resource
