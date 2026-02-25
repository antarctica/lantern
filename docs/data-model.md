# Lantern - Data Model

## Records

### Base records

Records are a partial representation of the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139)
information model implemented as a base data class (`lantern.lib.metadata_library.models.record.Record`). They
generically describe resources (maps [products], datasets, collections, etc.).

<!-- pyml disable md028 -->
> [!NOTE]
> The base Records model is considered part of the BAS Metadata Library. See the
> [Library](/docs/libraries.md#bas-metadata-library) docs for more information.

> [!NOTE]
> Unless stated otherwise, references to 'Records' elsewhere refer to the [`RecordRevision`](#record-revisions) class.
<!-- pyml enable md028 -->

### Catalogue records

Catalogue Records represent [Records](#records) within the Data Catalogue specifically as a `Record` subclass
(`lantern.models.record.Record`). This subclass SHOULD be used for any additional subclasses within the Catalogue.

Catalogue Records extend the [Base Record](#base-records) class by implementing the Catalogue's
[Record Requirements](#record-requirements).

### Record revisions

Record Revisions represent [Records](#records) at a particular point in time indicated by a revision identifier.

Revision identifiers are a local addition and not part of the ISO 19115 information model. Identifiers SHOULD come from
a version Control system (VCS) such as Git. Identifiers MUST be unique within the history of each Record but MAY be
shared across multiple Records, to represent a coordinated set of changes for example (i.e. a records  changeset).

Record Revisions are implemented as a [Catalogue Record](#catalogue-records) subclass
(`lantern.models.record.revision.RecordRevision`) adding a `file_revision` property.

> [!NOTE]
> Unless stated otherwise, references to 'Records' elsewhere in this documentation refer to the `RecordRevision` class.

### Record requirements

In addition to [Record Validation](/docs/libraries.md#record-validation), the Data Catalogue requires all records:

- MUST use a UUID value for the `file_identifier`:
  - to ensure resources can be distinguished without relying on a value such as title that may change or not be unique
  - to ensure resource identifiers and aliases are distinct and can't be ambiguous
- MUST include an `identification.identifier`, as per [1]
  - to determine if a record is part of the Catalogue
- MUST include an `identification.identifier.contacts.*.contact` with at least the 'pointOfContact' role
  - for use with the item contact tab
- MUST use unique identifiers for extents
- MUST structure any [Aliases](#item-aliases) as below if included:
  - MUST use values in the form: `{prefix}/{value}`
  - MUST use an allowed prefix for each hierarchy level, as per [2]
  - MUST NOT use UUIDs in values (to avoid conflicts with `file_identifier` values)
  - MUST set the `href` property to `https://data.bas.ac.uk/{alias}` (e.g. `https://data.bas.ac.uk/collections/foo`)

These requirements are enforced by the `validate()` method in the [Catalogue Record](#catalogue-records) class.

<!-- pyml disable md028 -->
> [!NOTE]
> Whilst not required, records without
> [Administration Metadata](/docs/libraries.md#record-administrative-metadata) will be interpreted as
> [Restricted Items](#item-access-levels) when processed, and is therefore typically also included.

> [!CAUTION]
> The catalogue does not enforce metadata access constraints if set.
<!-- pyml enable md028 -->

[1]

- identifier: `{file_identifier}`
- href: `https://data.bas.ac.uk/items/{file_identifier}`
- namespace: `data.bas.ac.uk`

[2]

| Hierarchy level           | Allowed Prefixes |
|---------------------------|------------------|
| `collection`              | `collections`    |
| `dataset`                 | `datasets`       |
| `initiative`              | `projects`       |
| `product`                 | `products`       |
| `mapProduct` (local)      | `maps`           |
| `paperMapProduct` (local) | `maps`           |
| `webMapProduct` (local)   | `maps`           |

## Items

Items are wrappers around Records to provide convenience properties and methods to access an underlying Record's
configuration for use in a specific context.

> [!NOTE]
> Items do not follow a formal specification and are not interoperable outside of this project.

### Item base

The `lantern.models.item.base.ItemBase` Python class contains common properties and methods across all item subclasses.

For example:

- `Item.citation_html` returns an HTML formatted version of `identification.other_citation_details`, if set
- `Item.kv` returns a dict of key-values if `identification.supplemental_information` is a suitable JSON encoded object
- `Item.resource_access` returns a local access type enumeration value by parsing any resource permissions set in
  optional [Administrative Metadata](#item-administrative-metadata)

### Catalogue items

Catalogue Items (`lantern.models.item.catalogue.ItemCatalogue`) are tightly coupled to the Data Catalogue and its user
interface. Features include:

- properties organised under classes for each UI tab (including logic to determine whether a tab should be shown)
- local enums mapping Record properties to UI values for improved readability
- a `render()` method to output an HTML page for each item
- classes (`lantern.models.item.catalogue.distributions`) for processing distribution options for the catalogue UI
- an item summary implementation (`lantern.models.item.catalogue.elements.ItemSummaryCatalogue`)

#### Catalogue item limitations

> [!WARNING]
> This section is Work in Progress (WIP) and may not be complete/accurate.

Supported properties (references not normative or exhaustive):

- `file_identifier`
- `file_revision`
- `hierarchy_level`
- `metadata.date_stamp`
- `metadata.metadata_standard.name`
- `metadata.metadata_standard.version`
- `metadata.constraints[type='usage', restriction_code='licence']` (only where a `href` is included)
- `reference_system_info`
- `identification.citation.title`
- `identification.citation.dates`
- `identification.citation.edition`
- `identification.citation.contacts` ('author' and single 'point of contact' roles only, excludes `contact.position`)
- `identification.citation.series`
- `identification.citation.identifiers[namespace='doi']`
- `identification.citation.identifiers[namespace='isbn']`
- `identification.citation.identifiers[namespace='alias.data.bas.ac.uk']`
- `identification.abstract`
- `identification.aggregations` (only as below)
  - 'part of' (items in collections)
  - item and collection cross-references
  - supersedes (not 'superseded by')
  - 'one side of' (physical maps only)
  - 'opposite side of' (physical maps only)
- `identification.constraints[type='usage', restriction_code='licence']`
- `identification.maintenance`
- `identification.extent` (single bounding temporal and geographic bounding box extent only)
- `identification.other_citation_details`
- `identification.graphic_overviews` ('overview' image only)
- `identification.spatial_resolution`
- `identification.supplemental_information` ('physical_size_*' and 'admin_meta' KV's only)
- `data_quality.lineage.statement`
- `data_quality.domain_consistency`
- `distribution.distributor.format` (`format` and `href` only)
- `distribution.distributor.transfer_option` (except `online_resource.protocol`)
- [Administrative Metadata](#item-administrative-metadata) (in trusted contexts only)

Unsupported properties (references not normative or exhaustive):

- `identification.purpose` (except as used in ItemSummaries)
- `identification.citation.identifiers` (except `'doi'`, `'isbn'`, `'alias.data.bas.ac.uk'` namespaces)

Intentionally omitted properties (references not normative or exhaustive):

- `*.character_set` (not useful to end-users, present in underlying record)
- `*.language` (not useful to end-users, present in underlying record)
- `*.online_resource.protocol` (not useful to end-users, present in underlying record)
- `*.constraints[type='access']` (not trustworthy, see [Item Access](#item-access-levels))
- `distribution.distributor` (not useful to end-users)

### Special catalogue items

To support more complex use-cases `ItemCatalogue` subclasses can be used to implement special handling for items.

Special catalogue items classes MUST implement a public `matches` class method returning a boolean indicating whether
the special class applies to a given Record.

Suitable logic needs to be implemented where Records are processed into items to call these `matches` methods to
determine which Catalogue Item class or subclass to use.

#### Physical map items

Physical maps are represented by a trio of Records, one per side plus a third Record for the overall map itself.
Aggregations are used to associate the records together with the local 'physicalReverseOf' aggregation association
(`lantern.lib.metadata_library.models.record.enums.AggregationAssociationCode.PHYSICAL_REVERSE_OF`) and local 'paperMap'
aggregation initiative (`lantern.lib.metadata_library.models.record.enums.AggregationInitiativeCode.PAPER_MAP`).

Records for each side processed as typical Catalogue Items. The overall Record is processed by the
`lantern.models.item.catalogue.special.physical_map.ItemCataloguePhysicalMap` class, distinguished by:

- using the local 'paperMapProduct' hierarchy level
  (`lantern.lib.metadata_library.models.record.enums.HierarchyLevelCode.PAPER_MAP_PRODUCT`)
- including at least one aggregation for a map side ('isComposedOf' association, 'paperMap' initiative)

The physical map class includes overloaded versions of some tabs to overload selected properties that should aggregate
values from each side (for example spatial resolution (scale)).

A general convention determines whether a single common value is shown, or multiple values labelled for each side:

- if the values in each side are the same they are ignored and the value from the overall Record is shown
- if different, values for each side are shown - the value from the overall Record is ignored

### Public website search items

Public website search items (`lantern.models.item.public_website.ItemWebsiteSearch`) are used to include items in the
[BAS Public Website](https://www.bas.ac.uk) global search. Search items are limited to the properties needed to
describe an item within these search results. A sync API aggregates these search items across the different catalogues
used in BAS for harvesting by the Public Website.

This sync API defines:

- a JSON Schema for the content of these items
- additional properties required to identify the source system of each item, whether it should be marked as deleted, etc.

This schema and requirements are implicitly implemented within this class. Other features include:

- selecting the most relevant date for the item (revision > publication > creation)
- selecting the most suitable description for the item (purpose > abstract)
- determining whether an item should be marked as removed/deleted (based item maintenance info)

### Item super-types

Item types (set by their underlying Record's `hierarchy_level` property) can be sorted into two broad 'super-types':

- *containers*: for types such as collections and projects that group and organise records
- *resources*: for types such as datasets and products that represent actual data holdings

This higher level grouping is useful to simplify and generalise logic in catalogue item tabs and other elements. For
example, whether to enable the licence tab.

Super-types are defined by the `lantern.models.item.catalogue.enums.ItemSuperType` enum.

The super-type for each item is available via the `Item._super_type` private property (for passing to tabs and elements).

### Item aliases

Items are identified by their Record's UUIDv4 `file_identifier` property, including in URLs for item pages. These
values are intentionally non-meaningful and due to their length and randomness not memorable. Whilst useful for ensuring
uniqueness, they are useful when sharing URLs.

Item aliases provide a way to create additional URLs for an item with more useful values, such as a slugified title or
existing codes or shorthand.

Aliases are defined as Record identifiers using the `alias.data.bas.ac.uk` namespace. Values are prefixed by a
pluralised term related to the Record hierarchy level (e.g. `collections/foo` for a collection record). See the
[Record requirements](#record-requirements) section for specific requirements.

> [!CAUTION]
> The catalogue does not enforce aliases to be unique across records and the behaviour of conflicting aliases is left
> undefined. Any implicit behaviour MUST NOT be relied upon.

### Item key value data

The `ItemBase` class includes a `kv` property returning a dictionary of:

- parsed [Key Value](/docs/libraries.md#record-key-value-data)
- or, an empty dict if no KV value is defined, or is malformed

### Item administrative metadata

The `ItemBase` class includes an optional `admin_metadata` property returning:

- parsed [Administrative Metadata](/docs/libraries.md#record-administrative-metadata)
- `None` if no admin metadata is defined, or cannot be decrypted and verified

Item properties, prefixed with `admin_` provide access to admin metadata properties, or also return `None`.

JSON Web Keys (JWKs) for decrypting JWEs and verifying the signature of JWTs should be configured using the
`ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE` and `ADMIN_METADATA_SIGNING_KEY_PUBLIC`
[Config Options](/docs/config.md#config-options) respectively.

> [!TIP]
> These keys can be accessed from [Export Metadata](#export-metadata) if created from a Config object.

### Item access levels

Access levels for each item are available via:

- `Item.admin_metadata_access` (who can view a description of the item)
- `Item.admin_resource_access` (who can access the item itself, if applicable)

Both properties return a `lantern.models.item.base.enums.AccessLevel` enum value, determined by permissions within the
[Administrative Metadata](#item-administrative-metadata).

Both properties default to `AccessLevel.NONE`. To allow open access, include permissions equivalent to the
`lantern.lib.metadata_library.models.record.presets.admin.OPEN_ACCESS` permission.

<!-- pyml disable md028 -->
> [!CAUTION]
> The catalogue does not enforce any metadata access permissions set.

> [!WARNING]
> External data access systems are responsible for enforcing any resource permissions that may apply. The catalogue
> only indicates whether restrictions may apply at an informative level.

> [!WARNING]
> The catalogue does not consider access constraints set in `metadata.costraints` or `identification.constraints`, as
> they can not be verified as trustworthy.

> [!NOTE]
> Access constraints SHOULD still be set for visibility to end users and for interoperability with other systems.
<!-- pyml enable md028 -->

[Catalogue Items](#catalogue-items) simplify the `admin_resource_access` access level to a binary `restricted`
property, returning and defaulting to true unless `Item.admin_access_level == AccessLevel.PUBLIC`.

Where restricted, [Item Templates](/docs/site.md#templates) display additional context in item summaries and
the data tab (if applicable).

## Verification Jobs

Verification jobs represent individual checks run as part of [Site Verification](/docs/monitoring.md#site-verification).

The `lantern.models.verification.jobs.VerificationJob` Python data class implements a structure for each job/check.

A typed dict, `lantern.models.verification.types.VerificationContext`, defines available keys for the context object
used by each job. Various enumerations are used to define values for check types and job status/results.

## Static site metadata

Site metadata represents site-wide information and page specific context, including:

- base URL, build time, etc.
- [Open Graph](https://ogp.me) metadata
  - which can be constructed via the `lantern.models.site.OpenGraphMeta` class
- [Schema.org](https://schema.org) metadata string
  - which can be constructed via the `lantern.models.site.SchemaOrgMeta` class

The `lantern.models.site.SiteMeta` Python data class implements this concept.

## Export metadata

Exporter metadata is a superset of [Site metadata](#static-site-metadata) including additional properties without
passing [Config](/docs/config.md) instances to exporters. This includes:

- the export path
- keys for accessing [Administrative Metadata](#item-administrative-metadata) .

The `lantern.models.site.ExportMeta` Python data class implements this concept, inheriting from `SiteMeta`.
