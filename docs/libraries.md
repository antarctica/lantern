# BAS Assets Tracking Service - Libraries

Extensions to, or code closely associated with, third-party libraries relied on by this application.

## Markdown

Package: `assets_tracking_service.lib.markdown`

### Markdown plain text plugin

A plugin based on https://github.com/kostyachum/python-markdown-plain-text is used to strip Markdown formatting from
text for use in HTML titles for example.

### Markdown automatic links plugin

A plugin based on https://github.com/daGrevis/mdx_linkify is used to convert inline URLs and email addresses in
Markdown text into HTML links.

### Markdown list formatting plugin

A plugin based on https://gitlab.com/ayblaq/prependnewline/ is used to automatically add additional line breaks to
correctly paragraphs from lists in Markdown and ensure proper formatting.

## BAS Metadata Library

> [!IMPORTANT]
> These are rough/working notes that will be written up properly when this module is extracted.

Package: `lantern.lib.metadata_library`

Includes classes for [Records](/docs/data-model.md#records).

These redesigned and refactored classes will replace core parts of the Metadata Library project.

### Records

Records are a partial representation of the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139)
information model implemented as a base data class (`lantern.lib.metadata_library.models.record.Record`). They
generically describe resources (maps [products], datasets, collections, etc.).

<!-- pyml disable md028 -->
> [!IMPORTANT]
> The Records model does not support all properties supported by the BAS ISO 19115 JSON Schema. See the
> [Record Limitations](#record-limitations) section for more information.

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

Sub-properties are implemented as additional data classes (e.g. an `Identification` class). Code list properties are
implemented using `Enum` classes.

### Record validation

The `Record` data class includes a `validate()` method which will:

- validate the record configuration against the
  [BAS ISO 19115 JSON schema](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas)
- validate the record configuration against any of these supported profiles:
  - the [MAGIC Discovery Profile (v1)](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v1).
  - the [MAGIC Discovery Profile (v2)](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2).

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
- `metadata.constraints`
- `metadata.maintenance`
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

### Record authoring

Records can be authored using any tool or system that can produce a valid record configuration. These may be created
directly as JSON documents, or constructed as `Record` data class instances and then dumped to JSON.

<!-- pyml disable md028 -->
> [!TIP]
> For manual editing, consider an editor that supports JSON schemas for inline validation and enum auto-completion.
>
> Within Python applications or scripts, consider using `Record` data classes for typed record properties, validation
> and easy serialisation to JSON.

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
> A larger scale present (`lantern.lib.metadata_library.models.record.presets.base.RecordMagicDiscoveryV2`) exists for
> creating [MAGIC Discovery ISO 19115 Profile](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2)
> compliant records.

### Record utilities

A set of utility functions in the `lantern.lib.metadata_library.models.record.utils` package are available to perform
common or complex tasks.

### Record key value data

To support properties that cannot be represented natively in the ISO 19115 information model, key value data can be
encoded in a JSON string within the `identifification.supplemental_information` element of a Record.

<!-- pyml disable md028 -->
> [!WARNING]
> The use of key values is non-standard and exclusive. If used, other content MUST NOT be included in the element.
>
> Keys in this data are not controlled and must be accessed defensively.

> [!TIP]
> The `lantern.lib.metadata_library.models.record.utils.kv.get_kv` and `set_kv` [Utility Functions](#record-utilities)
> MAY be used to access and update key value data.
<!-- pyml enable md028 -->

### Record administrative metadata

To support the internal management of metadata records, additional
[Administrative metadata](https://metadata-standards.data.bas.ac.uk/profiles/magic-administration-v1/) (as opposed
to discovery, calibration or other metadata) can be included in Records.

> [!NOTE]
> Administrative metadata uses an internally developed schema and is not intended for external use. Administrative
> metadata is stored in the supplemental information element within the ISO 19115 information model.

The `lantern.lib.metadata_library.models.record.elements.administration.Administration` Python data class implements
this concept and supports encoding/decoding to/from a JSON encoded string.

This string value is included as a custom `pyd` (payload) claim within an asymmetrically signed long-lived JSON Web
Token (JWT), nested within a symmetrically encrypted JWE (JSON Web Encryption) using the
`lantern.lib.metadata_library.models.record.utils.admin.AdministrationWrapper` utility class. JWE values should be
stored in Records a [Key Value](#record-key-value-data) item under a `administrative_metadata` key.

The JSON Web Keys (JWKs) for signing/verifying JWTs and encrypting/decrypting JWEs are held in the
`lantern.lib.metadata_library.models.record.utils.admin.AdministrationKeys` data class.

> [!TIP]
> The `lantern.lib.metadata_library.models.record.utils.admin.get_admin` and `set_admin` utility functions SHOULD be
> used to access and update administrative metadata.

### Adding new Record properties

> [!WARNING]
> This section is Work in Progress (WIP) and may not be complete/accurate.

To add support for a new ISO element within Records:

1. create a new data class for the new element in the relevant top module (i.e. `identification.py`)
2. define enums for code lists if needed
3. define a cattrs (un)structure hook if needed
4. include the new class as a property in the relevant top-level class (i.e. `Identification`)
5. register the cattrs (un)structure hook in the top-level class hooks if needed
6. add tests for the new class testing all permutations, and cattrs hook if needed
7. amend tests for top-level class (i.e. `TestIdentification`) variant:
   1. add variant for minimal instance of the new class if optional
   2. amend all variants with a minimal instance of the new class if required
   3. amend asserts to check new class as required
   4. amend tests for top-level cattrs hooks if changed
8. if new class part of minimal record, update `fx_record_config_minimal` fixture
9. amend tests for root-level class (i.e. `TestRecord`):
   1. amend tests for root-level cattrs hooks if top-level hooks changed (as an integration check)
   2. amend variants in `test_loop` as needed (include all possible options in complete variant)
10. amend list of unsupported properties in `/docs/data-model.md#record-limitations` as needed
