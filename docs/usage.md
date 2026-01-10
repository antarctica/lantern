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

> [!NOTE]
> This is a preview feature and does not directly relate to the workflows and tasks below unless noted.

To use this installation, you will need access to MAGIC custom environment modules in the module search path [1].

```text
$ ssh BAS_WORKSTATION
$ module load lantern
```

> [!TIP]
> This will load the latest stable [Release](/README.md#releases).
>
> To load a preview of the next release (built from `main`) use `module load lantern/0.0.0.STAGING`.

[1]

To include modules once:

```text
$ module use --append /data/magic/.Modules/modulefiles
```

To include modules on login via a shell profile:

```shell
# include MAGIC custom environment modules
type module >/dev/null 2>&1
if [ $? -eq 0 ]; then
    module use --append /data/magic/.Modules/modulefiles
    echo "MAGIC custom modules are available"
fi
```

## Creating records

1. create new records, (or clone a record using the `clone-record` [Development Task](/docs/dev.md#development-tasks))
   as JSON files in the import directory as per the [Record Authoring](/docs/libraries.md#record-authoring) section
2. then run the [Import Records](#import-records) workflow

The `clone-record` task will:

1. prompt interactively for:
   - the identifier of an existing record (unless the `--source` command line argument is set)
   - the file identifier to use for the cloned record (unless the `--target` command line argument is set)
1. populate a [GitLab Store](/docs/stores.md#gitlab-store) with current [Records](/docs/data-model.md#records)
1. load the existing (source) record
1. duplicate the source record with the new (target) file identifier [1]
1. save the new record configuration as a JSON file to the `import/` directory

[1]

These fields are updated when duplicating a record:

- `file_identifier`
- `identification.identifier[namespace='data.bas.ac.uk']` (data catalogue identifier)
- `identification.supplemental_information.record_origin` (cloned from ...)

> [!NOTE]
> Other fields (such as citation, aliases, edition, title, etc.) will need updating after cloning.

## Interactive record publishing workflow

A semi-automated workflow is available to [Import](#import-records), [Build](#build-static-site) and
[Verify](#verify-static-site) sets of manually authored records using interactive prompts for required information.

> [!NOTE]
> This workflow is intended as a convenience for the Business As Usual (BAU) process of publishing records from GitLab
> issues. It will not fit all use-cases.
>
> To publish records on a schedule, use the [Non-interactive Workflow](#non-interactive-record-publishing-workflow)
> instead. For other use-cases, combine individual record related tasks as needed.

To preview records in the testing catalogue:

1. copy record configurations as JSON files to the `import/` directory (see [Creating Records](#creating-records))
1. run the `records-workflow` [Development Task](/docs/dev.md#development-tasks)

Repeat this process (using the [`select-records`](#updating-records) task to update the now existing records) as needed
until the record author is happy for them to be live.

To publish records to the production catalogue:

1. merge the relevant merge request for the changeset into `main`
1. update the `AWS_S3_BUCKET` config option to the production bucket
1. run the `build-records` [Development Task](/docs/dev.md#development-tasks) with the publish option enabled
1. update the `AWS_S3_BUCKET` config option back to the integration bucket

> [!NOTE]
> As a precaution, the `records-workflow` development task will only run if the integration S3 bucket is selected.

The `records-workflow` task calls and coordinates other tasks to:

1. process records authored in the Zap ⚡️editor (via the [`zap-records`](#import-records) task)
1. prompt for an issue URL to use as a changeset identifier and branch name
1. commit new and/or updated records (via the [`import-records`](#import-records) task)
1. creates a merge request for the committed records if one does not exist for the changeset
1. by default, publish committed records to the testing site (via the [`build-records`](#build-static-site) task)
1. by default, verify committed records in the testing site (via the [`verify-records`](#verify-static-site) task)
1. outputs text for use in a comment listing the records changed, preview URLs and links to the merge request

## Non-interactive record publishing workflow

A workflow is available to [Import](#import-records) and [Build](#build-static-site) sets of records updated on a
schedule by other projects as a background task.

> [!IMPORTANT]
> This workflow is intended for routine updates to records owned by automated systems.
>
> To publish ad-hoc, manually authored records, use the [Interactive Workflow](#interactive-record-publishing-workflow).
>
> For other use-cases, see the documentation for each individual task.

1. export a set of record configurations as JSON files to a directory
2. call `/data/magic/projects/lantern/prod/tasks/pub-cat` with required arguments [1]

> [!WARNING]
> This will publish any records to the production S3 bucket / catalogue environment.

This workflow is experimental with major limitations:

- record files must be accessible from the BAS central workstations
- publishing scripts must have access to the [Environment Module](#workstation-module) on the BAS central workstations
- no authentication or authorization is performed on calling scripts
- the workflow is locked to the production publishing environment

[1] Example script:

```shell
#!/usr/bin/env bash
set -e -u -o pipefail

PUB_CAT_PATH="/data/magic/projects/PROJECT/prod/exports/records"
PUB_CAT_COMMIT_TITLE="Updating PROJECT records"
PUB_CAT_COMMIT_MESSAGE="Routine update to reflect latest extents."
PUB_CAT_AUTHOR_NAME="PROJECT-SLUG"
PUB_CAT_AUTHOR_EMAIL="magicdev@bas.ac.uk"

/data/magic/projects/lantern/prod/tasks/pub-cat \
--path "$PUB_CAT_PATH" \
--commit-title "$PUB_CAT_COMMIT_TITLE" \
--commit-message "$PUB_CAT_COMMIT_MESSAGE" \
--author-name "$PUB_CAT_AUTHOR_NAME" \
--author-email "$PUB_CAT_AUTHOR_EMAIL"
```

## Updating records

- run the `select-records` [Development Task](/docs/dev.md#development-tasks)
- update records in the import directory as per the [Record Authoring](/docs/libraries.md#record-authoring) section
- if needing to change access permissions, run the `restrict-records` [Development Task](/docs/dev.md#development-tasks)
- then run the [Import Records](#import-records) workflow

The `select-records` task will:

1. repeatedly prompt interactively for the identifier(s) of existing records unless:
   - the user accepts an initial selection set via the command line
   - the user indicates they're finished selecting records
1. confirm the file identifiers to load after processing selected identifiers
1. populate a [GitLab Store](/docs/stores.md#gitlab-store)
1. save selected record configurations as JSON files in the `import/` directory

> [!TIP]
> Record identifiers are intentionally flexible, supporting various catalogue URLs, file names, etc. optionally as a
> comma and/or space separated list (e.g. `https://example.com/items/123/, 123.json`). Run task for supported formats.

The `restrict-records` task (if needed) will:

1. parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/data-model.md#records)
1. prompt interactively for which records to update
1. prompt interactively for which access permission to set
1. update the [Administrative Metadata](/docs/libraries.md#record-administrative-metadata) in selected records with the
   selected access permission
1. save updated record configurations as JSON files in the `import/` directory

> [!NOTE]
> Only 'Open Access' and 'BAS Staff' access permissions are supported by this task.

## Import records

To import a set of new or updated records:

1. copy record configurations as JSON files to the `import/` directory
2. run the `zap-records` [Development Task](/docs/dev.md#development-tasks) if importing records from the Zap ⚡️editor
3. run the `import-records` [Development Task](/docs/dev.md#development-tasks)

<!-- pyml disable md028 -->
> [!NOTE]
> Records are considered existing if a record with the same `file_identifier` exists.

> [!TIP]
> All records in the `import/` directory will be committed together. Consider splitting unrelated changes into sets and
> importing each separately.
<!-- pyml enable md028 -->

The `zap-records` task (if applicable) will:

1. update collections referenced in records to create back-references and update the bounding extent of the collection
1. update metadata datestamps in any revised records, and edition in any revised collection records
1. create missing [Administrative Metadata](/docs/libraries.md#record-administrative-metadata) based on access
   constraints and any GitLab issue identifiers
1. save any revised records in the import directory and remove any original records

<!-- pyml disable md028 -->
> [!CAUTION]
> Creating administrative metadata from access constraints is not safe where the origin of a record is unknown.

> [!NOTE]
> Only open access (unrestricted) access constraints are converted to access permissions in administrative metadata.
> Other constraints are ignored and will need setting via the `restrict-records` [Development Task](/docs/dev.md#development-tasks).
<!-- pyml enable md028 -->

The `import-records` task will:

1. parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/data-model.md#records)
1. prompt interactively for commit information:
   - a changeset title and description (which will open your configured `$EDITOR`)
   - a changeset author name and email
1. populate a [GitLab Store](/docs/stores.md#gitlab-store) (to check for existing records and updating related records)
1. push validated records to the GitLab Store, committing any changes to the configured branch
1. log the URL to the commit, if a commit was made (i.e. records are new or different to an existing version)
1. delete any imported record files

## Build static site

To build the [Static Site](/docs/architecture.md#static-site):

1. set the options in `tasks/records_build.py` for whether to export the site locally and/or publish remotely
1. run the `build-records` [Development Task](/docs/dev.md#development-tasks)

> [!IMPORTANT]
> If publishing remotely, check the `AWS_S3_BUCKET` config option is set to the intended bucket name.

The `build-records` task will:

1. populate a [GitLab Store](/docs/stores.md#gitlab-store) with current [Records](/docs/data-model.md#records)
1. load all records into a [Site Exporter](/docs/exporters.md#site-exporter)
1. if the export option is enabled, build the static site and export it to a local path
1. if the publish option is enabled, build the static site and upload it to a remote S3 bucket

## Verify static site

To [Verify](/docs/monitoring.md#site-verification) the [Static Site](/docs/architecture.md#static-site):

1. set the options in `tasks/records_verify.py` for the site to check (`base_url`)
1. run the `verify-records` [Development Task](/docs/dev.md#development-tasks)

The `verify-records` task will:

1. populate a [GitLab Store](/docs/stores.md#gitlab-store) with current [Records](/docs/data-model.md#records)
1. load all records into a [Verification Exporter](/docs/exporters.md#verification-exporter)
1. run [Verification checks](/docs/monitoring.md#verification-checks) against the specified site
1. compile and export/publish a [Verification report](/docs/monitoring.md#verification-report)
