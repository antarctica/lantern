# Lantern - Usage

> [!NOTE]
> These are draft workflows and are not intended for use by general end-users.

## Setup

1. ensure you have a working [Local Development Environment](/docs/dev.md#local-development-environment) available with
   a valid [Configuration](/docs/config.md#config-options), including access tokens

> [!TIP]
> Run the [`config-check`](/docs/supplemental/proto-cli-reference.md#config-check) to validate the current
> configuration at a basic level.

## Logging

Log messages at or above the *warning* level are written to `stderr` by default. The logging level can be changed via
the `LOG_LEVEL` [Config Option](/docs/config.md#config-options), set to a valid Python logging level, typically *info*.

## Workstation module

An installation of this project is available on the BAS central workstations for other projects to manage and/or
publish records.

<!-- pyml disable md028 -->
> [!IMPORTANT]
> This installation is restricted to MAGIC staff.

> [!NOTE]
> This is a preview feature intended for running the
> [Non-Interactive Publishing Workflow](#non-interactive-publishing-workflow) only.
>
> It cannot be used for workflows or tasks that require [Development Tasks](/docs/dev.md#development-tasks).
<!-- pyml enable md028 -->

To use this installation:

1. ensure [MAGIC environment modules 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/dev-docs/-/blob/main/service-magic-env-modules.md#usage)
   are included in your module search path
1. load the `lantern` module: `module load lantern`

> [!TIP]
> This will load the latest stable [Release](/README.md#releases).
>
> To load a preview of the next release (built from `main`), run `module load lantern/0.0.0.STAGING` instead.

## Creating records

To create records:

- from scratch:
  - see [MAGIC metadata guidance](https://gist.github.com/felnne/d18cceab0fd87acaf2cd482ba3ee5d62)
- by cloning an existing record:
  - run the [`clone-record`](/docs/supplemental/proto-cli-reference.md#clone-record) command
- superseding an existing record:
  - if the successor record has been made already using Zap ⚡:
    - run the [`zap-records`](/docs/supplemental/proto-cli-reference.md#zap-records) command
  - otherwise:
    - run the [`clone-record`](/docs/supplemental/proto-cli-reference.md#clone-record) command
    - then update the cloned record as needed (edition, etc.)
  - run the [`supersede-record`](/docs/supplemental/proto-cli-reference.md#supersede-record) command

Then run the [Interactive Publishing Workflows](#interactive-publishing-workflow) to publish records.

> [!CAUTION]
> The catalogue does not enforce metadata access permissions. They will always evaluate to open access (unrestricted).

## Updating records

To update new and existing records:

- run the [`select-records`](/docs/supplemental/proto-cli-reference.md#select-records) command
- to replace a record with a successor:
  - run the [`supersede-record`](/docs/supplemental/proto-cli-reference.md#supersede-record) command
- to include an Esri ArcGIS Online item as a distribution option:
  - run the [`esri-record`](/docs/supplemental/proto-cli-reference.md#esri-record) command
- to set access permissions:
  - run the [`restrict-records`](/docs/supplemental/proto-cli-reference.md#restrict-record) command

Then run the [Interactive Publishing Workflows](#interactive-publishing-workflow) to publish records.

> [!CAUTION]
> The catalogue does not enforce metadata access permissions. They will always evaluate to open access (unrestricted).

### Replacing record thumbnails

> [!NOTE]
> This is an advanced topic

To replace a thumbnail for an existing resource:

- overwrite the thumbnail file using the AWS CLI [1]
- run the [`thumbnail-invalidate`](/docs/supplemental/proto-cli-reference.md#thumbnail-invalidate) command

> [!NOTE]
> If the thumbnail file name or file type has changed - select, and replace, the relevant graphic overview URL in
> the record for the resource as per the [Update](#updating-records) workflow instead.

[1]

```text
% aws s3 cp ./overview.png s3://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/{file_identifier}/
```

### Replacing record artefacts

> [!NOTE]
> This is an advanced topic

To replace file artefacts included in an existing resource:

- use Zap ⚡️to select (but not upload) the replacement artefact to get an updated distribution option
- replace the relevant distribution as per the [Update](#updating-records) workflow
  - the transfer option URL (and amending if renamed)
  - this should ensure the format and size are updated if needed but double-check this
- continue following the generic update workflow to complete updating the record

## Previewing records

To preview new and updated records before importing them:

1. copy record configurations as JSON files to the `import/` directory
2. run the [`preview-records`](/docs/supplemental/proto-cli-reference.md#preview-records) command
3. run the [Local development web server](/docs/dev.md#local-development-web-server) to view records as items

> [!TIP]
> To view [Administration Metadata](/docs/libraries.md#record-administrative-metadata) for a record at the command
> line, use the [`admin-record`](/docs/supplemental/proto-cli-reference.md#admin-record) command instead.

## Publishing workflows

### Interactive publishing workflow

To import, build and check sets of [Manually Authored](#creating-records) records via a changeset:

1. run the [Testing](#interactive-publishing-workflow-testing) publishing workflow, creating a changeset
2. when approved, run the [Live](#interactive-publishing-workflow-live) publishing workflow,

> [!NOTE]
> This workflow is intended for routine, manual, record publishing. This will not fit all use-cases and requires an
> associated GitLab issue.
>
> To publish records automatically, use the
> [Non-interactive Workflow](#non-interactive-publishing-workflow) instead.
>
> For other use-cases, chain together individual record [Commands](/docs/supplemental/proto-cli-reference.md).

#### Interactive publishing workflow (testing)

To publish records in the testing catalogue:

1. ensure a suitable GitLab issue exists to track publishing the records [1]
1. ensure `*.json` record configs exist in the `import/` directory (see [Create Records](#creating-records))
1. run the [`workflow-testing`](/docs/supplemental/proto-cli-reference.md#workflow-testing) command
1. repeat this process (using the [`select-records`](/docs/supplemental/proto-cli-reference.md#select-records) command),
   until the record author is happy to publish live (signified by approving the merge request for the related changeset)

> [!NOTE]
> The Lantern GitLab bot user MUST have reporter permissions or greater within the project containing the relevant
> GitLab issue. Project memberships SHOULD be defined using
> [Infrastructure as Code](/docs/infrastructure.md#infrastructure-as-code).

[1]

For example, a Helpdesk issue may exist to track the request for a product, which is then set as a GitLab issue within
its metadata record to provide context. When ready for publishing, a separate Mapping Coordination issue may be created.

In this case, the Mapping Coordination issue SHOULD be used in this workflow (as an '< OTHER >' value), *not* the
Helpdesk issue recorded in the record.

#### Interactive publishing workflow (live)

To publish records in the live catalogue:

1. ensure records have been published to the [Testing Site](#interactive-publishing-workflow-testing)
1. ensure the record author has approved the merge request for the changeset to be published
1. ensure the merge request is not a draft
1. run the [`workflow-live`](/docs/supplemental/proto-cli-reference.md#workflow-live) command

### Non-interactive publishing workflow

To import and build sets of record configurations updated automatically by other projects,
use the [Non-Interactive Publishing](/docs/supplemental/non-interactive-publishing.md) workflow.

> [!NOTE]
> This workflow is intended for routine updates to records managed by automated systems.
>
> To publish ad-hoc, manually authored, records, use the
> [Interactive Workflow](#interactive-publishing-workflow) instead.
>
> For other use-cases, chain together individual record [Commands](/docs/supplemental/proto-cli-reference.md).

This workflow:

- parses, validates and filters records from the given input path
  - only valid records that have changed are processed
  - changes are determined by comparing a SHA1 hash of the record content against the remote records store
- if needed, creates a new branch, and associated merge request, in the remote records store
- commits records to this branch
- publishes non-global, untrusted and trusted content from [Outputs](/docs/architecture.md#outputs)
- if set, calls a [Webhook](/docs/supplemental/non-interactive-publishing.md#webhook) with workflow output

<!-- pyml disable md028 -->
> [!TIP]
> The workflow will automatically recreate the configured branch and relevant merge request if needed.
>
> This merge request MAY be merged into the default branch to prevent drift but this is out of scope for this workflow.

> [!NOTE]
> This workflow does not run checks for published records.
>
> When merged, records will be checked via [Periodic Site Checks](/docs/monitoring.md#scheduled-checks).

> [!WARNING]
> Where records are updated frequently, the merge request SHOULD be squashed.
<!-- pyml enable md028 -->

## Importing records

> [!NOTE]
> This is an advanced topic, intended for when [Publishing Workflows](#publishing-workflows) are unsuitable.

To directly import a set of new and updated records:

1. copy record configurations as JSON files to the `import/` directory
1. if needed, run the [`zap-records`](/docs/supplemental/proto-cli-reference.md#zap-records) command
1. run the [`import-records`](/docs/supplemental/proto-cli-reference.md#import-records) command
1. manually create a merge request for the changeset branch in the [Records Repository](/docs/infrastructure.md#gitlab)
1. appropriately review the imported records and merge the changes into `main` when acceptable

> [!WARNING]
> All records in the `import/` directory will be committed together. Consider processing unrelated changes separately.

## Building static site

> [!NOTE]
> This is an advanced topic, intended for when [Publishing Workflows](#publishing-workflows) are unsuitable.

To build the catalogue static site:

1. run the [`build-records`](/docs/supplemental/proto-cli-reference.md#build-records) command

## Checking static site

> [!NOTE]
> This is an advanced topic, intended for when [Publishing Workflows](#publishing-workflows) are unsuitable.

To [Check](/docs/monitoring.md#site-checks) the catalogue static site:

1. run the [`check-records`](/docs/supplemental/proto-cli-reference.md#check-records) command

## Upgrading records

> [!NOTE]
> This is an advanced topic.

To update records in bulk (e.g. to a new profile version, or to adopt new conventions, etc.):

1. create a new [Development Task](/docs/dev.md#record-upgrade-tasks) named `upgrade-records`
1. run the [`upgrade-records`](/docs/supplemental/proto-cli-reference.md#upgrade-records) command to begin an upgrade
1. repeat the `upgrade-records` command to progressively process records
1. store the upgrade report
1. [Import](#importing-records) upgraded records

> [!TIP]
> The upgrade directory SHOULD be tracked in a local Git repo to easily compare and rollback changes.

## Rotating access tokens

See [Deployment](/docs/deployment.md#rotating-access-tokens) documentation.
