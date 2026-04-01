# Lantern - Colour Audit (Supplemental)

> [!NOTE]
> This page is specific to the [BAS Data Catalogue](/docs/architecture.md#bas-data-catalogue).

Summary of colours used across site templates. Compiled and referenced manually to encourage consistency in colour use.

## Distinct colours

Greyscale:

| Colour      | Source               | Comment                     |
|-------------|----------------------|-----------------------------|
| `white`     | BAS Style Kit 2015   | -                           |
| `grey-50`   | BAS Style Kit 2015   | Used once for code in prose |
| `grey-100`  | BAS Style Kit 2015   | -                           |
| `grey-300`  | BAS Style Kit 2015   | -                           |
| `grey-500`  | BAS Style Kit 2015   | -                           |
| `grey-700`  | BAS Style Kit 2015   | -                           |
| `grey-900`  | BAS Style Kit 2015   | -                           |
| `grey-950`  | BAS Style Kit 2015   | -                           |
| `black`     | BAS Style Kit 2015   | -                           |

Colours:

| Colour         | Source             | Comment                                     |
|----------------|--------------------|---------------------------------------------|
| `sky-blue-50`  | BSK-2025           | -                                           |
| `sky-blue-500` | BAS Style Kit 2015 | Contventional 'information' context         |
| `blue-300`     | BSK-2015           | Used once for 'primary' buttons hover state |
| `blue-500`     | BSK-2025           | -                                           |
| `yellow-500`   | BAS Style Kit 2015 | Contventional 'warning' context             |
| `yellow-700`   | BAS Style Kit 2015 | Used once for 'warning' buttons hover state |
| `red-500`      | BAS Style Kit 2015 | Contventional 'danger' context              |
| `pink-500`     | BAS Style Kit 2015 | Used for alpha development status           |
| `green-500`    | BAS Style Kit 2015 | Contventional 'success' context             |
| `mauve-500`    | BAS Style Kit 2015 | Used once for 'important' admonition        |

## Reference

<!-- pyml disable md013 -->
| Component                      | Aspect                 | Light        | Dark         | Comment                         |
|--------------------------------|------------------------|--------------|--------------|---------------------------------|
| Body                           | Text                   | grey-900     | grey-100     |                                 |
|                                | Background             | white        | grey-950     |                                 |
| Navbar                         | Text                   | white        | white        | For 'brand' text specifically   |
|                                | Background             | blue-500     | blue-500     | Equal                           |
| Development Status             | Text                   | white        | grey-950     |                                 |
|                                | Background             | pink-500     | pink-500     |                                 |
| Footer                         | Text                   | grey-100     | grey-100     |                                 |
|                                | Background             | grey-950     | black        |                                 |
| Footer (Links)                 | Text                   | white        | white        | Equal                           |
| Page Header                    | Border                 | grey-100     | grey-900     |                                 |
| Page Header (Sub-text)         | Text                   | grey-500     | grey-300     |                                 |
| Page Header (Title)            | Text                   | blue-500     | white        |                                 |
| Item Summary                   | Background             | sky-blue-50  | grey-900     |                                 |
| Item Restricted                | Background             | yellow-500   | yellow-500   |                                 |
| Item Tabs                      | Text                   | grey-500     | grey-300     |                                 |
|                                | Background (Hover)     | sky-blue-50  | grey-900     |                                 |
|                                | Text (Hover)           | blue-500     | grey-100     |                                 |
|                                | Border                 | grey-300     | grey-500     |                                 |
|                                | Border (Bottom, Hover) | grey-300     | grey-500     |                                 |
| Item Tabs (Active Tab)         | Text                   | grey-900     | grey-100     | To appear non-interactive       |
|                                | Text (Hover)           | grey-900     | grey-100     | To appear non-interactive       |
|                                | Background             | white        | grey-950     | To appear non-interactive       |
|                                | Background (Hover)     | white        | grey-950     | To appear non-interactive       |
|                                | Border (Bottom)        | white        | grey-950     | To appear invisible             |
|                                | Border (Bottom, Hover) | white        | grey-950     | To appear invisible             |
| Item Tabs (Tab Body)           | Border                 | grey-300     | grey-500     |                                 |
| Links                          | Text                   | blue-500     | white        |                                 |
| Common Border                  | Border                 | grey-100     | grey-700     |                                 |
| Item Summaries (Fragments)     | Text                   | grey-500     | grey-300     |                                 |
|                                | Text (Dividers)        | grey-100     | grey-700     |                                 |
| Definition List Item           | Text                   | black        | white        | For extra contrast in dark mode |
| Prose (Body)                   | Text                   | grey-900     | grey-100     |                                 |
| Prose (Heading)                | Text                   | grey-900     | grey-100     |                                 |
| Prose (Lead)                   | Text                   | grey-900     | grey-100     |                                 |
| Prose (Links)                  | Text                   | blue-500     | white        |                                 |
| Prose (Bold)                   | Text                   | grey-900     | grey-100     |                                 |
| Prose (Counters)               | Text                   | grey-500     | grey-300     |                                 |
| Prose (Bullets)                | Text                   | grey-900     | grey-100     |                                 |
| Prose (HR)                     | Border                 | grey-300     | grey-500     |                                 |
| Prose (Quotes)                 | Text                   | grey-900     | grey-100     |                                 |
|                                | Border                 | grey-300     | grey-500     |                                 |
| Prose (Captions)               | Text                   | grey-500     | grey-300     |                                 |
| Prose (Code)                   | Text                   | grey-950     | grey-50      |                                 |
| Prose (Keyboard)               | Text                   | grey-900     | grey-100     |                                 |
|                                | Shadow                 | grey-300     | grey-500     |                                 |
| Prose (Pre-formatted)          | Code (Text)            | grey-100     | grey-900     | Inverted                        |
|                                | Background             | grey-900     | grey-100     | Inverted                        |
| Prose (Table Headers)          | Border                 | grey-300     | grey-500     |                                 |
| Prose (Table Rows)             | Border                 | grey-300     | grey-500     |                                 |
| Alerts (Success)               | Border                 | green-500    | green-500    | Equal                           |
| Alerts (Warning)               | Border                 | yellow-500   | yellow-500   | Equal                           |
| Alerts (Danger)                | Border                 | red-500      | red-500      | Equal                           |
| Alerts (Info)                  | Border                 | sky-blue-500 | sky-blue-500 | Equal                           |
| Alerts (Experimental)          | Border                 | mauve-500    | mauve-500    | Equal                           |
| Admonition (Note)              | Border                 | sky-blue-500 | sky-blue-500 | Equal                           |
| Admonition (Tip)               | Border                 | green-500    | green-500    | Equal                           |
| Admonition (Important)         | Border                 | mauve-500    | mauve-500    | Equal                           |
| Admonition (Warning)           | Border                 | red-500      | red-500      | Equal                           |
| Admonition (Caution)           | Border                 | yellow-500   | yellow-500   | Equal                           |
| Forms (Input)                  | Text                   | -            | grey-white   | Light mode set by forms plugin  |
|                                | Background             | -            | grey-900     | Light mode set by forms plugin  |
|                                | Border                 | grey-300     | grey-500     |                                 |
| Forms (Textarea)               | Text                   | -            | grey-white   | Light mode set by forms plugin  |
|                                | Background             | -            | grey-900     | Light mode set by forms plugin  |
|                                | Border                 | grey-300     | grey-500     |                                 |
| Buttons (Default)              | Text                   | `black`      | `black`      | Equal                           |
| Buttons (Default)              | Text (Hover)           | `white`      | `white`      | Equal                           |
|                                | Background             | `grey-100`   | `grey-100`   | Equal                           |
|                                | Background (Hover)     | `grey-300`   | `grey-300`   | Equal                           |
| Buttons (Primary)              | Text                   | `black`      | `black`      | Equal                           |
|                                | Text (Hover)           | `white`      | `white`      | Equal                           |
|                                | Background             | `blue-500`   | `blue-500`   | Equal                           |
| Tables                         | Border                 | `grey-100`   | `grey-900`   |                                 |
| Tables (Header)                | Background             | `grey-100`   | `grey-900`   |                                 |
|                                | Border (Bottom)        | `grey-500`   | `grey-300`   |                                 |
| Tables (Body)                  | Border (Bottom)        | `grey-100`   | `grey-900`   |                                 |
| Item Downloads (Descriptions)  | Text                   | `grey-500`   | `grey-300`   |                                 |
| Feedback Widget                | Border                 | `grey-300`   | `grey-500`   |                                 |
|                                | Background             | `white`      | `grey-950`   |                                 |
|                                | Text                   | `grey-900`   | `grey-100`   |                                 |
| Feedback Widget (Close button) | Text                   | `grey-500`   | `grey-300`   |                                 |
|                                | Text (Hover)           | `grey-700`   | `grey-700`   | Equal                           |
<!-- pyml enable md013 -->

## Change log

### 0.6.x

#### Changes for BAS Style Kit 2025

Includes non-colour changes to typography.

Summary:

- font weights set to 'normal' for body (from undefined) and 'semibold' (from bold) for headers and related elements
- item summary background, item title, links and primary buttons aligned with (BAS) blue variants

| Element           |                    | Style                 | Variant | Pre               | Post                 |
|-------------------|--------------------|-----------------------|---------|-------------------|----------------------|
| Body              | Text               | Font Family           | -       | Open Sans         | Work Sans            |
|                   |                    | Weight                | -       | -                 | Normal               |
| Links             | Text               | Colour                | Light   | text-sky-blue-500 | text-blue-500        |
| Prose             | Links              | Colour                | Light   | text-sky-blue-500 | text-blue-500        |
|                   |                    |                       | Dark    | text-sky-blue-300 | text-white           |
|                   | Headings           | Weight                | -       | Bold              | Semibold             |
| Form Input        | Label              | Weight                | -       | Bold              | Semibold             |
| Page Header       | Title              | Weight                | -       | Normal            | Semibold             |
|                   |                    | Colour                | Light   | -                 | text-blue-500        |
| Definition List   | Term               | Weight                | -       | Bold              | Semibold             |
| Table             | Header             | Weight                | -       | Bold              | Semibold             |
| Button (Primary)  | Background         | Colour                | Light   | bg-turquoise-500  | bg-blue-500          |
| Button (Primary)  | Background         | Colour                | Dark    | bg-turquoise-500  | bg-blue-500          |
|                   | Background (Hover) | Colour                | Light   | bg-turquoise-700  | bg-blue-300          |
|                   | Background (Hover) | Colour                | Dark    | bg-turquoise-700  | bg-blue-300          |
| Button (Default)  | Text (Hover)       | Colour                | Light   | -                 | text-white           |
|                   |                    |                       | Dark    | text-sky-blue-300 | text-white           |
|                   |                    | Underline (thickness) | -       | -                 | 2                    |
| Admonition        | Title              | Weight                | -       | Bold              | Semibold             |
| Site header       | Text               | Weight                | -       | Bold              | Semibold             |
|                   |                    | Size                  | -       | Large             | 2XL                  |
|                   | Background         | Colour                | Light   | bg-grey-950       | bg-blue-500          |
|                   |                    |                       | Dark    | bg-black          | (Removed, now equal) |
| Site dev phase    | Text               | Weight                | -       | Bold              | Semibold             |
| Site footer       | Sub-heading        | Weight                | -       | Normal            | Semibold             |
|                   | Link               | Colour                | Light   | text-sky-blue-300 | (Removed)            |
|                   |                    |                       | Dark    | text-sky-blue-500 | (Removed)            |
| Site feedback     | Heading            | Weight                | -       | Bold              | Semibold             |
| Item summary      | Background         | Colour                | Light   | bg-grey-100       | bg-sky-blue-50       |
|                   | Headings           | Weight                | -       | Bold              | Semibold             |
| Item tabs         | Background (Hover) | Colour                | Light   | bg-grey-100       | bg-sky-blue-50       |
|                   | Text (Hover)       | Colour                | Light   | text-sky-blue-500 | text-blue-500        |
|                   | Text (Hover)       | Colour                | Dark    | text-sky-blue-300 | text-grey-100        |
| Related items     | Header             | Weight                | -       | Normal            | Semibold             |
|                   |                    | Size                  | -       | Base              | XL                   |
| Authors tab       | Strong             | Weight                | -       | Bold              | Semibold             |
| Licence tab       | Strong             | Weight                | -       | Bold              | Semibold             |
| Contact tab       | Alternate heading  | Weight                | -       | Bold              | Semibold             |
| Index page        | Header item        | Weight                | -       | Bold              | Semibold             |
| Verification page | Header item        | Weight                | -       | Bold              | Semibold             |
