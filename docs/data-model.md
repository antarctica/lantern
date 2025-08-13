# Lantern - Data Model

## Records

Records are the primary entity within the Data Catalogue, representing metadata about resources (maps, (products),
datasets, collections, etc.) using the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139)
information model. Records are not specific to the Data Catalogue.

Record configurations represent the contents of these metadata instances, typically expressed as a JSON document.

For use within Python, a Record data class (`lantern.lib.metadata_library.models.record.Record`) is defined which
allows for:

- easier discoverability of record properties
- configuration validation
- filtering list based properties such as contacts, aggregations, etc.
- loading and dumping record configurations (which may be loaded from or dumped to JSON documents)

Additional data classes are used to implement other properties (e.g. an `Identification` class). Properties which use
code lists of allowed values are implemented using `Enum` classes.

> [!NOTE]
> Unless stated otherwise, references to 'Records' elsewhere refer to the [`RecordRevision`](#record-revisions) class.

> [!NOTE]
> The Records model is considered part of the BAS Metadata Library but was developed for this project and not
yet upstreamed. See the [Library](/docs/libraries.md#bas-metadata-library) docs for more information.

### Record revisions

Record Revisions represent a [Record](#record) at a particular point in time by recording a revision identifier
alongside Record data. This identifier is a local addition and is not part of the ISO 19115 information model.

Identifiers are intended to come from a version Control system (VCS) such as Git, where values are unique across the
history of a Record but may be shared by multiple Records, to represent a coordinated set of changes (AKA a changeset).

For use within Python, a Record Revision data class (`lantern.models.record.revisiob.RecordRevision`), a subclass of
`Record` is defined which:

* inherits all `Record` properties and methods
* allows setting a `file_revision` property
* optionally (and not by default) allows dumping the Record config including `file_revision` to plain types (not JSON/XML)

> [!NOTE]
> Unless stated otherwise, references to 'Records' elsewhere refer to the `RecordRevision` data class.

### Record summaries

Conceptually, record summaries are a lightweight representations of a record entity, typically used for listing sets of
records. They contain a subset of record properties, such as title, identifiers, publication date, etc.

> [!NOTE]
> There is no formal specification for record summaries. See the class definition for the properties they include.

A Record Summary data class (`lantern.lib.metadata_library.models.record.summary.RecordSummary`) and
(`lantern.models.record.revision.RecordRevisionSummary`), a subclass corresponding to the `RecordRevision` class, are
used to implement record summaries. `RecordSummary`/`RecordRevisionSummary` instances can be configured directly, or
created from a `Record`/`RecordRevision` instance.

> [!NOTE]
> Unless stated otherwise, references to 'Record Summaries' elsewhere refer to the `RecordRevisionSummary` data class.

> [!NOTE]
> The Record Summary model is considered part of the BAS Metadata Library but was developed for this project
and not yet upstreamed. See the [Library](/docs/libraries.md#bas-metadata-library) docs for more information.

### Record authoring

Records can be authored using any tool or system that can produce a valid record configuration. These may be created
directly as JSON documents, or dumped from `Record` data class instances.

> [!NOTE]
> There is no formal guidance on what to include in record configurations. However, a starting point may be the
> [Examples Records](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1#example-records) defined
> for the MAGIC Discovery ISO 19115 Profile.

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

## Items

Items are wrappers around Records to provide convenience properties and methods to access an underlying Record's
configuration for use in a specific context.

> [!NOTE]
> Items do not follow a formal specification and are not designed to be interoperable outside of this project.

### Item base

The `lantern.models.item.base.ItemBase` Python class contains common properties and methods across all item subclasses.

For example:

- `Item.citation_html` returns an HTML formatted version of `identification.other_citation_details`, if set
- `Item.kv` returns a dict of key-values if `identification.supplemental_information` is a suitable JSON encoded object
- `Item.access` returns a local access type enumeration value by parsing access constraints from `identification.constraints`

### Item summaries

Item Summaries are created from Record Summaries and include relevant convenience properties.

The `lantern.models.item.base.ItemSummaryBase` class provides a base implementation that can be subclassed by Item
subclasses if needed.

### Catalogue items

Catalogue Items (`lantern.models.item.catalogue.ItemCatalogue`) are tightly coupled to the Data Catalogue and its user
interface. Features include:

- properties organised under classes for each UI tab (including logic to determine whether a tab should be shown)
- local enums mapping Record properties to UI values for improved readability
- a `render()` method to output an HTML page for each item
- classes (`lantern.models.item.catalogue.distributions`) for processing distribution options for the catalogue UI
- a local summary implementation (`lantern.models.item.catalogue.elements.ItemSummaryCatalogue`)

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

> [!WARNING]
> The catalogue does not currently enforce this convention but may in the future. To avoid invaliding previous aliases,
> this convention SHOULD be followed.

> [!CAUTION]
> The catalogue does not currently enforce uniqueness of aliases and will not be aware of (or error for) conflicts. The
> behavior of conflicting aliases is undefined. Any implicit behaviour MUST NOT be relied upon.
