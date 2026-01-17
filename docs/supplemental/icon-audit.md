
# Lantern - Icon Audit (Supplemental)

Summary of icons used across site templates. Compiled and referenced manually to encourage consistency in icon use.

## Uses

- directly in [Templates](/docs/site.md#templates)
- via [Template Macros](/docs/site.md#macros)
- `Tab.icon` properties in `lantern.models.item.catalogue.tabs`
- `lantern.models.item.catalogue.enums.ResourceTypeIcon`

## Reference

### Common icons

For consistency, these icons SHOULD be used where relevant via [Macros](/docs/site.md#macros).

<!-- pyml disable md013 -->
| Use Case                    | Icon Name                       | Icon Style   | Macro                         | Comment                 |
|-----------------------------|---------------------------------|--------------|-------------------------------|-------------------------|
| Linking to an external site | `fa-arrow-up-right-from-square` | `fa-regular` | `com.ext_link_i()`            | As part of larger macro |
| Copy to clipboard           | `fa-copy`                       | `fa-regular` | `com.copyable_path()`         | As part of larger macro |
| Experimental feature        | `fa-flask-round-potion`         | `fa-regular` | `com.experimental_i()`        |                         |
| Restricted feature          | `fa-lock-keyhole`               | `fa-regular` | `com.restricted_i()`          |                         |
| Maintenance feature         | `fa-screwdriver-wrench`         | `fa-regular` | `com.maintenance_i_classes()` |                         |
<!-- pyml enable md013 -->

### Single-use icons

Included directly.

| Component                              | Icon Name                   | Icon Style   | Comment         |
|----------------------------------------|-----------------------------|--------------|-----------------|
| Site Footer (Back to top link)         | `fa-arrow-up`               | `fa-regular` |                 |
| Site Feedback (Submit button)          | `fa-paper-plane-top`        | `fa-regular` |                 |
| Item Contact (Alternative - Post)      | `fa-envelope`               | `fa-regular` |                 |
| Item Contact (Alternative - Email)     | `fa-at`                     | `fa-regular` |                 |
| Item Contact (Alternative - Phone)     | `fa-phone-rotary`           | `fa-regular` |                 |
| Item Contact (Submit button)           | `fa-paper-plane-top`        | `fa-regular` |                 |
| Item Info (Page Size - Portrait)       | `fa-rectangle-vertical`     | `fa-regular` |                 |
| Item Info (Page Size - Landscape)      | `fa-rectangle`              | `fa-regular` |                 |
| Item Authors (ORCID)                   | `fa-orcid`                  | `fa-brands`  |                 |
| Item Licence (Additional restrictions) | `fa-ban`                    | `fa-regular` | in 5 licences   |
| Item Licence (Inaccuracies)            | `fa-circle-question`        | `fa-regular` | in 5 licences   |
| Item Licence (Warrenty)                | `fa-circle-exclamation`     | `fa-regular` | in 5 licences   |
| Item Licence (Allowed use)             | `fa-circle-check`           | `fa-regular` | in 2 licences   |
| Item Licence (Allowed copy)            | `fa-creative-commons-share` | `fa-brands`  | in 2 licences   |
| Item Licence (Allowed remix)           | `fa-creative-commons-remix` | `fa-brands`  | in 2 licences   |
| Item Licence (Attribution)             | `fa-creative-commons-by`    | `fa-brands`  | in 2 licences   |
| Item Licence (Keep attribution)        | `fa-creative-commons-nd`    | `fa-brands`  | in 2 licences   |
| Item Licence (OGL symbol)              | `fa-ogl-symbol`             | `fa-kit`     | Custom ket icon |
| Item Tab (Items)                       | `fa-grid-2`                 | `fa-regular` |                 |
| Item Tab (Data)                        | `fa-cube`                   | `fa-regular` |
| Item Tab (Extent)                      | `fa-expand`                 | `fa-regular` |                 |
| Item Tab (Authors)                     | `fa-user-group-simple`      | `fa-regular` |                 |
| Item Tab (Licence)                     | `fa-file-certificate`       | `fa-regular` |                 |
| Item Tab (Lineage)                     | `fa-scroll`                 | `fa-regular` |                 |
| Item Tab (Related)                     | `fa-diagram-project`        | `fa-regular` |                 |
| Item Tab (AdditionalInfo)              | `fa-square-info`            | `fa-regular` |                 |
| Item Tab (Contact)                     | `fa-comment-captions`       | `fa-regular` |                 |
| Item Tab (Admin)                       | `fa-shield-halved`          | `fa-regular` |                 |
| Item Distribution (Restricted)         | `fa-lock-keyhole`           | `fa-regular` |                 |
| Item Distribution (ArcGIS)             | `fa-layer-plus`             | `fa-regular` |                 |
| Item Distribution (File)               | `fa-file-arrow-down`        | `fa-regular` |                 |
| Item Distribution (Published Map)      | `fa-basket-shopping`        | `fa-regular` |                 |
| Item Distribution (SAN)                | `fa-server`                 | `fa-regular` |                 |
| Item Type (Collection)                 | `fa-shapes`                 | `fa-regular` |                 |
| Item Type (Dataset)                    | `fa-cube`                   | `fa-regular` |                 |
| Item Type (Initiative)                 | `fa-cassette-betamax`       | `fa-regular` |                 |
| Item Type (Product)                    | `fa-map`                    | `fa-regular` |                 |
| Item Type (Paper map product)          | `fa-map`                    | `fa-regular` |                 |

## Fontawesome upgrade

### v5 to v7

Sizing:

- `fa-fw` removed as icons now show as fixed width by default, classes simplified to remove option
- `fa-2x` updated to `fa-2xl`

Styles:

| v5 Style | v7 Style     |
|----------|--------------|
| `far`    | `fa-regular` |
| `fab`    | `fa-brands`  |

Icons:

| v5 Icon                     | v7 Icon                         | Comment                  | Checked |
|-----------------------------|---------------------------------|--------------------------|---------|
| `fa-external-link`          | `fa-arrow-up-right-from-square` |                          | -       |
| `fa-copy`                   | `fa-copy`                       | No change                | -       |
| `fa-flask-potion`           | `fa-flask-round-potion`         |                          | -       |
| `fa-lock-alt`               | `fa-lock-keyhole`               |                          | -       |
| `fa-tools`                  | `fa-screwdriver-wrench`         | Changed to regular style | -       |
| `fa-envelope`               | `fa-envelope`                   | No change                | -       |
| `fa-at`                     | `fa-at`                         | No change                | -       |
| `fa-phone-rotary`           | `fa-phone-rotary`               | No change                | -       |
| `fa-arrow-right`            | `fa-paper-plane-top`            | Icon swapped             | -       |
| `fa-rectangle-portrait`     | `fa-rectangle-vertical`         |                          | -       |
| `fa-rectangle-landscape`    | `fa-rectangle`                  |                          | -       |
| `fa-orcid`                  | `fa-orcid`                      | No change                | -       |
| `fa-ban`                    | `fa-ban`                        | No change                | -       |
| `fa-question-circle`        | `fa-circle-question`            |                          | -       |
| `fa-exclamation-circle`     | `fa-circle-exclamation`         |                          | -       |
| `fa-check-circle`           | `fa-circle-check`               |                          | -       |
| `fa-creative-commons-share` | `fa-creative-commons-share`     | No change                | -       |
| `fa-creative-commons-remix` | `fa-creative-commons-remix`     | No change                | -       |
| `fa-creative-commons-by`    | `fa-creative-commons-by`        | No change                | -       |
| `fa-creative-commons-nd`    | `fa-creative-commons-nd`        | No change                | -       |
| `fa-grip-horizontal`        | `fa-grid-2`                     |                          | -       |
| `fa-cube`                   | `fa-cube`                       | No change                | -       |
| `fa-expand-arrows`          | `fa-expand`                     | Icon swapped             | -       |
| `fa-user-friends`           | `fa-user-group-simple`          | Icon swapped             | -       |
| `fa-file-certificate`       | `fa-file-certificate`           | No change                | -       |
| `fa-scroll-old`             | `fa-scroll`                     | Icon swapped             | -       |
| `fa-project-diagram`        | `fa-diagram-project`            |                          | -       |
| `fa-info-square`            | `fa-square-info`                |                          | -       |
| `fa-comment-alt-lines`      | `fa-comment-captions`           | Icon swapped             | -       |
| `fa-shield-alt`             | `fa-shield-halved`              |                          | -       |
| `fa-layer-plus`             | `fa-layer-plus`                 | No change                | -       |
| `fa-download`               | `fa-file-arrow-down`            | Icon swapped             | -       |
| `fa-shopping-basket`        | `fa-basket-shopping`            |                          | -       |
| `fa-hdd`                    | `fa-server`                     | Icon swapped             | -       |
| `fa-shapes`                 | `fa-shapes`                     | No change                | -       |
| `fa-cube`                   | `fa-cube`                       | No change                | -       |
| `fa-betamax`                | `fa-cassette-betamax`           |                          | -       |
| `fa-map`                    | `fa-map`                        | No change                | -       |
| `fa-map`                    | `fa-map`                        | No change                | -       |
