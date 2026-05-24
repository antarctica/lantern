# Lantern - Non-interactive record publishing workflow (Supplemental)

## Overview

### Outputs filtering

Global outputs are not called because:

- the [Site Index](/docs/outputs.md#site-index-output)) Output for example only includes records from the Store passed
  to it, which would be limited to records managed by the workflow, clobbering outputs that include other (all)
  expected records and giving incomplete results
- calling exporters such as the [Site Pages Exporter](/docs/outputs.md#site-resources-output) is unnecessary, given
  they are not sensitive to record changes

## Bootstrapping

To set up this workflow for an application:

1. [Generate](/docs/usage.md#creating-records) a set of JSON encoded record configurations as files in a directory
2. import and publish these records using the [Interactive Workflow](/docs/usage.md#interactive-publishing-workflow):
   - merge the changeset into `main`
   - this includes records in [Outputs](#outputs-filtering) normally filtered out
   - it also adds new records under any parent collections or other container resources
3. then follow the [Routine Usage](#routine-usage) instructions for future updates

## Routine usage

Configure your application to perform these actions as frequently as needed:

1. generate a set of updated JSON encoded record configurations as files in a directory
2. call `/data/magic/projects/lantern/live/tasks/pub-cat` with the required arguments

> [!WARNING]
> This will publish any records directly to the live catalogue.
>
> To publish to the testing catalogue, call `/data/magic/projects/lantern/testing/tasks/pub-cat` instead.

### Example usage script

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

An optional webhook can be provided which will be called if any records are committed as part of the workflow. A POST
request will be made to the configured URL, with a JSON payload containing:

- GitLab commit and merge request URLs
- new and/or updated record file identifiers
- statistics about the number of files created and/or updated

> [!TIP]
> See `/resources/scripts/non-interactive-publishing-workflow-schema.json` for the schema used with an example.
