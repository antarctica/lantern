# Lantern - Rothera Progress Monitoring Orthomosaics publishing workflow (Supplemental)

> [!WARNING]
> This section is Work in Progress (WIP) and may not be complete/accurate.

## Overview

A workflow to generate discovery metadata for GeoTIFF images representing orthomosaics of the Rothera research station
captured routinely by BAS Engineering and provided to MAGIC for distribution, including with BAS Construction Partners
within the Antarctic Infrastructure Modernisation Programme (AIMP).

Includes limited processing of source GeoTIFFs to produce consistent file artefacts and catalogue item thumbnails.

> [!TIP]
> This workflow represents an initial exploration of how a time series can be catalogued to minimise manual effort and
> promote consistency. As this workflow matures, parts SHOULD be generalisable to other similar use-cases.

### Limitations

This workflow:

- does not support [Service Provisioning](#service-artefact-provisioning)
- requires a [Local Development Environment](/docs/dev.md#local-development-environment)
- has not been robustly tested
- is an initial, exploratory, implementation, which MAY be changed or removed without warning

Resources catalogued by this workflow:

- have limited data quality (acquisition, processing) as we don't generate receive this information
- uses qualitative rather than structured data quality (for instrumentation, acquisition, processing, etc.)

## Bootstrapping

To set up this workflow:

1. create a [Data Area](#data-area) containing acquired GeoTIFF images
1. create an [Events Manifest](#events-manifest)
1. [Create](/docs/usage.md#creating-records) and [Publish](/docs/usage.md#publishing-workflows) a collection record
1. then follow the [Routine Usage](#routine-usage) instructions for future updates

## Routine usage

To process a newly acquired image:

1. add the image to the [Data Area](#data-area)
1. add a row to the [Events Manifest](#events-manifest)
1. run the [`workflow-rothera-orthos`](/docs/supplemental/proto-cli-reference.md#workflow-rothera-orthos) command

This command runs through a sequence of [Processing Steps](#processing-steps) for events (images) defined in the
[Events Manifest](#events-manifest), referencing and processing associated files from the [Data Area](#data-area) as
needed. Where an event fails a processing step a message is logged and the event is skipped from further processing.

The [`workflow-rothera-orthos`](/docs/supplemental/proto-cli-reference.md#workflow-rothera-orthos) command writes
logging messages to STDERR, including any warnings and/or errors encountered during processing.

### Workflow outputs

Generated records are written to an output directory for [Publishing](/docs/usage.md#publishing-workflows).

A summary report is written to STDOUT listing each image subdirectory within the [Data Area](#data-area) and any
completed [Processing Steps](#processing-steps).

## Data Area

A base directory containing source GeoTIFFs is required. This base directory is typically stored centrally but CAN be
local (for testing etc.).

Source images MUST:

- be named in the form: `rothera_orthomosaic_YYYY-MM-DD.tif`
- be within a subdirectory in the form `YYYY-MM-DD_Rothera_Station` (e.g. `2014-04-30_Rothera_Station`)

For example an image acquired on 30 April 2014 MUST be stored as:
`2014-04-30_Rothera_Station/rothera_orthomosaic_2014-04-30.tif`.

Image subdirectories MAY contain additional files but MUST NOT group images within additional subdirectories
(e.g. per year).

A set of images would be stored as:

```text
exp/SAN
├── 2026-01-14_Rothera_Station
│  └── rothera_orthomosaic_2026-01-14.tif
...
└── 2026-07-20_Rothera_Station
    └── rothera_orthomosaic_2026-07-20.tif
```

## Events Manifest

To associate persistent identifiers to each acquired image (termed an event within this workflow), and control which
files in the [Data Area](#data-area) are processed, a manifest CSV file is used.

> [!NOTE]
> Images not included in the manifest will not be processed and show as 'NOT_INITIALISED' in the workflow report.

Example CSV:

```csv
file_identifier,acquisition_date,cde_geotiff,cde_jpeg
27fec43e-d404-4b24-b5ca-233dc89238be,2026-01-14,AIMP-BAS-002,AIMP-BAS-002
4115b3dd-4e5f-448e-876e-db5dbf005f1a,2026-02-16,,
18b17422-e614-4e7c-8684-d0dd13aa6c0e,2026-03-02,,AIMP-BAS-003
```

Where:

- `file_identifier`: is required and MUST meet the [Record Requirements](/docs/models.md#record-requirements)
- `acquisition_date`: is required and MUST relate to a subdirectory and file in the [Data Area](#data-area)
- `cde_geotiff` and `cde_jpeg`: are optional BAS construction partner Common Data Environment (CDE) references for the
  source image and derived and generated JPEG files where assigned

## Processing steps

The sequence of these processing steps is defined by the `tasks.data_workflow_rothera_orthos.EventStage` enum.

Some additional non-event processing steps are also run, such as updating the parent collection record.

### Manifest processing

`tasks.data_workflow_rothera_orthos._load_manifest`

- loads the [Events Manifest](#events-manifest)
- returns event metadata including external identifiers and the acquisition date which cannot otherwise be derived

Valid events are reported as `EventStage.MANIFEST`.

### Image processing

`tasks.data_workflow_rothera_orthos._process_images`

- ensures GeoTIFFs have external overviews, and do not have internal overviews, for compatibility with ArcGIS Server
- generates a derived full resolution JPEG image from the source GeoTIFF
- generates a low resolution JPEG file from the derived JPEG for use as a thumbnail (target size < 300KB)
- extends event metadata will file paths to source and derived image files, and a bounding box extent from the GeoTIFF

Processed events are reported as `EventStage.PROCESSED`.

### Record generation

`tasks.data_workflow_rothera_orthos._generate_records` and `tasks.data_workflow_rothera_orthos._finish_records`

Initially:

- generates and validates a templated product metadata [Record](/docs/models.md#records) using event metadata
- extends event metadata with the generated record object

Events with valid records are reported as `EventStage.RECORD`.

Then later:

- adds thumbnail overviews
- adds distribution options for [Deposited](#file-artefact-deposit) and [Provisioned](#service-artefact-provisioning)
  artefacts
- sets successor and predecessor relationships between events ordered by acquisition date
- re-validates and updates the record object in the event metadata

Events with valid records are reported as `EventStage.FINISHED`.

### File artefact deposit

`tasks.data_workflow_rothera_orthos._deposit_files`

- deposits processed images as file artefacts using the
  [MAGIC Distribution](/docs/libraries.md#magic-resource-distribution) service
- extends event metadata with artefact metadata (format, size, checksum, access URL, etc.)

Events with deposited artefacts are reported as `EventStage.DEPOSITED`.

### Service artefact provisioning

`tasks.data_workflow_rothera_orthos._provision_services`

> [!IMPORTANT]
> Service provisioning (as ArcGIS map services) is not yet supported meaning this step is essentially skipped

- extends event metadata with blank artefact metadata

Events with (fake) provisioned artefacts are reported as `EventStage.PROVISIONED`.
