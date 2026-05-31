# Lantern - Proto-CLI Reference (Supplemental)

## Overview

<!-- pyml disable md028 -->
> [!IMPORTANT]
> This project does not include a formal CLI.
>
> The commands described here are [Development Tasks](/docs/dev.md#development-tasks) that resemble a CLI but are
> untested, standalone, scripts - which may be inconsistent in structure and behaviour and/or unstable.

> [!NOTE]
> Parts of this page are specific to the [BAS Data Catalogue](/docs/architecture.md#bas-catalogue).
<!-- pyml enable md028 -->

### Limitations

These [Development Tasks](/docs/dev.md#development-tasks) acting as CLI commands:

- MAY be changed or removed without warning
- MAY NOT be consistent in structure and behaviour (i.e. between each other)
- do not use a typical CLI structure (subcommands, autocompletion etc.)
- are not tested

### Summary

> [!NOTE]
> See the [Setup](/docs/usage.md#setup) section of the usage documentation before running these commands.

```yaml
# high-level publishing workflows
workflow-testing     Import records to testing site
workflow-live        Import records to live site

# single record commands
clone-record         Clone record from cache into import directory
supersede-record     Indicate a new record is the successor to another
issues-record        Set GitLab issues for a record
admin-record         View administrative metadata for a record
restrict-record      Set access permissions for a record
esri-record          Add Esri item distribution options to a record

# multiple records commands
select-records       Copy records from cache to import directory for editing
zap-records          Process Zap ⚡️ authored records from import directory
preview-records      Preview records as HTML items
import-records       Import records from directory
build-records        Build records as a catalogue site
check-records        Check static site and records contents
invalidate-records   Invalidate cached records in live site
upgrade-records      Upgrade records
bootstrap-records    Bootstrap a new records repo

# other commands
esri-item            Sync record details to an Esri item
site-invalidate      Invalidate cached content in live site
thumbnail-invalidate Invalidate cached item thumbnail in CDN

# utility commands
version              Show app version
config-check         Check app config
keys-check           Check admin meta keys
```

## Publishing workflow commands

> [!NOTE]
> These commands do not support any options or arguments, and only run interactively.
>
> See the [Usage](/docs/usage.md#publishing-workflows) documentation for information on how they work.

### `workflow-testing`

Import records to the testing site.

```shell
% workflow-testing
```

Calls and coordinates other tasks to:

1. process any records authored in the Zap ⚡️editor (via the [`zap-records`](#zap-records) command)
1. prompt for the issue URL to use as a changeset identifier and branch name
1. commit new and/or updated records (via the [`import-records`](#import-records) command) to the changeset branch
1. if needed, create a merge request for the changeset branch, adding the record author as a reviewer
1. export committed records to the testing site (via the [`build-records`](#build-records) command)
1. check committed records in the testing site (via the [`check-records`](#check-records) command)
1. optionally, post a comment listing the records changed, preview URLs and links in the changeset merge request
1. if needed and optionally, post a comment on the changeset issue with a link to the merge request
1. save check results as a timestamped JSON file in `./workflow_results/testing/`

### `workflow-live`

Import records to the live site.

```shell
% workflow-live
```

Calls and coordinates other tasks to:

1. prompt for an existing changeset (merge request) to complete
   1. the workflow will check the merge request has been approved and is not a draft
1. merge the changeset branch into main
1. export and invalidate all changeset records to the live site (via the [`build-records`](#build-records) command)
1. check changeset records in the live site (via the (via the [`check-records`](#check-records) command)
1. optionally, post a comment listing the item and alias URLs for published records in the changeset issue
1. save check results as a timestamped JSON file in `./workflow_results/live/`

## Single record commands

### `clone-record`

Clone record from cache into import directory.

```shell
% task clone-record --help
```

Examples:

```shell
# set source reference, with interactive conformation of other defaults
% task clone-record --source https://data.bas.ac.uk/items/a16dd760-6d99-4fba-825a-99b7409efb94/
# set destination path, branch and source/target record reference/identifier, without interaction
% task clone-record --force --path ./x --branch main --source ff622870-a0ce-418a-a9a4-5803e57bc83c --target 9dacc12b-3cdb-4e08-972f-fdf8e51896e3
```

These fields are updated when cloning a record:

- `file_identifier`
- `identification.identifier[namespace='lantern.data.bas.ac.uk']` (data catalogue identifier)
- `identification.supplemental_information[admin_metadata[id]]` (admin metadata ID to match the new `file_identifier`)

> [!NOTE]
> Other fields (such as citation, aliases, edition, title, admin gitlab issues, permissions, etc.) are not changed and
> may need updating.

### `supersede-record`

Indicate a new record is the successor to another.

```shell
% task supersede-record --help
```

These fields are updated in the predecessor record:

- `identification.aggregations[assocation='largerWorkCitation',initiative='collection']` (removed)
- `identification.abstract` (superseded note with link to successor appended)

These fields are updated in the successor record:

- `identification.aggregations[assocation='revisionOf']` (pointing to predecessor)
- `identification.aggregations[assocation='largerWorkCitation',initiative='collection']` (any from predecessor)

These fields are updated in any collection records the predecessor contained:

- `identification.aggregations[assocation='isComposedOf',initiative='collection']` (identifier updated to successor)

> [!NOTE]
> If working with a [`zap-records`](#zap-records) processed record, this command will separately update collections to
> correct back-references to the successor record. Other collection changes (e.g. extent updates) will need reapplying.

Examples:

```shell
# set current and successor records with default branch and import path, without interaction
% task supersede-record --force --current 76c35d79-3611-4a12-adbc-8a1ce45200df --successor ./import/88d2ff3f-b159-42a4-826d-183c5c5dde70.json
```

### `issues-record`

Set GitLab issues for a record.

```shell
% task issues-record --help
```

### `admin-record`

View administrative metadata for a record config file.

```shell
% task admin-record --help
```

> [!TIP]
> See the [`select-records`](#select-records) command to get record configs for existing records.

Examples:

```shell
# set record config, without interaction
% task admin-record --force --record import/ed1fe01c-951f-4979-8339-00748d6bfb0b.json
```

### `restrict-record`

Set access permissions for a record.

```shell
% task restrict-record --help
```

### `esri-record`

Add Esri ArcGIS Online item to a record as a distribution option.

```shell
% task esri-record --help
```

> [!TIP]
> See the [`esri-item`](#esri-item) command to do the opposite (update an AGOL item to based on a catalogue record).

Examples:

```shell
# set source record config and target item, without interaction
% task esri-record --force --record ./import/af4acf4d-af76-46f8-bc6a-928cf72fa9ae.json --target 27a7eda22cf249748502ddfc3d31d6bf
```

## Multiple records commands

### `select-records`

Copy records from cache to import directory for editing.

```shell
% task select-records --help
````

### `zap-records`

Process Zap ⚡️ authored records from import directory.

```shell
% task zap-records --help
```

At a high level, this command:

- updates collections referenced in records, to create back-references and update the bounding extent of collections
- updates the metadata datestamp in any updated records, as well as the edition in any revised collection records
- upgrades records to the [MAGIC Discovery profile](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/)
  v2 if needed
- sets resource permissions within [Administration Metadata](/docs/libraries.md#record-administrative-metadata) based
  on any resource access constraints in the record (not metadata access constraints, which are always ignored)
- moves any GitLab issue identifiers to administration metadata
- saves revised records to the import directory and remove original records, ready for import

<!-- pyml disable md028 -->
> [!CAUTION]
> Creating administrative metadata from access constraints is not safe where the origin of a record is not trusted.

> [!TIP]
> See also the [Restrict Record](#restrict-record) command to set administrative resource permissions once processed.
<!-- pyml enable md028 -->

### `preview-records`

Preview records as HTML items.

```shell
% task preview-records --help
```

<!-- pyml disable md028 -->
> [!NOTE]
>
> - XML and JSON versions of items and related items are not available in previews.
> - links to a generic 'x' item will be used as a placeholder for other items.

> [!NOTE]
> If the `--force` flag is set and a specific record isn't selected, previews for all loaded records will be generated.
<!-- pyml enable md028 -->

Examples:

```shell
# set a specific record config to preview, without interaction
% task preview-records --force --path import/ed1fe01c-951f-4979-8339-00748d6bfb0b.json
```

### `import-records`

Import records from a directory.

```shell
% task import-records --help
```

> [!NOTE]
>
> - records cannot be commited directly to the default branch.
> - the commit author name and email will default to `user.name` and `user.email` from Git config if available
> - successfully imported record files are removed from the import directory as potentially outdated revisions

Examples:

```shell
# set non-default branch (with interactive conformation or prompts for other values)
% task import-records --branch not-main
# set non-default import dir & branch, and commit identifier, without interactive conformation
% task import-records --force --path ./x --branch not-main --title "..." --message "..." --author-name "Connie Watson" --author-email "conwat@bas.ac.uk"
```

### `build-records`

Build records as a catalogue site.

```shell
% task builds-records --help
```

Examples:

```shell
# set branch, export target and record identifiers (site environment doesn't apply when target is 'local')
% task build-records --target local --branch main 2f8816ad-6cf8-421f-a4ee-d766bfb36b80
# prompt for branch, export site environment and select all record identifiers
% task build-records --env testing 61ab0a3e-ea8d-49fe-bce6-6bfd994f8ac4
```

### `check-records`

Check static site and records contents.

```shell
% task check-records --help
```

### `upgrade-records`

Upgrade records.

```shell
% task upgrade-records --help
```

### `bootstrap-records`

Bootstrap a records repo.

```shell
% task bootstrap-records --help
```

## Other commands

### `esri-item`

Sync record details to an Esri ArcGIS Online item.

```shell
% task esri-item --help
```

> [!CAUTION]
> This task will update the target item's sharing level based on the resource access permissions set in the source
> record's administration metadata, unless group sharing is used which is not supported.

Examples:

```shell
# set source record config and target item, without interaction
% task esri-item --force --source f89be0bb-28d4-4148-afad-4460459d0efd --target 9942249081204e619531cbe144ffcf6e
```

> [!TIP]
> See the [`esri-record`](#esri-record) command to do the opposite (add an AGOL item to a catalogue record).

### `site-invalidate`

Invalidate cached content in live site.

```shell
% task site-invalidate --help
```

Creates a CloudFront invalidation for specified S3 keys.

> [!TIP]
> See the [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/invalidation-specifying-objects.html)
> documentation for more information about cache invalidation keys.

Examples:

```shell
# invalidate all cached content
% task site-invalidate --key '/*'
# invalidate all record outputs
% task site-invalidate --key '/items/*'  --key '/records/*'
```

### `thumbnail-invalidate`

Invalidate thumbnails for an item in the BAS CDN.

```shell
% task thumbnail-invalidate --help
```

<!-- pyml disable md028 -->
> ![NOTE]
> Item thumbnails are hosted in the BAS CDN (`cdn.web.bas.ac.uk`), which is a separate CloudFront distribution to the
> live catalogue site.
>
> The CloudFront distribution ID is read from [Infrastructure as Code](/docs/infrastructure.md#infrastructure-as-code).

> [!TIP]
> This command doesn't accept a `--force` argument for some reason.
<!-- pyml enable md028 -->

Examples:

```shell
# invalidate thumbnails for a specific item
% task thumbnail-invalidate --item 54b8c8d4-aef0-48d0-b4a2-97d02a8b6c0a
```

## Utility commands

### `version`

Print application version.

```shell
% task version
```

### `config-check`

Check and show app config.

```shell
% task config-check
```

### `keys-check`

Check admin metadata signing and encryption keys.

```shell
% task keys-check
```

> [!TIP]
> This command returns no output if keys are valid.
