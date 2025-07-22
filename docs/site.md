# Lantern - Static site

The Data Catalogue website is built as a static site using the [Site Exporter](/docs/exporters.md#site-exporter).

## Site structure

Simplified, primary, top level structure:

```
├── items/
├── records/
└── static/
```

| Path       | Description                                                    | Exporter                                                                                                                                                      |
|------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `items/`   | Rendered [Item](/docs/data-model.md#items) pages               | [HTML](/docs/exporters.md#html-resource-exporter)                                                                                                             |
| `records/` | [Record](/docs/data-model.md#records) files in various formats | [JSON](/docs/exporters.md#json-resource-exporter), [XML](/docs/exporters.md#xml-resource-exporter), [XML HTML](/docs/exporters.md#xml-html-resource-exporter) |
| `static/`  | CSS, images, and other assets                                  | [Site Resources Exporter](/docs/exporters.md#site-resources-exporter)                                                                                         |

Secondary top-level items:

```
├── 404.html
├── favicon.ico
├── -/
├── {aliases}/
└── legal/
```

| Path          | Description                                                                                         | Exporter                                                          |
|---------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `404.html`    | Not found error page                                                                                | [Site Pages](/docs/exporters.md#site-pages-exporter)              |
| `favicon.ico` | Site favicon                                                                                        | [Site Resources](/docs/exporters.md#site-resources-exporter)      |
| `-/`          | Internal (but not secret) site index                                                                | [Site Index](/docs/exporters.md#site-index-exporter)              |
| `{aliases}/`  | [Item Aliases](/docs/data-model.md#item-aliases) redirect pages (for `collections/`, `maps/`, etc.) | [HTML Aliases](/docs/exporters.md#html-aliases-resource-exporter) |
| `legal/`      | Legal policy pages                                                                                  | [Site Pages](/docs/exporters.md#site-pages-exporter)              |

### Record pages structure

```
├── maps/
│     ├── foo/
│     │    └── index.html -> redirecting to /items/123/
│     └── .../
│          └── index.html -> redirecting to /items/.../
├── items/
│     ├── 123/
│     │    └── index.html
│     └── .../
│          └── index.html
└── records/
    ├── 123.html
    ├── 123.json
    ├── 123.xml
    └── ...
```

### Hidden pages structure

```
└── -/
    └── index/
         └── index.html -> 'hidden' index page
```

### Site assets structure

```
├── favicon.ico
└── static/
    ├── css/
    │    └── main.css
    ├── fonts
    │    ├── open-sans-italic.ttf
    │    └── open-sans.ttf
    ├── img
    │    ├── favicon-180.png
    │    ├── favicon-512.png
    │    ├── favicon-mask.png
    │    ├── favicon.ico
    │    ├── favicon.svg
    │    └── safari-pinned-tab.svg
    └── txt
         ├── heartbeat.txt
         └── manifest.webmanifest
```

## Templates configuration

Templates use these options from the app `lantern.Config` class:

- `TEMPLATES_CACHE_BUST_VALUE`: See [Cache busting](#cache-busting)
- `TEMPLATES_ITEM_CONTACT_ENDPOINT`: See [Contact form](#contact-form)
- `TEMPLATES_ITEM_MAPS_ENDPOINT`: See [Extent maps](#extent-maps)
- `TEMPLATES_PLAUSIBLE_DOMAIN`: Plausible site identifier for [Frontend Analytics](/docs/monitoring.md#plausible)

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

## Styling

[Tailwind](https://tailwindcss.com) is used as a base CSS framework, extended to:

- use the colours and fonts from the 2015 [BAS Style Kit](https://style-kit.web.bas.ac.uk)
- use the [Tailwind typography](https://github.com/tailwindlabs/tailwindcss-typography) plugin to style user generated
  content in Records (such as abstracts)
- use the [Tailwind forms](https://github.com/tailwindlabs/tailwindcss-forms) plugin to apply base styles to the
  [Contact Form](#contact-form)

> [!NOTE]
> For practical reasons, the licenced Gill Sans font used for headings in the 2015 Style Kit is not used in this
> Tailwind adaption (falling back to Open Sans).

The `pytailwindcss` package is used to manage a standalone
[Tailwind CLI](https://tailwindcss.com/docs/installation/tailwind-cli) install to avoid needing Node.js.

Input styles are defined in `src/lantern/resources/css/main.css.j2`, which is a Jinja2 template so the search path to
content can be set dynamically.

A search path needs to explicitly defined to ensure the Tailwind compiler finds all classes used in the build static
site, as the [Site Templates](#templates) use interpolation to build class names. This search path needs to be set
dynamically to allow the static site build directory to be set at runtime.

The compiled and minified output MUST be stored as `src/lantern/resources/css/main.css`, as this file will be copied
into the site build directory and is referenced within generated pages.

> [!TIP]
> To recompile the CSS styles, run the `tailwind` [Development Task](/docs/dev.md#development-tasks), which will
> perform all these steps automatically using a temporary site build.

## Cache busting

To ensure the latest CSS and JS files are used by browsers, a query string value is appended to the URLs of static
assets, e.g. `main.css?v=123`. For reproducibility, this value is set to the first 7 characters of the current package
version as a SHA1 hash, e.g. `main.css?v=f053ddb` for version 0.1.0.

> [!NOTE]
> You may need to manually clear caches locally as this value will not change until the next release.

> [!CAUTION]
> Asset references are not automatically amended, make sure any references in templates are suitably configured.

## Scripts

A limited number of scripts are loaded using [Site Macros](#site-macros) for:

- including [Plausible](/docs/monitoring.md#plausible) analytics
- including [Sentry](/docs/monitoring.md#sentry) error monitoring and user feedback
- enabling 'sticky tabs', where the active tab is reflected in the URL fragment
  - this includes setting the active tab on page load if a fragment is present
- enabling 'collapsible' sections, to show or hide additional information for select distribution options

> [!NOTE]
> Scripts are intended to be used sparingly, with functionality implemented using HTML and CSS alone where possible.

## Templates

HTML templates use the [Jinja2](https://jinja.palletsprojects.com/) framework.

### Layout

A base [Jinja2](https://jinja.palletsprojects.com/) layout is available in
`src/lantern/resources/templates/_layouts/base.html.j2`. It a common HTML structure including:

- a `<head>` element with page metadata and include site styles and scripts
- a `<header>` element with site navigation, development phase banner and user feedback link
- a 'content' block for each page's content
- a `<footer>` element with site feedback link and legal information

All pages SHOULD extend from this base layout. Uses of this layout require a `lantern.models.templates.PageMetadata`
class instance passed as a `meta` template context variable.

### Macros

Macros are used extensively within templates, to emulate the component pattern commonly used in JavaScript frameworks.

> [!NOTE]
> Whilst this is an aim, it is applied pragmatically rather than dogmatically and will evolve over time.

#### Common macros

`src/lantern/resources/templates/_macros/site.html.j2` defines macros for:

- classes for layouts, links, buttons, icons and other common elements
- common identifiers for 'back to top' links, user feedback widget triggers, etc.
- low level components such as internal and external links, page and item headers, layout containers, etc.
- higher level components such as item summaries, alerts, etc.

Common macros are intended for use across templates to avoid inconsistencies and simplify maintenance.

#### Site macros

`src/lantern/resources/templates/_macros/site.html.j2` defines:

- a `html_head` macro builds a `<head>` element
  - requires a `PageMetadata` context object
- a `header` macro builds a site wide `<header>` element with side wide navigation and development phase banner
  including site feedback
- a `footer` macro builds a side wide `<footer>` element with site feedback and legal information
  - requires a `PageMetadata` context object

### Item templates

[Items](/docs/data-model.md#items) use a complex template when rendered, with the Item passed as a context variable. It
extends the [Site Layout](#layout) with three parts:

- a top part, consisting of a page header
- a middle part, consisting of a summary section and optional item thumbnail
- a bottom part, with dynamic tabs, where a macro is called based on a series of tab names

All elements across these parts use [Item Macros](#item-macros) to organise and breakdown the template's content.

#### Item macros

`src/lantern/resources/templates/_macros/site.html.j2`, `src/lantern/resources/templates/_macros/tabs.html.j2` and
`src/lantern/resources/templates/_macros/_tabs/*.j2` define a large number of macros to render various parts of an Item.

#### Extent maps

The extent tab within the [Item Templates](#item-templates) includes a map for the Item's geographic extent. These maps
use the [BAS Embedded Maps Service](https://github.com/antarctica/embedded-maps), embedded as an `<iframe>` with a src
URL computed within each Item.

#### Contact form

The contact tab within the [Item Templates](#item-templates) includes a form for users to send item enquires. This is
implemented as a static HTML form with a POST action to a Microsoft Power Automate flow. This routes enquires to a
relevant system and team, then returns a conformation page linking back to the Item.
