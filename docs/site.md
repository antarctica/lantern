# Lantern - Static site

The Data Catalogue website is built as a static site using the [Site Exporter](/docs/exporters.md#site-exporter).

## Site access

The static site is accessible without authentication via a placeholder index page at:

- [data.bas.ac.uk](https://data.bas.ac.uk/-/index) (production)
- [data-testing.bas.ac.uk](https://data-testing.bas.ac.uk/-/index) (integration/testing)

See the [Infrastructure](/docs/infrastructure.md#hosting) documentation for hosting details.

## Site structure

### OpenAPI definition

An [OpenAPI](https://spec.openapis.org/oas/v3.1.0) definition describes the majority of the site structure. It is
available as:

- a JSON document (using the OAS 3.1 schema) at: `/static/json/openapi.json`
- interactive documentation built from this JSON document at: `/guides/api/index.html`

Additional static content such as CSS, JS, fonts and images managed by the
[Site Resources Exporter](/docs/exporters.md#site-resources-exporter) are not listed in this definition.

## HTML metadata

HTML metadata elements are included by the `html_head` [Site Macro](#site-macros) for:

- `viewport` - for enabling [Responsive design](#responsive-design)
- `generator` and `version` - for reporting the application name and version (for troubleshooting)
- `generated` - when a page was generated (for troubleshooting)
- `store-ref` - optional commit associated with the site build's [Store](/docs/architecture.md#stores) (for troubleshooting)
- `description` - page summary (for SEO)

## Site navigation

### Primary navigation

All pages inheriting from the [Base Layout](#base-layout) will include primary navigation links shown in either the
site header or footer (for desktop and mobile respectively).

These links always included:

- the catalogue root
- the [BAS Public Website](https://www.bas.ac.uk)

Additional links MAY be included for significant sections of the site, such as the BAS Maps Catalogue, or relevant
external resources, such as data access guides. Additional links are defined in the `primary_nav_items` variable within
the [Site Macros](#site-macros).

> [!NOTE]
> A high bar SHOULD apply items included in the primary navigation.

## Styling

[Tailwind](https://tailwindcss.com) is used as a base CSS framework, extended to:

- use the colours and fonts from the 2015 [BAS Style Kit](https://style-kit.web.bas.ac.uk)
- use the [Tailwind typography](https://github.com/tailwindlabs/tailwindcss-typography) plugin to style user generated
  content in Records (such as abstracts)
- use the [Tailwind forms](https://github.com/tailwindlabs/tailwindcss-forms) plugin to apply base styles to the
  [Contact Form](#item-enquires)

> [!NOTE]
> For practical reasons, the licenced Gill Sans font used for headings in the 2015 Style Kit is not used in this
> Tailwind adaption (falling back to Open Sans).

The `pytailwindcss` package is used to manage a standalone
[Tailwind CLI](https://tailwindcss.com/docs/installation/tailwind-cli) install to avoid needing Node.js.

### Styling guidelines

#### Accessibility

As per the [BAS Style Kit](https://style-kit.web.bas.ac.uk/start/standards-accessibility), and wider UK Government
guidance, the Catalogue site MUST be designed with accessibility in mind.

We maintain a basic accessibility check in `src/lantern/resources/templates/_views/legal/accessibility.html.j2`, which
SHOULD be reviewed and revised on a regular basis.

#### Responsive design

As per the [BAS Style Kit](https://style-kit.web.bas.ac.uk/start/standards-accessibility/#responsiveness-and-mobile-first),
the Catalogue site MUST use
[Responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design).

This means designing for the smallest (mobile) viewport by default with Tailwind's modifiers used for larger viewports.
For example, stacking content in a single column by default and two or more where the viewport allows.

> [!NOTE]
> Whilst mobiles aren't expected to be the primary device type for this site, designing responsively to avoid common
> pitfalls (such as overflowing content) also helps with accessibility and so MUST be considered.

#### Sizing

Ratio based sizing SHOULD be used over fixed sizes (e.g. `w-1/2`).

#### Spacing

A consistent, and constrained, spacing scale SHOULD be used wherever possible:

- small: `-2`
- medium: `-4`
- large: `-8`

Exceptions to this scale MAY and will be made for specific use cases.

Tailwind's `space-x-*` and `space-y-*` classes SHOULD be used for spacing between elements for consistency. Padding
SHOULD be used over margins where possible to limit `the number of classes.

> [!TIP]
> Run the `css-audit` [Development Task](/docs/dev.md#development-tasks) to check currently used classes in templates.

#### Dark mode

Consideration SHOULD be given the user's colour preference by providing a dark mode using the Tailwind `dark:` modifier.

Common pairings, which SHOULD be used and re-enforced where sensible, are:

| Light Mode | Dark Mode |
|------------|-----------|
| `black`    | `white`   |
| `*-100`    | `*-900`   |
| `*-500`    | `*-300`   |

#### Colour audit

A [Colour Audit](/docs/supplemental/colour-audit.md) and reference is manually maintained to coordinate and constrain
the range of colours used across the site. Update this document if changing or adding colours.

> [!TIP]
> Run the `css-audit` [Development Task](/docs/dev.md#development-tasks) to check currently used classes in templates.

### Style definitions

Styles are defined in `src/lantern/resources/templates/_assets/css/main.css.j2`, which is a Jinja2 template to allow
the search path for content to be set dynamically at runtime. This content is needed for the Tailwind compiler to find
classes used in the built static site.

> [!NOTE]
> Using the [Site Templates](#templates) as the content path will not work, as they contain interpolated class names
> the Tailwind compiler cannot resolve, causing missing styles.

Compiled and minified output MUST be stored as `src/lantern/resources/css/main.css`, as this file will be copied into
the site build directory and referenced within generated pages.

> [!TIP]
> See the [Development](/docs/dev.md#updating-styles) documentation for how to update styles.

## Icons

[Font Awesome Pro 7](https://fontawesome.com/v7/search?o=r) MAY be used for adding icons.

Font Awesome is included via a hosted [Kit](https://docs.fontawesome.com/web/setup/use-kit).

> [!IMPORTANT]
> Icons SHOULD be used sparingly and MUST NOT exclusively convey context or meaning.

### Icons audit

An [Icon Audit](/docs/supplemental/icon-audit.md) and reference is manually maintained to coordinate and constrain
icons used across the site. Update this document if changing or adding icons.

> [!TIP]
> Run the `icons-audit` [Development Task](/docs/dev.md#development-tasks) to check currently used icons in templates
> and a list of additional places to manually check.

## Scripts

A set of site wide scripts are included using [Site Macros](#site-macros) for:

- [Sentry](/docs/monitoring.md#sentry) error monitoring and user feedback
- [Plausible](/docs/monitoring.md#plausible) analytics
- [Cloudflare Turnstile](#bot-protection) bot protection for forms
- [Progressive Enhancements](#enhancements-script) for various bits of functionality

> [!NOTE]
> Functionality SHOULD be preferably implemented using HTML and CSS alone where practical. Scripts SHOULD be used for
> progressive enhancement and support graceful degradation where possible.

First party JavaScript are defined in `src/lantern/resources/templates/_assets/js/*`, which are Jinja2 templates to
allow using variables from [Common](#common-macros) and [Asset](#asset-macros) macros.

Rendered versions of these templates MUST be stored in `src/lantern/resources/js/`, as this directory will be copied
into the site build directory, and referenced within generated pages.

> [!TIP]
> See the [Development](/docs/dev.md#updating-scripts) documentation for how to update scripts.

### Graceful degradation

Where functionality relies on JavaScript, templates SHOULD:

- use a `<noscript>` element to show a static fallback of some content for users without JavaScript
- use `class="{{ com.show_js_only() }} ..."` on the full/interactive version which will add a `.hidden` class

The [Enhancements](#enhancements-script) script will remove this `.hidden` class from any elements, and the browser
will automatically hide any `<noscript>` elements, where JavaScript is available.

This approach is used for distribution options for example, where collapsible sections are used to hide optional data
where possible. Where JavaScript is disabled, `<noscript>` elements show the full content statically as a fallback.

### Enhancements script

A set of targeted enhancements to:

- enable 'sticky tabs' where:
  - the active tab is set in the URL fragment when switching tabs
  - an initial tab is switched to automatically if a tab fragment is present on page load
- enable progressive disclosure via simple collapsible sections
  - used for [Site Feedback](#user-feedback) and some item distribution options (e.g. feature services)
- show content where JavaScript is enabled, as an 'else' to `<noscript>`
- process feedback from the [User Feedback](#user-feedback) widget when submitted

## Cache busting

To ensure the latest CSS and JS files are used by browsers, a query string value is appended to the URLs of static
assets, e.g. `main.css?v=123`. For reproducibility, this value is set to the first 7 characters of the current package
version as a SHA1 hash, e.g. `main.css?v=f053ddb` for version 0.1.0.

<!-- pyml disable md028 -->
> [!IMPORTANT]
> Asset references are not automatically changed. Rebuild the site after a release to update references.

> [!TIP]
> You may need to manually clear caches locally when developing, as this value will not change until the next release.
<!-- pyml enable md028 -->

## Security

### Bot protection

For features vulnerable to spam and abuse, such as the [Item Enquires](#item-enquires),
[Cloudflare Turnstile](https://www.cloudflare.com/en-gb/application-services/products/turnstile/) is used to
distinguish humans from bot agents. Typically, this check is non-interactive but may require the user to check a box.

## User feedback

A custom form for collecting [User Feedback](/docs/monitoring.md#user-feedback) via Sentry is included on all pages
via a [Site Macro](#site-macros) included in the [Base Layout](#base-layout).

## Templates

HTML templates use the [Jinja2](https://jinja.palletsprojects.com/) framework.

### Templates configuration

Templates use these options from the app `lantern.Config` class:

- `TEMPLATES_CACHE_BUST_VALUE`: See [Cache busting](#cache-busting)
- `TEMPLATES_ITEM_CONTACT_ENDPOINT`: See [Contact form](#item-enquires)
- `TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY`: Turnstile site key for item form [Bot Protection](#bot-protection)
- `TEMPLATES_ITEM_MAPS_ENDPOINT`: See [Extent maps](#item-extent-maps)
- `TEMPLATES_ITEM_VERSIONS_ENDPOINT`: Base URL for constructing links to view
  [Record Revisions](/docs/data-model.md#record-revisions)
- `TEMPLATES_PLAUSIBLE_DOMAIN`: Plausible site identifier for [Frontend Analytics](/docs/monitoring.md#plausible)

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

### Layouts

A set of layouts are available in `src/lantern/resources/templates/_layouts/`. All pages SHOULD ultimately extend the
[Base Layout](#base-layout). Most pages SHOULD extend from the [Main Layout](#main-layout).

#### Base layout

The `base.html.j2` layout provides a common HTML structure including:

- a `<head>` element with HTML metadata and imports for site styles and scripts
- a `<body>` element with:
  - a `<header>` element with site navigation, development phase banner and user feedback link
  - a 'content' block for each HTML page's content with minimal padding
  - a `<footer>` element with site feedback link and legal information

> [!NOTE]
> This layout requires a [Site Context](/docs/data-model.md#static-site-metadata) instance as a `meta` template context
> variable.

#### Main layout

The `main.html.j2` layout extends the [Base Layout](#base-layout) with:

- a `<main>` element containing a 'main' block for each HTML page's content, wrapped in a container at a standard
  width

#### Page templates

The `page.html.j2` template extends the [Main Layout](#main-layout) providing a simple page structure for legal
policies, error documents, guides, etc.

It extends the parent 'main' block with:

- a page header
- a 'page_content' block for each page's content

> [!IMPORTANT]
> Child templates MUST set a `main_title` variable for setting the page header title. E.g.:
>
> ```html
> {% extends "_layouts/page.html.j2" %}
>
> {% set header_main = "Foo" %}
>
> {% block page_content %}
>  <p>...</p>
> {% endblock %}
> ```

### Macros

Macros are used extensively within templates, to emulate the component pattern commonly used in JavaScript frameworks.

> [!NOTE]
> Whilst this is an aim, it is applied pragmatically rather than dogmatically and will evolve over time.

#### Common macros

`src/lantern/resources/templates/_macros/common.html.j2` defines macros for:

- classes for layouts, links, buttons, tables, icons and other common elements
- common identifiers for 'back to top' links, user feedback widget triggers, etc.
- low level components such as internal and external links, page and item headers, layout containers, etc.
- higher level components such as item summaries, alerts, etc.

Common macros are intended for use across templates to avoid inconsistencies and simplify maintenance.

#### Asset macros

`src/lantern/resources/templates/_macros/assets.html.j2` defines macros for:

- JavaScript snippets for [Progressive Enhancements](#enhancements-script)

#### Site macros

`src/lantern/resources/templates/_macros/site.html.j2` defines:

- a `primary_nav_items` variable for [Primary Navigation](#primary-navigation)
- a `html_head` macro builds a `<head>` element
  - requires a [Site Metadata](/docs/data-model.md#static-site-metadata) context object
- a `header` macro builds a site wide `<header>` element with side wide navigation and development phase banner
  including site feedback
- a `footer` macro builds a side wide `<footer>` element with site feedback and legal information
  - requires a [Site Metadata](/docs/data-model.md#static-site-metadata) context object

### Item templates

[Items](/docs/data-model.md#items) use a complex template when rendered, with the Item passed as a context variable. It
extends the [Main Layout](#main-layout) with:

1. a top part, consisting of a page header
2. a middle part, consisting of a summary section and optional item thumbnail
3. a bottom part, with dynamic tabs, where a macro is called based on a series of tab names

Elements across these parts use [Item Macros](#item-macros) to organise and breakdown the template's content.

> [!TIP]
> See the [Development](/docs/dev.md#adding-properties-to-items) documentation for how to add new elements.

#### Item macros

Macros in these templates are used to assemble Items:

- `src/lantern/resources/templates/_macros/site.html.j2`
- `src/lantern/resources/templates/_macros/tabs.html.j2`
- `src/lantern/resources/templates/_macros/_tabs/*.j2`

#### Item downloads

The data tab within the [Item Templates](#item-templates) shows any available downloads, services or other distribution
methods (collectively distribution items) in a grid-based table layout. Each grid row consists of:

- columns for:
  - a distinguishing label: which may be the file format if unique or a custom value
  - an optional download size: automatically formatted with appropriate units if measured in bytes
  - an action link or button: either to an external URL or to trigger a collapsible section
- optional descriptive text: shown full-width without any HTML formatting
- an optional collapsible section, shown full-width using a template snippet

> [!NOTE]
> It isn't intended for descriptive text and a collapsible section to be used together.

Distribution items are defined by the `lantern.models.item.catalogue.distributions.Distribution`) class with properties
for the *label*, *action*, *description*, etc. Subclasses for file and service based options (e.g. feature services)
set common defaults.

For file based options, *label* and *description* properties map to the *title* and *description* if set in the
transfer option online resource. Where the *title* is not set, the file format is used as a default.

> [!IMPORTANT]
> For consistency, file based options should use the file format as the online title using values defined by the
> `lantern.models.item.catalogue.enums.DistributionType` enum.

For service based options, *labels* are hard-coded to the service type name and *descriptions* are disabled as
collapsible sections are used for showing service endpoints and usage instructions.

#### Item extent maps

The extent tab within the [Item Templates](#item-templates) includes a map for the Item's geographic extent. These maps
use the [BAS Embedded Maps Service](https://github.com/antarctica/embedded-maps), embedded as an `<iframe>` with a src
URL computed within each Item.

#### Item enquires

The contact tab within the [Item Templates](#item-templates) includes a form for users to send item enquires. These
forms submit to a Microsoft Power Automate flow which routes enquires to the relevant team and returns a result page to
the user.

To protect against spam and abuse, the form includes a hidden [Bot Protection](#bot-protection) field, validated in the
Power Automate flow. Where this validation fails, the flow returns an error page to the user.

#### Item Markdown

Free-text item properties including title, abstract, summary, lineage, etc. support Markdown formatting.

In addition to typical syntax, some additional features are supported:

- tables
- admonitions (notes, tips, warnings, etc.)
- automatically formatting inline URLs and email addresses as links

The guide in `src/resources/templates/_views/-/formatting.html.j2` SHOULD be maintained to show end-users how supported
formatting will appear.

For development, use the [Formatting Test Record](/tests/resources/records/item_cat_formatting.py) for more exciting
examples.

#### Item Sharing previews

Item pages include metadata to improve how items appear when shared on social media and messaging platforms:

- [Open Graph](https://ogp.me) is included as part of [Site Metadata](/docs/data-model.md#static-site-metadata)
- limited [Schema.org](https://schema.org) (JSON-LD) metadata is implemented via and for Microsoft Teams
