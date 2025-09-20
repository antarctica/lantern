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

## Workstation module

A minimal installation of this project is available on the BAS central workstations for integrating directly with other
projects to manage and/or publish records.

> [!NOTE]
> This is a preview feature and does not directly relate to the workflows and tasks below.

To use this installation, you will need access to MAGIC custom environment modules in the module search path [1].

```text
$ ssh BAS_WORKSTATION
$ module load lantern
```

> [!TIP]
> This will load the latest stable [Release](/README.md#releases). To load a preview of the next release (built from
> `main`) use `module load lantern/0.0.0.STAGING`.

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

1. create new records as JSON files in the import directory as per the
   [Record Authoring](/docs/data-model.md#record-authoring) section
2. then run the [Import Records](#import-records) workflow

## Publishing records workflow

A workflow is available to [Import](#import-records), [Build](#build-static-site) and [Verify](#verify-static-site)
tasks for a set of new and/or updated records as a publishing workflow.

> [!IMPORTANT]
> This is intended as a convenience for the Business As Usual (BAU) process of publishing records from GitLab issues.
>
> For other use-cases, see the documentation for each individual task.

1. copy record configurations as JSON files to the `import/` directory
1. run the `records-workflow` [Development Task](/docs/dev.md#development-tasks)
1. verify the record author is happy with the changes in the integration environment
1. update the `AWS_S3_BUCKET` config option to the production bucket
1. run the `build-records` [Development Task](/docs/dev.md#development-tasks)

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

> [!IMPORTANT]
> Run the `zap-records` [Development Task](/docs/dev.md#development-tasks) first if importing records from the Zap ⚡️
> editor to:
>
> - update collections referenced in records
> - update metadata datestamps in any revised records, and edition in any revised collection records
> - save any revised records in the import directory and remove any original records exported from Zap ⚡️

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
