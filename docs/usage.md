# Lantern - Usage

> [!NOTE]
> These are draft workflows and are not intended for use by general end-users.

## Setup

<!-- pyml disable md028 -->
> [!IMPORTANT]
> Ensure you have a working [Local Development Environment](/docs/dev.md#local-development-environment) available with
> a valid [Configuration](/docs/config.md#config-options) (including access tokens) before running these instructions.

> [!TIP]
> Run the `config-check` [Development Task](/docs/dev.md#development-tasks) to validate the current configuration.
<!-- pyml enable md028 -->

## Logging

Log messages at or above the *warning* level are written to `stderr` by default. The logging level can be changed via
the `LOG_LEVEL` [Config Option](/docs/config.md#config-options) set to a valid Python logging level.

## Workstation module

A minimal installation of this project is available on the BAS central workstations for integrating directly with other
projects to manage and/or publish records.

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

- ensure MAGIC environment modules are included in your module search path [1]
- load the `lantern` module `module load lantern`

> [!TIP]
> This will load the latest stable [Release](/README.md#releases).
>
> To load a preview of the next release (built from `main`), run `module load lantern/0.0.0.STAGING` instead.

[1]

To include MAGIC modules in your current session:

```text
$ module use --append /data/magic/.Modules/modulefiles
```

To always include MAGIC modules, add the above to your shell profile (e.g. in `~/.bash_profile`):

```shell
# include MAGIC custom environment modules
type module >/dev/null 2>&1
if [ $? -eq 0 ]; then
    module use --append /data/magic/.Modules/modulefiles
    echo "MAGIC custom modules are available"
fi
```

## Create records

1. create new records, (or clone a record using the `clone-record` [Development Task](/docs/dev.md#development-tasks))
   as JSON files in the import directory as per the [Record Authoring](/docs/libraries.md#record-authoring) section
1. use the `esri-record` [Development Task](/docs/dev.md#development-tasks) to include distribution options for any
   Esri ArcGIS Online items that apply to records
1. run the [Import Records](#import-records) workflow

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
- `identification.identifier[namespace='data.bas.ac.uk']` (data catalogue identifier)
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
- load the record from a [GitLab Store](/docs/stores.md#gitlab-store) or from the given file path
- get details for the ArcGIS item via the ArcGIS REST API
- create distribution options for the layer and service based on these details and catalogue conventions
- add these options to the record where they do not yet exist

## View records

To preview new or edited records before importing them:

1. copy record configurations as JSON files to the `import/` directory
2. run the `preview-records` [Development Task](/docs/dev.md#development-tasks) and select which records to preview
3. run the [Local development web server](/docs/dev.md#local-development-web-server) to records as items

To view [Administration Metadata](/docs/libraries.md#record-administrative-metadata) for a record:

1. run the `admin-record` [Development Task](/docs/dev.md#development-tasks)

The `preview-records` task will:

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/data-model.md#records)
- prompt interactively for which records to preview
- export selected records using the [HTML resource exporter](/docs/exporters.md#html-resource-exporter)

> [!NOTE]
> XML and JSON versions of items are not available in previews.
>
> Related items are not available in previews. Links to a generic 'x' item will be used as a placeholder.

The `admin-record` task will:

- accept an identifier to an existing record, or path to a record configuration file via the command line
- prompt interactively to confirm the GitLab store is configured with the correct branch
- if needed, prompt interactively for a record identifier
  - the user accepts any initial selection set via the command line
  - the user indicates they're finished selecting records
- load the record from a [GitLab Store](/docs/stores.md#gitlab-store) or from the given file path
- output any administration metadata for the loaded record

## Interactive record publishing workflow

A semi-automated workflow is available to [Import](#import-records), [Build](#build-static-site) and
[Verify](#verify-static-site) sets of [Manually Authored](#create-records) records using interactive prompts for
required information.

> [!NOTE]
> This workflow is intended as a convenience for the Business As Usual (BAU) process of publishing records from GitLab
> issues. It will not fit all use-cases.
>
> To publish records on a schedule, use the [Non-interactive Workflow](#non-interactive-record-publishing-workflow)
> instead. For other use-cases, combine individual record related tasks as needed.

To publish records in the testing catalogue:

1. copy record configurations as JSON files to the `import/` directory (see [Create Records](#create-records))
1. run the `records-workflow` [Development Task](/docs/dev.md#development-tasks)
1. repeat this process (using the [`select-records`](#update-records) task to get the now existing records) until the
   record author is happy for them to be published live

> [!NOTE]
> The Lantern GitLab bot user MUST have at least reporter permissions to post comments on a tracking issue (if specified).
> Project access SHOULD be defined via [Infrastructure as Code](/docs/infrastructure.md#infrastructure-as-code).

The `records-workflow` task calls and coordinates other tasks to:

1. process records authored in the Zap ⚡️editor (via the [`zap-records`](#import-records) task)
1. prompt for an optional issue URL to use as a changeset identifier and branch name [1]
1. commit new and/or updated records (via the [`import-records`](#import-records) task)
1. create a merge request for the committed records if one does not exist for the changeset
1. publish committed records to the testing site (via the [`build-records`](#build-static-site) task)
1. verify committed records in the testing site (via the [`verify-records`](#verify-static-site) task)
1. if an issue was selected, post a comment listing the records changed, preview URLs and links to the merge request

> [!NOTE]
> As a precaution, the `records-workflow` [Development Task](/docs/dev.md#development-tasks) will not run if the
> integration S3 bucket is selected.

To publish records to the live catalogue:

1. merge the relevant merge request for the changeset into `main`
1. switch the `AWS_S3_BUCKET` config option to the production bucket
1. run the `build-records` [Development Task](/docs/dev.md#development-tasks) with the publish option enabled
1. switch the `AWS_S3_BUCKET` config option back to the integration bucket

[1] If needed, ensure the selected issue URL is for publishing the record(s), rather than an issue for authoring.

For example, a Helpdesk issue may exist to track the request for a product, which is then set as a GitLab issue within
its metadata record to provide context. When ready for publishing, a separate Mapping Coordination issue may be created.

In this case, the Mapping Coordination issue should be used in this workflow (as an '< OTHER >' value), *not* the
Helpdesk issue recorded in the record.

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
- calls the [Records](/docs/exporters.md#records-resource-exporter) exporter (only [1]) and publishes to S3 and secure
  hosting (for public and trusted content respectively)
- if set, calls a [Webhook](#non-interactive-record-publishing-workflow---webhook) with workflow output

> [!TIP]
> The configured branch CAN be periodically squashed and merged to the default branch to prevent drift (e.g. nightly),
> but does not provide this functionality.
>
> The workflow will automatically recreate the branch and merge request as needed.

[1] Other exporters are not called because:

- the [Site Index Exporter](/docs/exporters.md#site-index-exporter)) for example only includes records passed to it,
  which would be limited to records managed by the workflow, clobbering outputs including other (all) expected records
  and giving incomplete results
- calling exporters such as the [Site Pages Exporter](/docs/exporters.md#site-pages-exporter) is unnecessarily, given
  they are not sensitive to record changes

### Non-interactive record publishing workflow - bootstrapping

Perform these actions manually to set up the workflow for your application:

1. export a set of JSON encoded record files to a directory
2. import and publish these records using the [Interactive Workflow](#interactive-record-publishing-workflow):
   - commit to the `main` branch
   - this adds new records to global exporters (e.g. the [Site Index Exporter](/docs/exporters.md#site-index-exporter))
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
> Change `PROJECT` and `PROJECT_SLUG` to relevant values.

```shell
#!/usr/bin/env bash
set -e -u -o pipefail

PUB_CAT_PATH="/data/magic/projects/PROJECT-SLUG/prod/exports/records"
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

## Update records

- run the `select-records` [Development Task](/docs/dev.md#development-tasks)
- update records in the import directory as per the [Record Authoring](/docs/libraries.md#record-authoring) section
- if changing access permissions, run the `restrict-records` [Development Task](/docs/dev.md#development-tasks)
- run the [Import Records](#import-records) workflow

> [!CAUTION]
> The catalogue does not enforce metadata access permissions. They will always evaluate to open access (unrestricted).

### Replacing record thumbnails

To replace the thumbnail for an existing resource:

```text
% aws s3 cp $IMAGE_FILE s3://cdn.web.bas.ac.uk/add-catalogue/0.0.0/img/items/$FILE_IDENTIFIER/
% aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/add-catalogue/0.0.0/img/items/$FILE_IDENTIFIER/$IMAGE_FILE"
% aws cloudfront get-invalidation --distribution-id $DISTRIBUTION_ID --id $INVALIDATION_ID --query "Invalidation.Status" --output text
InProgress
# ...
% aws cloudfront get-invalidation --distribution-id $DISTRIBUTION_ID --id $INVALIDATION_ID --query "Invalidation.Status" --output text
Completed
```

Where:

- `$IMAGE_FILE` is the local path to the replacement thumbnail file
- `$FILE_IDENTIFIER` is the identifier of the resource being updated
- `$DISTRIBUTION_ID` is the CloudFront distribution hosting catalogue thumbnails
- `$INVALIDATION_ID` is returned by the `create-invalidation` command

If the thumbnail file name has changed:

- select the record for the resource as per the generic update workflow
- replace the relevant graphic overview URL
- continue following the generic update workflow to complete updating the record

### Replacing record artefacts

To replace an artefact for an existing resource:

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
- get selected records from a [GitLab Store](/docs/stores.md#gitlab-store)
- save selected record configurations as JSON files to the `import/` directory

> [!TIP]
> Record identifiers are intentionally flexible, supporting various catalogue URLs, file names, etc. optionally as a
> comma and/or space separated list (e.g. `https://example.com/items/123/, 123.json`). Run task for supported formats.

### Setting record permissions

The `restrict-records` task will:

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/data-model.md#records)
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

## Import records

To import a set of new and/or updated records:

1. copy record configurations as JSON files to the `import/` directory
2. run the `zap-records` [Development Task](/docs/dev.md#development-tasks) if importing records from the Zap ⚡️editor
3. run the `import-records` [Development Task](/docs/dev.md#development-tasks)

<!-- pyml disable md028 -->
> [!NOTE]
> Records are considered existing if a record with the same `file_identifier` exists.

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

- parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/data-model.md#records)
- prompt interactively to confirm the GitLab store is configured with the correct branch
- prompt interactively for commit information:
  - a changeset title and description (which will open your configured `$EDITOR`)
  - a changeset author name and email
- push validated records to a [GitLab Store](/docs/stores.md#gitlab-store), committing changes to the configured branch
- log the commit URL, if a commit was made (i.e. if one or more records are new or is different to its existing version)
- delete any imported record files

## Build static site

To build the [Static Site](/docs/architecture.md#static-site):

1. set the options in `tasks/records_build.py` for whether to export the site locally and/or publish remotely
1. run the `build-records` [Development Task](/docs/dev.md#development-tasks)

> [!IMPORTANT]
> If publishing remotely, check the `AWS_S3_BUCKET` config option is set to the intended bucket name.

The `build-records` task will:

- load some or all or records from a [GitLab Store](/docs/stores.md#gitlab-store) into a
  [Site Exporter](/docs/exporters.md#site-exporter)
- if the export option is enabled, output the static site to a local path
- if the publish option is enabled:
  - upload public static site content to a remote S3 bucket
  - upload [Trusted Content](/docs/exporters.md#trusted-publishing) to the
    [BAS Operations Data Store 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/ops-data-store) hosting server

## Verify static site

To [Verify](/docs/monitoring.md#site-verification) the [Static Site](/docs/architecture.md#static-site):

1. set the options in `tasks/records_verify.py` for the site to check (`base_url`)
1. run the `verify-records` [Development Task](/docs/dev.md#development-tasks)

The `verify-records` task will:

- load some or all or records from a [GitLab Store](/docs/stores.md#gitlab-store) into a
  [Verification Exporter](/docs/exporters.md#verification-exporter)
- run [Verification checks](/docs/monitoring.md#verification-checks) against the generated static site
- compile and export/publish a [Verification report](/docs/monitoring.md#verification-report)

## Rotate access tokens

See [Deployment](/docs/deployment.md#rotating-access-tokens) documentation.

## Troubleshooting

### Administration metadata keys

Run the `keys-check` [Development Task](/docs/dev.md#development-tasks) to verify the current administration metadata
keys work. No output will be returned if working.
