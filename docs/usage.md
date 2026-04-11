# Lantern - Usage

<!-- pyml disable md028 -->
> [!NOTE]
> This page is specific to the [BAS Data Catalogue](/docs/architecture.md#bas-data-catalogue).

> [!NOTE]
> These are draft workflows and are not intended for use by general end-users.
<!-- pyml enable md028 -->

## Setup

1. ensure you have a working [Local Development Environment](/docs/dev.md#local-development-environment) available with
   a valid [Configuration](/docs/config.md#config-options), including access tokens

> [!TIP]
> Run the `config-check` [Development Task](/docs/dev.md#development-tasks) to validate the current configuration.

## Logging

Log messages at or above the *warning* level are written to `stderr` by default. The logging level can be changed via
the `LOG_LEVEL` [Config Option](/docs/config.md#config-options) set to a valid Python logging level, typically *info*.

## Workstation module

An installation of this project is available on the BAS central workstations for other projects to manage and/or
publish records.

<!-- pyml disable md028 -->
> [!IMPORTANT]
> This installation is restricted to MAGIC staff.

> [!NOTE]
> This is a preview feature limited to running the
> [Non-Interactive Publishing Workflow](#non-interactive-record-publishing-workflow) only.
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

## Create records

1. create new records, (or clone a record using the `clone-record` [Development Task](/docs/dev.md#development-tasks))
   as JSON files in the import directory as per the [Record Authoring](/docs/libraries.md#record-authoring) section
   - records MAY be created using the experimental [Zap ⚡](https://basweb.nerc-bas.ac.uk/~felnne/apps/zap/prod/) editor,
     though this tool now has limitations
   - published map records MAY use the experimental [MEGA Zap ⚡️](https://mega-zap.streamlit.app/) to finalise records,
     though this tool now has limitations
   - restricted product records MAY use deposit file artefacts (downloads) using the experimental
     [MAGIC Products Distribution Service 🛡](https://gitlab.data.bas.ac.uk/MAGIC/products-distribution) tool
1. use the `esri-record` [Development Task](/docs/dev.md#development-tasks) to include distribution options for any
   Esri ArcGIS Online items that apply to records
1. run the [Interactive Publishing Workflow](#interactive-record-publishing-workflow) (preferred) or where you need
   greater control, run the [Import Records](#import-records) task directly

<!-- pyml disable md028 -->
> [!CAUTION]
> The catalogue does not enforce metadata access permissions. They will always evaluate to open access (unrestricted).

> [!TIP]
> See the [Content Formatting](https://data.bas.ac.uk/guides/formatting) for Markdown syntax supported in record
> free-text elements.
<!-- pyml enable md028 -->

The `clone-record` task will:

1. prompt interactively for:
   - the identifier of an existing record (unless the `--source` command line argument is set)
   - the file identifier to use for the cloned record (unless the `--target` command line argument is set)
1. load the source record from the [GitLab Store](/docs/stores.md#gitlab-store)
1. duplicate the source record with the new record file identifier [1]
1. save the new record configuration as a JSON file to the `import/` directory

[1]

These fields are updated when duplicating a record:

- `file_identifier`
- `identification.identifier[namespace='lantern.data.bas.ac.uk']` (data catalogue identifier)
- `identification.supplemental_information[admin_metadata]`

> [!NOTE]
> Other fields (such as citation, aliases, edition, title, etc.) are not changed and may need updating.

For administrative metadata, these fields are updated:

- `id` (to match the new `file_identifier`)

> [!NOTE]
> Other properties (gitlab issues, metadata/resource access permissions etc.) are not changed and may need updating.

The `esri-record` task will:

- accept an identifier to an existing record, or path to a record configuration file, and an AGOL item ID or URL via
  the command line
- prompt interactively to confirm the GitLab store is configured with the correct branch
- load the record from the [GitLab Store](/docs/stores.md#gitlab-store) or from the given file path
- get details for the ArcGIS item via the ArcGIS REST API
- create distribution options for the layer and service based on these details and catalogue conventions
- add these options to the record where they do not yet exist

> [!TIP]
> Use the `esri-item` [Development Task](/docs/dev.md#development-tasks) instead to update an ArcGIS Online item with
> supported properties from a catalogue record.

## View records

To preview new or edited records before importing them:

1. copy record configurations as JSON files to the `import/` directory
2. run the `preview-records` [Development Task](/docs/dev.md#development-tasks) and select which records to preview
3. run the [Local development web server](/docs/dev.md#local-development-web-server) to view records as items

To view [Administration Metadata](/docs/libraries.md#record-administrative-metadata) for a record at the command line:

1. run the `admin-record` [Development Task](/docs/dev.md#development-tasks)

The `preview-records` task will:

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/models.md#records)
- prompt interactively for which records to preview
- export selected records using the [Catalogue Item HTML](/docs/outputs.md#catalogue-item-output) Output

> [!NOTE]
> XML and JSON versions of items and related items are not available in previews.
>
> Links to a generic 'x' item will be used as a placeholder for other items.

The `admin-record` task will:

- accept an identifier to an existing record, or path to a record configuration file via the command line
- prompt interactively to confirm the GitLab store is configured with the correct branch
- if needed, prompt interactively for a record identifier
  - the user accepts any initial selection set via the command line
  - the user indicates they're finished selecting records
- load the record from the [GitLab Store](/docs/stores.md#gitlab-store) or from the given file path
- output any administration metadata for the loaded record

## Interactive record publishing workflow

Semi-automated workflows with interactive prompts for required information are available to:

- [Import](#import-records), [Build](#build-static-site) and [Verify](#verify-static-site) sets of
  [Manually Authored](#create-records) records, creating a changeset (merge request) and publishing to the testing site
- merge, [Build](#build-static-site) and [Verify](#verify-static-site) approved changesets, publishing to the live site

> [!NOTE]
> This workflow is intended as a convenience for the Business As Usual (BAU) process of publishing records. It will not
> fit all use-cases and requires an associated GitLab issue.
>
> To publish records on a schedule, use the [Non-interactive Workflow](#non-interactive-record-publishing-workflow)
> instead.
>
> For other use-cases, combine individual record related tasks as needed.

### Interactive record publishing workflow - testing

To publish records to the testing catalogue:

1. ensure a suitable GitLab issue exists to track publishing the records [1]
1. ensure JSON configurations for these records exist in the `import/` directory (see [Create Records](#create-records))
1. run the `workflow-testing` [Development Task](/docs/dev.md#development-tasks)
1. repeat this process (using the [`select-records`](#update-records) task to get the now existing records for editing)
   until the record author is happy to publish live (by approving the merge request for the related changeset)

> [!NOTE]
> This workflow will comment on GitLab tracking issue when creating the changeset. The Lantern GitLab bot user MUST
> have at least reporter permissions within the relevant project to do this. Project memberships SHOULD be defined via
> [Infrastructure as Code](/docs/infrastructure.md#infrastructure-as-code).

The `workflow-testing` task calls and coordinates other tasks to:

1. if used, process records for resources authored in the Zap ⚡️editor (via the [`zap-records`](#import-records) task)
1. prompt for an issue URL to use as a changeset identifier and branch name
   - ensure the selected issue URL is for publishing the record(s), rather than an issue for authoring [1]
1. commit new and/or updated records (via the [`import-records`](#import-records) task) to the changeset branch
1. if needed, create a merge request for the changeset branch, adding the record author as a reviewer
1. export committed records to the testing site (via the [`build-records`](#build-static-site) task)
1. verify committed records in the testing site (via the [`verify-records`](#verify-static-site) task)
1. post a comment listing the records changed, preview URLs and links to the merge request
1. if needed, post a comment on the issue with a link to the changeset merge request
1. save the verification report as a timestamped JSON file in the `workflow_results/testing` directory

[1]

For example, a Helpdesk issue may exist to track the request for a product, which is then set as a GitLab issue within
its metadata record to provide context. When ready for publishing, a separate Mapping Coordination issue may be created.

In this case, the Mapping Coordination issue SHOULD be used in this workflow (as an '< OTHER >' value), *not* the
Helpdesk issue recorded in the record.

### Interactive record publishing workflow - live

To publish records to the live catalogue:

1. ensure records have been published via the `workflow-testing` [Development Task](/docs/dev.md#development-tasks)
1. ensure the record author has approved the merge request for the changeset to be published
1. remove the draft status for the merge request
1. run the `workflow-live` [Development Task](/docs/dev.md#development-tasks)

The `workflow-live` task calls and coordinates other tasks to:

1. prompt for the changeset (merge request) to confirm (merge)
   1. the workflow will check the merge request is not a draft and has approval
1. merge the changeset into main
1. export changeset records to the live site (via the [`build-records`](#build-static-site) task)
1. invalidate changeset records in the live site (via the [`invalidate-records`](#update-records) task)
1. verify changeset records in the live site (via the [`verify-records`](#verify-static-site) task)
1. post a comment listing the item and alias URLs for published records in the changeset issue
1. save the verification report as a timestamped JSON file in the `workflow_results/live` directory

## Non-interactive record publishing workflow

A workflow is available to [Import](#import-records) and [Build](#build-static-site) sets of records updated on a
schedule by other projects using the [Workstation module](#workstation-module).

> [!IMPORTANT]
> This workflow is intended for routine updates to records managed by automated systems.
>
> To publish ad-hoc, manually authored records, use the [Interactive Workflow](#interactive-record-publishing-workflow).
>
> For other use-cases, combine individual record related tasks as needed.

The workflow:

- parses, validates and filters records from the given input path, such that only valid records that have changed are
  processed (changes are determined by comparing a SHA1 hash of the record content against the remote records store)
- creates a new branch and associated merge request in the remote records store if needed
- commits records to this branch
- calls non-global [Outputs](/docs/architecture.md#outputs) [1] only and publishes untrusted and trusted content
- if set, calls a [Webhook](#non-interactive-record-publishing-workflow---webhook) with workflow output

> [!TIP]
> The workflow will automatically recreate the branch and merge request if needed.
>
> The configured branch CAN be periodically squashed and merged to the default branch to prevent drift (e.g. nightly),
> but this workflow does not provide that functionality.

[1] Global outputs are not called because:

- the [Site Index](/docs/outputs.md#site-index-output)) Output for example only includes records from the Store passed
  to it, which would be limited to records managed by the workflow, clobbering outputs including other (all) expected
  records and giving incomplete results
- calling exporters such as the [Site Pages Exporter](/docs/outputs.md#site-resources-output) is unnecessary, given
  they are not sensitive to record changes

### Non-interactive record publishing workflow - bootstrapping

Perform these actions manually to set up the workflow for your application:

1. export a set of JSON encoded record files to a directory
2. import and publish these records using the [Interactive Workflow](#interactive-record-publishing-workflow):
   - commit to the `main` branch
   - this adds new records to global exporters (e.g. the [Site Index](/docs/outputs.md#site-index-output) Output)
   - this adds new records under any parent collections or other container resources
3. then follow the routine usage instructions for ongoing updates

### Non-interactive record publishing workflow - routine usage

Configure your application to perform these actions as frequently as needed:

1. export a set of JSON encoded record files to a directory
2. call `/data/magic/projects/lantern/live/tasks/pub-cat` with required arguments [1]

> [!WARNING]
> This will publish any records to the live catalogue.
>
> To publish to the testing catalogue, call `/data/magic/projects/lantern/testing/tasks/pub-cat`.

[1] Example usage script:

> [!NOTE]
> Change `SITE`, `PROJECT` and `PROJECT_SLUG` to relevant values.

```shell
#!/usr/bin/env bash
set -e -u -o pipefail

PUB_CAT_PATH="/data/magic/projects/PROJECT-SLUG/prod/exports/records"
# 'live' or 'testing'
PUB_CAT_SITE="live"
PUB_CAT_BRANCH="auto-PROJECT_SLUG"
# 'Automated publishing changeset: ' will always be prefixed to the MR title
PUB_CAT_MR_TITLE="Updates from PROJECT"
PUB_CAT_MR_MESSAGE="..."
PUB_CAT_COMMIT_TITLE="Updating PROJECT records"
PUB_CAT_COMMIT_MESSAGE="Routine update to reflect latest extents."
PUB_CAT_AUTHOR_NAME="PROJECT_SLUG"
PUB_CAT_AUTHOR_EMAIL="magicdev@bas.ac.uk"
# Optional
PUB_CAT_WEBHOOK="https://example.com/webhook"

/data/magic/projects/lantern/prod/tasks/pub-cat \
--path "$PUB_CAT_PATH" \
--site "$PUB_CAT_SITE" \
--changeset-base "$PUB_CAT_BRANCH" \
--changeset-title "$PUB_CAT_MR_TITLE" \
--changeset-message "$PUB_CAT_MR_MESSAGE" \
--commit-title "$PUB_CAT_COMMIT_TITLE" \
--commit-message "$PUB_CAT_COMMIT_MESSAGE" \
--author-name "$PUB_CAT_AUTHOR_NAME" \
--author-email "$PUB_CAT_AUTHOR_EMAIL" \
--webhook "$PUB_CAT_WEBHOOK"
```

### Non-interactive record publishing workflow - webhook

An optional webhook can be provided which will be called if any records are committed as part of the workflow. The
configured URL will be called as a POST request with a JSON payload containing:

- merge request and commit URLs
- new and/or updated record file identifiers
- statistics about the number of files created and/or updated)

Payload JSON [Schema and Example](/resources/scripts/non-interactive-publishing-workflow-schema.json)
(for 2 committed records, one new, one updated).

## Import records

To import a set of new and/or updated records:

1. copy record configurations as JSON files to the `import/` directory
2. run the `zap-records` [Development Task](/docs/dev.md#development-tasks) if importing records from the Zap ⚡️editor
3. run the `import-records` [Development Task](/docs/dev.md#development-tasks)
4. create a merge request for the changeset branch in the [Records Repository](/docs/infrastructure.md#gitlab)
5. after appropriate review, merge the changes into `main`

<!-- pyml disable md028 -->
> [!NOTE]
> Records are considered existing if a record with the same `file_identifier` exists.

> [!NOTE]
> Records cannot be commited directly to the 'main' branch.

> [!TIP]
> All records in the `import/` directory will be committed together. Consider splitting unrelated changes separately.
<!-- pyml enable md028 -->

The `zap-records` task (if used) will:

- update collections referenced in records, to create back-references and update the bounding extent of the collection
- update metadata datestamps in any revised records, and the edition in any revised collection records
- upgrade records to the MAGIC discovery profile v2
- set resource permissions in [Administration Metadata](/docs/libraries.md#record-administrative-metadata) from any
  resource access constraints in the record
- move any GitLab issue identifiers to administration metadata
- save revised records to the import directory and remove original records, ready for import

<!-- pyml disable md028 -->
> [!CAUTION]
> Creating administrative metadata from access constraints is not safe where the origin of a record is not trusted.

> [!NOTE]
> Only open access (unrestricted) access constraints are converted to resource access permissions in administrative
> metadata. Metadata access permissions are always set to open access (unrestricted).
>
> Other constraints are ignored and will need setting via the `restrict-records`
> [Development Task](/docs/dev.md#development-tasks).
<!-- pyml enable md028 -->

The `import-records` task will:

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/models.md#records)
- prompt interactively to confirm the GitLab store is configured with the correct branch
- prompt interactively for commit information:
  - a changeset title and description (which will open your configured `$EDITOR`)
  - a changeset author name and email
- push validated records to the [GitLab Store](/docs/stores.md#gitlab-store), committing changes to the configured branch
- log the commit URL, if a commit was made (i.e. if one or more records are new or is different to its existing version)
- delete any imported record files

## Update records

- run the `select-records` [Development Task](/docs/dev.md#development-tasks)
- update records in the import directory as per the [Record Authoring](/docs/libraries.md#record-authoring) section
- if changing access permissions, run the `restrict-records` [Development Task](/docs/dev.md#development-tasks)
- run the [Import Records](#import-records) workflow
- run the `invalidate-records` [Development Task](/docs/dev.md#development-tasks)

> [!CAUTION]
> The catalogue does not enforce metadata access permissions. They will always evaluate to open access (unrestricted).

The `invalidate-record` task will:

- take one or more resource identifiers as command line arguments
- create a CloudFront invalidation in the static site for all keys under each resource identifier prefix

E.g. for a resource ID `123`, an invalidation is made for `/records/123/*` and `/items/123/*`.

> [!NOTE]
> The CloudFront distribution ID is read from [Infrastructure as Code](/docs/infrastructure.md#infrastructure-as-code).

### Replacing record thumbnails

To replace a thumbnail for an existing resource:

- overwrite the thumbnail file using the AWS CLI [1]
- run the `thumbnail-invalidate` [Development Task](/docs/dev.md#development-tasks)

> [!TIP]
> If the thumbnail file name or file type has changed - select, and replace the relevant graphic overview URL in,
> the record for the resource as per the [Update](#update-records) workflow instead.

The `thumbnail-invalidate` task will:

- take a resource identifier as a command line argument
- create a CloudFront invalidation in the BAS CDN for all keys under the resource identifier prefix

E.g. for a resource ID `123`, an invalidation is made for `/add-catalogue/0.0.0/img/items/123/*`.

> [!NOTE]
> The CloudFront distribution ID is read from [Infrastructure as Code](/docs/infrastructure.md#infrastructure-as-code).

[1]

```text
$ aws s3 cp ./overview.png s3://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/{file_identifier}/
```

### Replacing record artefacts

To replace file artefacts included in an existing resource:

- use the Zap ⚡️editor to select (but not upload) the replacement artefact to get an updated distribution option
- select the record for the resource as per the generic update workflow
- replace the relevant distribution option, preserving the transfer option URL (and amending if renamed)
  - this should ensure the format and size are updated if needed but double-check this
- continue following the generic update workflow to complete updating the record

### Selecting records

The `select-records` task will:

- accept identifiers for existing record identifiers via the command line
- prompt interactively to confirm the GitLab store is configured with the correct branch
- repeatedly prompt interactively for any additional the identifier(s) of existing records until:
  - the user accepts any initial selection set via the command line
  - the user indicates they're finished selecting records
- confirm the selected file identifiers to load
- get selected records from the [GitLab Store](/docs/stores.md#gitlab-store)
- save selected record configurations as JSON files to the `import/` directory

> [!TIP]
> Record identifiers are intentionally flexible, supporting various catalogue URLs, file names, etc. optionally as a
> comma and/or space separated list (e.g. `https://example.com/items/123/, 123.json`). Run task for supported formats.

### Setting record issues

The `gitlab-record` task will:

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/models.md#records)
- prompt interactively for which record to update
- via an editor, prompt interactively for which GitLab issues to include in the selected record
  - issues should be listed on separate lines as canonical GitLab issue URLs (not short references)
  - existing issues will be pre-populated to either append or remove
- update the [Administrative Metadata](/docs/libraries.md#record-administrative-metadata) in the selected record with
  the specified issues
- save the updated record configuration as a JSON file to the `import/` directory

### Setting record permissions

The `restrict-records` task will:

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/models.md#records)
- prompt interactively for which records to update
- prompt interactively for which metadata and resource permissions to set
- update the [Administrative Metadata](/docs/libraries.md#record-administrative-metadata) in selected records with the
  selected access permission
- save updated record configurations as JSON files to the `import/` directory

<!-- pyml disable md028 -->
> [!CAUTION]
> The catalogue does not enforce metadata access permissions. They will always evaluate to open access (unrestricted).

> [!NOTE]
> Only 'Open Access' and 'BAS Staff' access permissions are supported by this task.
<!-- pyml enable md028 -->

## Build static site

To build the static site for the [BAS Data Catalogue](/docs/architecture.md#bas-data-catalogue):

1. set the options in `tasks/records_build.py` for whether to export the site locally and/or publish remotely
1. run the `build-records` [Development Task](/docs/dev.md#development-tasks)

The `build-records` task will:

- load some or all or records from the [GitLab Store](/docs/stores.md#gitlab-store) into a
  [Site](/docs/architecture.md#sites)
- if the `target` option is 'local', export the site to a local path
- if the `target` option is 'remote', export the site to the relevant BAS Catalogue environment set by the `env` option

## Verify static site

To [Verify](/docs/monitoring.md#site-verification) for the
[BAS Data Catalogue](/docs/architecture.md#bas-data-catalogue):

1. set the options in `tasks/records_verify.py` for the site to check (`base_url`)
1. run the `verify-records` [Development Task](/docs/dev.md#development-tasks)

The `verify-records` task will:

- load some or all or records from the [GitLab Store](/docs/stores.md#gitlab-store) into a
  [Verification](/docs/monitoring.md#site-verification) instance
- run [Verification checks](/docs/monitoring.md#verification-checks) against the generated static site
- compile a [Verification report](/docs/monitoring.md#verification-report)
- if the `target` option is 'local', export the report to a local path
- if the `target` option is 'remote', export the report to the relevant BAS Catalogue environment set by the `env` option

## Apply record details to ArcGIS item

To update an ArcGIS Online item with supported properties from a catalogue record (via an
[ArcGOS (Catalogue) Item](/docs/models.md#arcgis-items)):

1. run the `esri-item` [Development Task](/docs/dev.md#development-tasks)

> [!TIP]
> Use the `esri-record` [Development Task](/docs/dev.md#development-tasks) instead to add ArcGIS distribution options
> to records.

The `esri-item` task will:

- load a source record from the [GitLab Store](/docs/stores.md#gitlab-store)
- load an existing target item from ArcGIS Online via the ArcGIS REST API
- simulate a ArcGIS content item from the source record, to allow comparison against the target
- update the target item's metadata, sharing level and/or a subset of in-scope properties as needed

<!-- pyml disable md028 -->
> [!CAUTION]
> This task will update the target item's sharing level based on the resource access permissions set in the source
> record's administration metadata.

> [!WARNING]
> This task can access any item in the BAS AGOL subscription.

> [!NOTE]
> This task only supports items hosted in ArcGIS Online.
<!-- pyml enable md028 -->

## Upgrade records

To update records in bulk (e.g. to a new profile version, or to adopt new conventions, etc.):

1. create a new [Development Task](/docs/dev.md#record-upgrade-tasks) named `upgrade-records`
1. run the `upgrade-records` [Development Task](/docs/dev.md#development-tasks) to initialise an upgrade directory
1. run the `upgrade-records` task again to process records in the upgrade directory
1. store the upgrade report
1. [Import](#import-records) the upgraded records

> [!TIP]
> The upgrade directory SHOULD be tracked in a local Git repo to easily compare and rollback changes.

The `upgrade-records` task will:

- create an upgrade directory and dump all records from the [GitLab Store](/docs/stores.md#gitlab-store) as JSON files
- capture the SHA1 hashes of all records to allow detecting changes after processing as `hashes_orginal.json`
- process records as needed and writing back to the upgrade directory
- capture the SHA1 hashes of all (processed) records as `hashes_working.json` for comparison
- generate a report of changes as `report_data.json` and `report_rendered.md`

## Rotate access tokens

See [Deployment](/docs/deployment.md#rotating-access-tokens) documentation.

## Troubleshooting

### Administration metadata keys

Run the `keys-check` [Development Task](/docs/dev.md#development-tasks) to verify the current administration metadata
keys work. No output will be returned if working.
