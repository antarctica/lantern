# Lantern - Data Model

## Records

Records are a partial representation of the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139)
information model implemented as a data class (`lantern.lib.metadata_library.models.record.Record`). They describe
resources (maps [products], datasets, collections, etc.) and form the primary entity within the Data Catalogue.

<!-- pyml disable md028 -->
> [!NOTE]
> When encoded as XML records are interoperable with applications that support ISO 19139 encoded records.

> [!WARNING]
>When encoded as JSON, records are only interoperable with applications that support the
> [BAS ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas) JSON Schema.
<!-- pyml enable md028 -->

The Record data class provides:

- access to typed record properties
- record configuration validation
- filtering list based properties such as contacts, aggregations, etc.
- loading and dumping record configurations (including from/to JSON documents)

Additional data classes are used to implement sub-properties (e.g. an `Identification` class). Code list properties are
implemented using `Enum` classes.

<!-- pyml disable md028 -->
> [!NOTE]
> Unless stated otherwise, references to 'Records' elsewhere refer to the [`RecordRevision`](#record-revisions) class.

> [!NOTE]
> The Records model is considered part of the BAS Metadata Library but was developed for this project and not
yet upstreamed. See the [Library](/docs/libraries.md#bas-metadata-library) docs for more information.

> [!IMPORTANT]
> The Records model does not support all properties supported by the BAS ISO 19115 JSON Schema. See the
> [Record Limitations](#record-limitations) section for more information.
<!-- pyml enable md028 -->

### Record revisions

Record Revisions represent a [Record](#record) at a particular point in time by recording a revision identifier
alongside Record data. This identifier is a local addition and is not part of the ISO 19115 information model.

Identifiers are intended to come from a version Control system (VCS) such as Git, where values are unique across the
history of a Record but may be shared by multiple Records, to represent a coordinated set of changes (AKA a changeset).

For use within Python, a Record Revision data class (`lantern.models.record.revisiob.RecordRevision`), a subclass of
`Record` is defined which:

- inherits all `Record` properties and methods
- allows setting a `file_revision` property
- optionally (and not by default) allows dumping the Record config including `file_revision` to plain types (not JSON/XML)

> [!NOTE]
> Unless stated otherwise, references to 'Records' elsewhere refer to the `RecordRevision` data class.

### Record authoring

Records can be authored using any tool or system that can produce a valid record configuration. These may be created
directly as JSON documents, or dumped from `Record` data class instances.

<!-- pyml disable md028 -->
> [!TIP]
> For manual editing, consider an editor that supports JSON schemas for inline validation and enum auto-completion.
>
> Within Python applications or scripts, consider using `Record` data classes for typed record properties, validation
> and serialisation to JSON.

> [!NOTE]
> There is no formal guidance on what to include in record configurations. However, a starting point may be the
> [Examples Records](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1#example-records) defined
> for the MAGIC Discovery ISO 19115 Profile.

> [!TIP]
> See the [Guide](https://data.bas.ac.uk/-/formatting) for how titles, summaries, abstracts and lineage statements can
> be formatted.
<!-- pyml enable md028 -->

### Record presets

If authoring Records using data classes, a set of *presents* in the `lantern.lib.metadata_library.models.record.presets`
package are available to create common config subsets and improve consistency across records.

For example:

- `lantern.lib.metadata_library.models.record.presets.extents.make_bbox_extent`:
  - simplifies creating a bounding box extent from a set of coordinates
- `lantern.lib.metadata_library.models.record.presets.constraints.OGL_V3`:
  - provides a constant for the Open Government Licence

> [!TIP]
> A larger scale present (`lantern.lib.metadata_library.models.record.presets.base.RecordMagicDiscoveryV1`) exists for
> creating [MAGIC Discovery ISO 19115 Profile](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1)
> compliant records.

### Record requirements

The Data Catalogue itself requires these properties to be set in all records:

1. the `file_identifier`, so records can be distinguished, without relying on a value that may change or not be unique
1. the `hierarchy_level`, so item types can be distinguished
1. an `identification.identifier`, as per [1] to determine if a record is part of the Catalogue
1. an `identification.identifier.contacts[role='pointOfContact']`, for the item contact tab

[1]

- identifier: `{file_identifier}`
- href: `https://data.bas.ac.uk/items/{file_identifier}`
- namespace: `data.bas.ac.uk`

### Record validation

The `Record` data class includes a `validate()` method which will:

- validate the record configuration against the
  [BAS ISO 19115 JSON schema](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas)
- validate the record configuration against any of these supported profiles:
  - the [MAGIC Discovery Profile (v1)](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1).

Records will be validated automatically when needed. Invalid records will raise a
`lantern.lib.metadata_library.models.record.RecordInvalidError` exception.

### Record limitations

Supported common elements (references not normative or exhaustive):

- `*.citation.title`
- `*.citation.dates`
- `*.citation.edition`
- `*.citation.contacts` (except `contact.position`)
- `*.citation.identifiers`
- `*.citation.series` (with local workaround for `series.page` until v5 schema)
- `*.online resource` (partial)

Supported elements (references not normative or exhaustive):

- `$schema`
- `file_identifier`
- `file_revision` (non-ISO 19115 property, see RecordRevision)
- `hierarchy_level`
- `metadata.character_set` (hard-coded to 'utf8')
- `metadata.language` (hard-coded to 'eng')
- `metadata.contacts` (see `*.citation.contacts`)
- `metadata.date_stamp`
- `metadata.metadata_standard`
- `reference_system_info`
- `identification.title` (via `*.citation.title`)
- `identification.dates` (via `*.citation.dates`)
- `identification.edition` (via `*.citation.edition`)
- `identification.identifiers` (via `*.citation.identifiers`)
- `identification.contacts` (except `*.citation.contacts`)
- `identification.abstract`
- `identification.purpose`
- `identification.other_citation_details`
- `identification.supplemental_information`
- `identification.constraints` (except permissions)
- `identification.aggregations`
- `identification.extents` (temporal and bounding box extents only)
- `identification.graphic_overviews`
- `identification.spatial_resolution`
- `identification.maintenance`
- `identification.character_set` (hard-coded to 'utf8')
- `identification.language` (hard-coded to 'eng')
- `(identification.)data_quality.domain_consistency`
- `(identification.)data_quality.lineage.statement`
- `distribution.distributor`
- `distribution.format` (`format` and `href` only)
- `distribution.transfer_option`

Unsupported elements (not normative or exhaustive):

- `*.contact.position`
- `*.online_resource.protocol`
- `(identification.)data_quality.lineage.process_step`
- `(identification.)data_quality.lineage.sources`
- `distribution.format` (except name and URL)
- `identification.credit`
- `identification.constraint.permissions`
- `identification.extent.geographic.identifier`
- `identification.extent.vertical`
- `identification.keywords`
- `identification.resource_formats`
- `identification.spatial_representation_type`
- `identification.status`
- `identification.topics`
- `metadata.maintenance` (`identification.metadata` is supported)

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
- `Item.access` returns a local access type enumeration value by parsing access constraints from `identification.constraints`

### Catalogue items

Catalogue Items (`lantern.models.item.catalogue.ItemCatalogue`) are tightly coupled to the Data Catalogue and its user
interface. Features include:

- properties organised under classes for each UI tab (including logic to determine whether a tab should be shown)
- local enums mapping Record properties to UI values for improved readability
- a `render()` method to output an HTML page for each item
- classes (`lantern.models.item.catalogue.distributions`) for processing distribution options for the catalogue UI
- an item summary implementation (`lantern.models.item.catalogue.elements.ItemSummaryCatalogue`)

#### Catalogue item limitations

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

Supported properties (references not normative or exhaustive):

- `file_identifier`
- `file_revision`
- `hierarchy_level`
- `reference_system_info`
- `identification.citation.title`
- `identification.citation.dates`
- `identification.citation.edition`
- `identification.citation.contacts` ('author' and single 'point of contact' roles only, excludes `contact.position`)
- `identification.citation.series`
- `identification.citation.identifiers[namespace='doi']`
- `identification.citation.identifiers[namespace='isbn']`
- `identification.citation.identifiers[namespace='alias.data.bas.ac.uk']`
- `identification.citation.identifiers[namespace='gitlab.data.bas.ac.uk'] (as references only)`
- `identification.abstract`
- `identification.aggregations` (only as below)
  - 'part of' (items in collections)
  - item and collection cross-references
  - supersedes (not 'superseded by')
  - 'one side of' (physical maps only)
  - 'opposite side of' (physical maps only)
- `identification.constraints` ('licence' only)
- `identification.maintenance`
- `identification.extent` (single bounding temporal and geographic bounding box extent only)
- `identification.other_citation_details`
- `identification.graphic_overviews` ('overview' image only)
- `identification.spatial_resolution`
- `identification.supplemental_information` (for 'physical dimensions' and 'sheet number' only)
- `data_quality.lineage.statement`
- `data_quality.domain_consistency`
- distributor.format (`format` and `href` only)
- distributor.transfer_option (except `online_resource.protocol`)

Unsupported properties (references not normative or exhaustive):

- `identification.purpose` (except as used in ItemSummaries)

Intentionally omitted properties (references not normative or exhaustive):

- `*.character_set` (not useful to end-users, present in underlying record)
- `*.language` (not useful to end-users, present in underlying record)
- `*.online_resource.protocol` (not useful to end-users, present in underlying record)
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

### Item Aliases

Items are identified by their Record's UUIDv4 `file_identifier` property, including in URLs for item pages. These
values are intentionally non-meaningful and due to their length and randomness not memorable. Whilst useful for ensuring
uniqueness, they are useful when sharing URLs.

Item aliases provide a way to create additional URLs for an item with more useful values, such as a slugified title or
existing codes or shorthand.

Aliases are defined as Record identifiers using the `alias.data.bas.ac.uk` namespace. By convention alias, values are
prefixed by a pluralised version of the Record hierarchy level (e.g. `collections/foo`).

<!-- pyml disable md028 -->
> [!WARNING]
> The catalogue does not currently enforce this convention but may in the future. To avoid invaliding previous aliases,
> this convention SHOULD be followed.

> [!CAUTION]
> The catalogue does not currently enforce uniqueness of aliases and will not be aware of (or error for) conflicts. The
> behavior of conflicting aliases is undefined. Any implicit behaviour MUST NOT be relied upon.
<!-- pyml enable md028 -->
