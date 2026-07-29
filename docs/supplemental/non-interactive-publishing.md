# Lantern - Non-interactive record publishing workflow (Supplemental)

## Overview

## Bootstrapping

To set up this workflow for an application:

1. [Generate](/docs/usage.md#creating-records) a set of JSON encoded record configurations as files in a directory
2. import and publish these records using the [Interactive Workflow](/docs/usage.md#interactive-publishing-workflow):
   - merge the changeset into `main`
   - this includes records in [Outputs](#outputs-filtering) normally filtered out
   - it also adds new records under any parent collections or other container resources
3. then follow the [Routine Usage](#routine-usage) instructions for future updates

## Routine usage

To update records as needed:

1. generate a set of updated JSON encoded record configurations as files in a directory
2. call the [Non-Interactive Publishing](/docs/contrib.md#non-interactive-publishing-workflow) contrib module with the
   required arguments and valid [Configuration](/docs/config.md#config-options)

### Publishing script

If you are using the BAS central workstations, and have access to
[MAGIC Environment Modules 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/dev-docs/-/blob/main/service-magic-env-modules.md),
you can use the `/data/magic/projects/lantern/live/tasks/pub-cat` script to publish to the live site.

For example:

> [!NOTE]
> Change `SITE`, `PROJECT` and `PROJECT_SLUG` to relevant values.

```shell
#!/usr/bin/env bash
set -e -u -o pipefail

# 'Automated publishing changeset: ' will always be prefixed to `--changeset-title`
# `--webook` is optional
/data/magic/projects/lantern/prod/tasks/pub-cat \
--site "live" \
--path "/path/to/records" \
--changeset-base "auto-$PROJECT_SLUG" \
--changeset-title "$PROJECT routine updates" \
--changeset-message "..." \
--commit-title "$PROJECT routine update" \
--commit-message "Routine update to records reflecting ..." \
--author-name "$PROJECT_SLUG" \
--author-email "magicdev@bas.ac.uk" \
--webhook "https://example.com/webhook"
```

## Webhook

An optional webhook URL CAN be provided, which will be called if any records are successfully committed as part of the
workflow.

> [!NOTE]
> A configured webhook will not be called if an error occurs within the workflow, or no records need publishing.

If successful, a POST request will be made to the configured URL, with a JSON payload containing:

- the GitLab commit and merge request URL
- new and/or updated record file identifiers
- statistics about the number of files created and/or updated

> [!TIP]
> See `lantern.contrib.non-interactive-publishing-workflow-schema.json` for a JSON Schema and an example payload.

### Outputs filtering

Global outputs are not called because:

- the [Site Index](/docs/outputs.md#site-index-output) Output for example only includes records from the Store passed
  to it, which would be limited to records managed by the workflow, clobbering outputs that include other (all)
  expected records and giving incomplete results
- calling exporters such as the [Site Pages Exporter](/docs/outputs.md#site-resources-output) is unnecessary, given
  they are not sensitive to record changes
