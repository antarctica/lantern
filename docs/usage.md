# Lantern - Usage

> [!NOTE]
> These are draft workflows and are not intended for use by general end-users.

## Setup

<!-- pyml disable md028 -->
> [!IMPORTANT]
> Ensure you have a working [Local Development Environment](/docs/dev.md#local-development-environment) available with
> a valid [Configuration](/docs/config.md#config-options) before running these instructions.

> [!TIP]
> Run the `config-check` [Development Task](/docs/dev.md#development-tasks) to validate the current configuration.
<!-- pyml enable md028 -->

## Logging

Log messages at or above the *warning* level are written to `stderr` by default. The logging level can be changed via
the `LOG_LEVEL` [Config Option](/docs/config.md#config-options) set to a valid Python logging level.

## Creating records

1. create new records as JSON files in the import directory as per the
   [Record Authoring](/docs/data-model.md#record-authoring) section
2. then run the [Import Records](#import-records) workflow

## Updating records

For updating individual records:

- run the `select-records` [Development Task](/docs/dev.md#development-tasks)
- update records in the import directory as per the [Record Authoring](/docs/data-model.md#record-authoring) section
- then run the [Import Records](#import-records) workflow

For updating large numbers of records from an external working copy of the records repository:

- update records in the working copy as per the [Record Authoring](/docs/data-model.md#record-authoring) section
- run the `load-records` [Development Task](/docs/dev.md#development-tasks)
- then run the [Import Records](#import-records) workflow

## Import records

To import a set of new or updated records:

1. copy record configurations as JSON files to the `import/` directory
1. run the `import-records` [Development Task](/docs/dev.md#development-tasks)

<!-- pyml disable md028 -->
> [!NOTE]
> Records are considered existing if a record with the same `file_identifier` exists.

> [!TIP]
> All records in the `import/` directory will be committed together. Consider separating unrelated changes by splitting
> records into sets and running this workflow multiple times.
<!-- pyml enable md028 -->

The `import-records` task will:

1. prompt for information to use when commiting updates:
   - a changeset title and description (which will open your `$EDITOR`)
   - an author name and email
1. populate a [GitLab Store](/docs/stores.md#gitlab-store) (to check for existing records and updating related records)
1. parse and validate `import/*.json` files (ignoring subfolders) as [Records](/docs/data-model.md#records)
1. process parsed records:
   1. where a record has a 'parent collection' aggregation targeting one or more selected MAGIC managed collection:
      1. each target collection is updated to include a backref 'in collection' aggregation
      1. each target collection's bounding extent is updated to account for the record
   1. where any existing records have changed (including records from previous processing steps):
      1. the metadata revision date is updated
      1. if a collection, the revision date and edition are updated

## Build static site

To build the [Static Site](/docs/site.md):

1. set the options in `tasks/build.py` for whether to export the site locally and/or publish remotely
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
