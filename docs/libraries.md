# Lantern - Libraries

Extensions to, or code closely associated with, third-party libraries relied on by this application.

## Markdown

`lantern.lib.markdown`

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

`lantern.lib.metadata_library`

Includes classes for [Records](/docs/models.md#records).

These redesigned and refactored classes are intended ti replace core parts of the
[BAS Metadata Library](https://github.com/antarctica/metadata-library).

### Records

`lantern.lib.metadata_library.models.record.Record`

Records are a partial representation of the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139)
information model in Python. They generically describe resources (maps/products, datasets, collections, etc.).

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
  - the [MAGIC Administration Profile (v1)](https://metadata-standards.data.bas.ac.uk/profiles/magic-administration/v1).

Records will be validated automatically when needed. Invalid records will raise a
`lantern.lib.metadata_library.models.record.RecordInvalidError` exception.

### Record limitations

> [!NOTE]
> These references are not normative or exhaustive and relate to the BAS ISO 19115 JSON schema.

Supported common elements:

- `*.citation.title`
- `*.citation.dates`
- `*.citation.edition`
- `*.citation.identifiers`
- `*.citation.contacts` (except `contact.position`)
- `*.citation.series` (with local workaround for `series.page` until v5 schema)
- `*.constraints` (limited restriction code list options)
- `*.maintenance`
- `*.online resource` (partial)

Supported elements:

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

Unsupported elements:

- `*.contact.position`
- `*.online_resource.protocol`
- `(identification.)data_quality.lineage.process_step`
- `(identification.)data_quality.lineage.sources`
- `distribution.format` (except name and URL)
- `identification.credit`
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

If authoring Records using data classes, a set of *presets* in the `lantern.lib.metadata_library.models.record.presets`
package are available to create common config subsets and improve consistency across records.

For example:

- `lantern.lib.metadata_library.models.record.presets.extents.make_bbox_extent`:
  - simplifies creating a bounding box extent from a set of coordinates
- `lantern.lib.metadata_library.models.record.presets.constraints.OGL_V3`:
  - provides a constant for the Open Government Licence

Larger scale presets for creating typical MAGIC records, valid against the MAGIC Discovery (v2) and Administration (v1)
profiles, are available in two forms:

- `lantern.lib.metadata_library.models.record.presets.base.RecordMagic` (*base*)
- `lantern.lib.metadata_library.models.record.presets.base.RecordMagicOpen` (inherits from *base*)

> [!TIP]
> Additional elements to check when using these larger presets:
>
> - `metadata.maintenance` (uses AS_NEEDED and COMPLETED by default)

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

The `lantern.lib.metadata_library.models.record.utils.admin.get_admin` and `set_admin` utility functions extend the
[Metadata Library](https://github.com/antarctica/metadata-library/blob/v0.16.0rc1/docs/usage.md#magic-administration-metadata)
methods to access and update MAGIC Administration metadata to work with [Records](#records).

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

### Adding new well known access permissions

> [!WARNING]
> This section is Work in Progress (WIP) and may not be complete/accurate.

1. update the `lantern.lib.metadata_library.models.record.enums.MagicAccessFrameworkPermission` enum
1. add a preset in `lantern.lib.metadata_library.models.record.presets.admin` (for administration metadata)
1. add a preset in `lantern.lib.metadata_library.models.record.presets.constraints` (for discovery metadata)
1. update `lantern.lib.metadata_library.models.record.utils.admin.parse_framework_permissions` and associated tests

## MAGIC Distribution

`lantern.lib.magic_distribution`

Includes clients, [Artefact](#artefacts) models and clients for managing file artefacts within [SharePoint](#sharepoint)
and service artefacts within [ArcGIS](#arcgis).

### SharePoint

`lantern.lib.magic_distribution.sharepoint`

Includes metadata data structures, [Artefact](#sharepoint-file-artefacts) and a Microsoft Graph upload client for
managing file artefacts within Microsoft SharePoint Online.

> [!NOTE]
> This package is specific to the SharePoint implementation of the
> [MAGIC Resource Distribution Service 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/resource-distribution).

#### SharePoint client

`lantern.lib.magic_distribution.sharepoint.client.MagicResourceDistributionClient`

Used to deposit [File Artefacts](#file-artefacts) and lookup/download hosted
[SharePoint File Artefacts](#sharepoint-file-artefacts) in a SharePoint Online site document library using the
Microsoft Graph API.

> [!NOTE]
> This client requires an Entra app registration with permissions to either read, or manage files within the relevant
> SharePoint site (depending on whether file deposit is needed).

#### SharePoint client limitations

In addition to [Limitations 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/resource-distribution#limitations) from the
underlying MAGIC Resource Distribution service, known limitations include:

- permissions on existing files cannot be updated

> [!TIP]
> Where needed, permissions on existing files can be updated by (manually) removing files then re-depositing them.

#### SharePoint file artefacts

`lantern.lib.magic_distribution.sharepoint.models.artefact.ArtefactSharePointFile`

[File Artefacts](#file-artefacts) representing a remote file hosted in a SharePoint document library, accessed via the
Microsoft Graph as a [Drive Item](https://learn.microsoft.com/en-us/graph/api/resources/driveitem).

Includes [Metadata](#sharepoint-file-metadata) and an [Artefact Format](#artefact-formats) from associated SharePoint
list values accessed via the Microsoft Graph as a
[Field Value Set](https://learn.microsoft.com/en-us/graph/api/resources/fieldvalueset).

<!-- pyml disable md028 -->
> [!Note]
> SharePoint artefacts do not include direct access to file content. An access URL intended for end-users is available.

> [!WARNING]
> This URL MAY NOT resolve to a raw file (for example CSV and PDF files MAY open in an online viewer.
<!-- pyml enable md028 -->

#### SharePoint file metadata

In addition to required [Artefact Metadata](#artefact-metadata), SharePoint file artefacts include properties for:

- whether a resource has unrestricted (open) access, for use with an
  [Anonymous Access Proxy 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/resource-distribution/-/blob/main/docs/implementation.md#anonymous-access-proxy)

### ArcGIS

`lantern.lib.magic_distribution.arcgis`

Includes metadata data structures, [Artefact](#arcgis-service-artefacts) and an ArcGIS API client for managing and
accessing artefacts within ArcGIS Online and Enterprise.

> [!NOTE]
> This package is focused on and limited to needs within the Mapping and Geographic Information Centre (MAGIC).
>
> It is not a suitable replacement for the ArcGIS API for Python and/or `arcpy` packages maintained by Esri.

#### ArcGIS vendored classes

`lantern.lib.magic_distribution.arcgis.gis`

A vendored subset of data classes and enums representing ArcGIS Portal items.

> [!NOTE]
> These classes are based on originals from the ArcGIS API for Python. These local classes remove unneeded
> functionality and/or adjust types to comply with linting rules in this project.

#### ArcGIS item properties

`lantern.lib.magic_distribution.arcgis.gis.dataclasses.ItemProperties`

> [!WARNING]
> The behaviour and/or use of some item properties has been expanded or changed from their original implementation in
> the ArcGIS API for Python to suit the requirements of this project.

Supported item JSON properties:

- id
- owner
- org_id
- url (service endpoint)
- access (sharing level)
- title
- type (`enum`)
- snippet
- description
- accessInformation (attribution)
- licenseInfo
- thumbnail (with [Special Handling](#arcgis-thumbnails))

Unsupported item JSON properties:

- created
- isOrgItem
- modified
- guid
- name
- typeKeywords
- tags
- documentation
- extent
- categories
- spatialReference
- classification
- culture
- properties
- advancedSettings
- proxyFilter
- size
- subInfo
- appCategories
- industries
- languages
- largeThumbnail
- banner
- screenshots
- listed
- ownerFolder
- protected
- commentsEnabled
- numComments
- numRatings
- avgRating
- cnumViews
- itemControl
- scoreCompleteness
- groupDesignations
- apiToken1ExpirationDate
- apiToken2ExpirationDate
- lastViewed

#### ArcGIS thumbnails

In ArcGIS Portal items, thumbnails are stored as a related resource, similar to metadata. The relative path to this
file, if set, is stored in the `thumbnail` item property.

To enable thumbnail syncing between catalogue records and ArcGIS items, a target Arc item is compared against a
simulated item from a catalogue record (using the [`ItemArcGIS`](/docs/models.md#arcgis-items) model). Catalogue
records store complete URLs to thumbnails, and file references stored in a Arc item cannot be reliably guaranteed.

This means filename based comparisons cannot be used to determine if the item thumbnail needs to be replaced, based
on a source record. Instead, SHA1 hashes are used to compare the source and target thumbnails. For targets items, the
SHA1 is calculated from the thumbnail if set (by hashing a temporary download). For source records, the SHA1 is taken
from the relevant graphic overview href.

However, as original thumbnails are post-processed by ArcGIS Portal/Online when uploaded, its original SHA1 value
(calculated outside of Arc), will never match the target item (even where the target represents the same resource).
To work around this, an additional `sha1Agol` query parameter is used to record a known accurate value.

> [!TIP]
>

The `thumbnailurl` ArcGIS Python SDK class property is used to hold the computed (for target items) or pre-determined
(for source records) image URLs containing sha1 values. Normally this property is only set when creating a thumbnail
from an item. This property is not part of the general item representation (used by the Rest API for example) and is
otherwise unused.

> [!NOTE]
> Due to this system, only the `sha1Agol` value is used to compare item thumbnails. If the underlying image is changed,
> and the SHA1 values are not, the sync process will not determine the thumbnail needs to be replaced.

#### ArcGIS item property limitations

Partially supported features (not-exhaustive):

- the `metadataEditable` property
  - not exposed as a property via these classes
  - used only in the `_update_agol_item()` method of the `esri-item` dev task (force set)

#### ArcGIS client

`lantern.lib.magic_distribution.arcgis.client.ArcGisClient`

Used for managing and accessing [ArcGIS Service Artefacts](#arcgis-service-artefacts) in a ArcGIS Online organisation
using ArcGIS APIs.

<!-- pyml disable md028 -->
> [!NOTE]
> This client is focused on and limited to needs within the Mapping and Geographic Information Centre (MAGIC).
>
> It is not a suitable replacement for the ArcGIS API for Python and/or `arcpy` packages maintained by Esri.

> [!NOTE]
> The Esri [ArcGIS API for Python](https://developers.arcgis.com/python) package is not used due to the number of
> dependencies it relies on (see https://github.com/Esri/arcgis-python-api/issues/1692).

> [!NOTE]
> This client requires an ArcGIS OAuth client registration with permissions to either read, or manage content within
> an ArcGIS Online organisation.
<!-- pyml enable md028 -->

#### ArcGIS client limitations

Known unsupported features (not-exhaustive):

- group sharing (see also [ArcGIS Item Limitations](/docs/models.md#arcgis-items-limitations))
- [Item and Service Types](#supported-arcgis-types) not listed as supported (e.g. non-raster tile map services)
- [Unsupported Item Properties](#arcgis-item-properties)
- provisioning services via a collaborated ArcGIS Enterprise instance
- content administration and organisation (except item reassignment)
- user administration

#### Supported ArcGIS types

Supported ArcGIS service types:

- Feature Services
- ArcGIS OGC API Features
- Map Services (for raster tiles only)
- Vector Tile Services

Supported ArcGIS item types:

- Feature Layers
- OGC API Feature Layers
- Raster Tile Layers
- Vector Tile Layers
- Web Scenes
- Web Maps

Items vs Services:

- services are hosted within ArcGIS Server and are used to access and query data (such as features, tiles, etc.)
- items describe services and other objects such as maps within ArcGIS Portal
- all services have a corresponding item; not all items are backed by an underlying service (e.g. web maps)
- for this reason item metadata are usually used over service for e.g. a bounding extent
- exceptions to this include `ArcGisClient._get_fs_layer_last_data_update` to get a more specific value

#### ArcGIS service artefacts

`lantern.lib.magic_distribution.arcgis.models.artefact.ArtefactArcGisService`

[Service Artefacts](#service-artefacts) representing content hosted in an ArcGIS Online organisation accessed as a
ArcGIS Portal item.

Items vs Artefacts:

- items are ArcGIS specific metadata about resources held within ArcGIS Portal, using an ArcGIS information model
- artefacts are an internal concept representing how resources can be accessed in a generic way (e.g. as files)
- items are used internally with this client for compatibility with ArcGIS APIs
- items may be used directly outside of this client where this makes (e.g. in ArcGIS specific workflows)
- artefacts can be constructed by this client based on an item (as `ArtefactArcGisService` instances) for use in a
  more generic way within other tools and workflows (e.g. a resource may include both service and file artefacts
  hosted across a range of providers)

> [!Note]
> ArcGIS artefacts do not include direct access to data within underlying services. The [ArcGIS Client](#arcgis-client)
> provides methods to access data from some service types.

## Artefacts

`lantern.lib.magic_distribution.models.artefact.ArtefactBase`.

Artefacts represent a description of the contents of a resource in Python. They describe files, services or other
representations containing all or part of the resource in a specific format or protocol. Artefacts are related to
resources via distribution options within metadata.

For example:

- a map product MAY be distributed with PDF and JPEG [File Artefacts](#file-artefacts)
  - the underlying GIS project for this map COULD also be an artefact as a resource representation, if supported
- a vector dataset MAY be distributed as a GeoPackage file, and/or as an OGC Features API
  [Service Artefact](#service-artefacts)

The `ArtefactBase` abstract class defines common logic and properties and methods artefact subclasses MUST implement.

### Artefact metadata

`lantern.lib.magic_distribution.models.metadata.ArtefactMetadata`

Artefacts MUST include metadata for:

- the identifier of the associated resource
- a unique artefact identifier (generated via a hash of a relevant value)
- a controlled and supported [Format](#artefact-formats)

### Artefact formats

`lantern.lib.magic_distribution.models.artefact.ArtefactFormat`

Artefacts MUST select a supported format, identified by the `lantern.lib.magic_distribution.formats.ArtefactFormatLabel`
enum. Either by examining the entity the Artefact represents (e.g. a file's extension and contents or service
conformance info), or by direct assignment.

### File artefacts

`lantern.lib.magic_distribution.models.artefact.ArtefactFile`

Represents information held in a stored or virtual file of a particular type in Python, with a name which includes a
file extension.

File artefacts MAY be local (using `lantern.lib.magic_distribution.models.artefact.ArtefactLocalFile`), where the file
contents is available and the [Format](#artefact-formats) can be reliably determined (as file extensions are not
definitive in some cases).

### Service artefacts

`lantern.lib.magic_distribution.models.artefact.ArtefactService`

Represents information accessible via a particular protocol in Python, available at a given endpoint URL.

### Supported file formats

- CSV
- FPL (Garmin flight plan - for Garmin aviation GPS units)
- GPX (nominally for handheld GPS units)
- GeoPackage (optionally zipped for compression)
- JPEG images
- GeoJSON (non-geo JSON files are not supported)
- MapBox vector tiles
- PDF (including georeferenced PDF)
- PNG
- Shapefile (specifically where zipped with required files `.shp`, `.shx`, `.dbf`)
- GeoTiff (non-geo TIFF images are not supported)

### Supported service formats

> [!NOTE]
> Format in this context relates to the service protocol, rather than the formats a service may offer as output.

- ArcGIS feature service (and associated layer)
- OGC API features (as implemented by ArcGIS, and including associated layer)
- ArcGIS raster tile service (and associated layer)
- ArcGIS vector tile service (and associated layer)
- ArcGIS scene service (and associated layer)
- ArcGIS web map

### Adding file artefact formats

> [!WARNING]
> This section is Work in Progress (WIP) and may not be complete/accurate.

To enable additional file formats to be deposited as [File Artefacts](#file-artefacts).

- add a new member to the `lantern.lib.magic_distribution.models.artefact.ArtefactFormatLabel` enumeration
- add a new list item to `lantern.lib.magic_distribution.models.artefact.ArtefactFormats.file_formats`
  (or `.service_formats`)
- update tests (typically `lib_tests.magic_distribution.models.test_artefacts.TestArtefactsFormats.test_get_file_format`)
- update supported [File](#supported-file-formats) or [Service](#supported-service-formats) documentation

> [!NOTE]
> Typically, new artefact formats are also added as supported
> [Distribution Formats](/docs/dev.md#adding-distribution-formats) for display within catalogue items.
