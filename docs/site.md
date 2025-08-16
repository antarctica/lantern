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
| `-/`          | Internal (but not secret) pages, such as the site index                                             | *Various*                                                         |
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
     ├── index/
     │    └── index.html -> 'hidden' index page
     └── public-website-search/
          ├── items.json -> temporary static list of aggregation API resources
          └── mockup.html -> temporary results rendering
```

| Path                       | Description                                  | Exporter                                                      |
|----------------------------|----------------------------------------------|---------------------------------------------------------------|
| `-/index/`                 | Hidden index page                            | [Site Index](/docs/exporters.md#site-index-exporter)          |
| `-/public-website-search/` | Temporary public website search items output | [Website Search](/docs/exporters.md#site-pages-exporter) |

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

### Styling guidelines

#### Accessibility

> [!CAUTION]
> This section is Work in Progress (WIP) and not yet complete.

As per the [BAS Style Kit](https://style-kit.web.bas.ac.uk/start/standards-accessibility), and wider UK Government
guidance, the Catalogue site MUST be designed with accessibility in mind.

We maintain a basic accessibility check in `src/lantern/resources/templates/_views/legal/accessibility.html.j2`, which
should be reviewed and revised on a regular basis.

#### Responsive design

As per the [BAS Style Kit](https://style-kit.web.bas.ac.uk/start/standards-accessibility/#responsiveness-and-mobile-first),
the Catalogue site MUST use
[Responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design).

This means designing for the smallest (mobile) viewport by default with Tailwind's modifiers used for larger viewports.
For example, stacking content in a single column by default then using two or more where the viewport allows.

> [!NOTE]
> Whilst mobiles aren't expected to be the primary device type for this site, it should still be usable and functional,
> avoiding common pitfalls such as overflowing images, tables, and needing to pan horizontally.

#### Sizing

Ration based sizing SHOULD be used over fixed sizes (e.g. `w-1/2`).

#### Spacing

A consistent, and constrained, spacing scale SHOULD be used wherever possible:

- small: `-2`
- medium: `-4`
- large: `-8`

Exceptions to this scale MAY and will be made for specific use cases.

Tailwind's `space-x-*` and `space-y-*` classes SHOULD be used for spacing between elements for consistency. Padding
SHOULD be used over margins where possible to limit the number of classes.

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

#### Icons

[Font Awesome Pro 5](https://fontawesome.com/v5/search?o=r) is available for adding icons.

Icons SHOULD be used sparingly. For consistency these icons SHOULD be used where relevant:

- restricted: `far fa-lock`
- external link: `far fa-external-link`

> [!TIP]
> In templates, [Macros](#common-macros) are available to include these icons.

### Style definitions

Styles are defined in `src/lantern/resources/css/main.css.j2`, which is a Jinja2 template to allow the search path for
content to be set dynamically at runtime. This content is needed for the Tailwind compiler to find classes used in the
built static site.

> [!NOTE]
> Using the [Site Templates](#templates) as the content path will not work as they contain interpolated class names
> which the Tailwind compiler cannot resolve, which would lead to missing styles.

Compiled and minified output MUST be stored as `src/lantern/resources/css/main.css`, as this file will be copied into
the site build directory and referenced within generated pages.

> [!TIP]
> See the [Development](/docs/dev.md#updating-styles) documentation for how to update styles.

## Scripts

A limited number of scripts are loaded using [Site Macros](#site-macros) for:

- including [Plausible](/docs/monitoring.md#plausible) analytics
- including [Sentry](/docs/monitoring.md#sentry) error monitoring and user feedback
- enabling 'sticky tabs', where the active tab is reflected in the URL fragment
  - this includes setting the active tab on page load if a fragment is present
- enabling 'collapsible' sections, to show or hide additional information for select distribution options

> [!NOTE]
> Scripts are intended to be used sparingly, with functionality implemented using HTML and CSS alone where possible.

## Cache busting

To ensure the latest CSS and JS files are used by browsers, a query string value is appended to the URLs of static
assets, e.g. `main.css?v=123`. For reproducibility, this value is set to the first 7 characters of the current package
version as a SHA1 hash, e.g. `main.css?v=f053ddb` for version 0.1.0.

> [!NOTE]
> You may need to manually clear caches locally as this value will not change until the next release.

> [!CAUTION]
> Asset references are not automatically amended, make sure any references in templates are suitably configured.

## Templates

HTML templates use the [Jinja2](https://jinja.palletsprojects.com/) framework.

### Templates configuration

Templates use these options from the app `lantern.Config` class:

- `TEMPLATES_CACHE_BUST_VALUE`: See [Cache busting](#cache-busting)
- `TEMPLATES_ITEM_CONTACT_ENDPOINT`: See [Contact form](#contact-form)
- `TEMPLATES_ITEM_MAPS_ENDPOINT`: See [Extent maps](#extent-maps)
- `TEMPLATES_ITEM_VERSIONS_ENDPOINT`: Base URL for constructing links to view
  [Record Revisions](/docs/data-model.md#record-revisions)
- `TEMPLATES_PLAUSIBLE_DOMAIN`: Plausible site identifier for [Frontend Analytics](/docs/monitoring.md#plausible)

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

### Layouts

A set of layouts are available in `src/lantern/resources/templates/_layouts/`. All pages SHOULD extend from the
`base.html.j2` layout.

#### Base layout

The `base.html.j2` layout provides a common HTML structure including:

- a `<head>` element with HTML metadata and imports for site styles and scripts
- a `<header>` element with site navigation, development phase banner and user feedback link
- a `<main>` element containing a 'content' block for each HTML page's content
- a `<footer>` element with site feedback link and legal information

 Uses of this layout require a `lantern.models.templates.PageMetadata` class instance passed as a `meta` template
 context variable.

#### Page templates

The `page.html.j2` template provides a simple page structure for legal policies, error documents, guides, etc.

It extends the parent 'content' block with:

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
extends the [Base Layout](#layouts) with three parts:

1. a top part, consisting of a page header
2. a middle part, consisting of a summary section and optional item thumbnail
3. a bottom part, with dynamic tabs, where a macro is called based on a series of tab names

Elements across these parts use [Item Macros](#item-macros) to organise and breakdown the template's content.

> [!TIP]
> See the [Development](/docs/dev.md#adding-properties-to-item-templates) documentation for how to add new elements.

#### Item macros

These files define a lage number of macros to assemble Items:

- `src/lantern/resources/templates/_macros/site.html.j2`
- `src/lantern/resources/templates/_macros/tabs.html.j2`
- `src/lantern/resources/templates/_macros/_tabs/*.j2`

#### Extent maps

The extent tab within the [Item Templates](#item-templates) includes a map for the Item's geographic extent. These maps
use the [BAS Embedded Maps Service](https://github.com/antarctica/embedded-maps), embedded as an `<iframe>` with a src
URL computed within each Item.

#### Contact form

The contact tab within the [Item Templates](#item-templates) includes a form for users to send item enquires. This is
implemented as a static HTML form with a POST action to a Microsoft Power Automate flow. This routes enquires to a
relevant system and team, then returns a conformation page linking back to the Item.

#### Markdown

Freetext item properties including title, abstract, summary, lineage, etc. support Markdown formatting.

In addition to typical syntax, some additional features are supported:

- tables
- admonitions (notes, tips, warnings, etc.)
- automatically formatting inline URLs and email addresses as links

See the [Formatting Test Record](/tests/resources/records/item_cat_formatting.py) for examples.
