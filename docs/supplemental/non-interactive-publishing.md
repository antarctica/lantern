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

1. generate a set of JSON encoded record configurations as files in a directory
2. import and publish these records using the [Interactive Workflow](/docs/usage.md#interactive-record-publishing-workflow):
   - commit to the `main` branch
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

## Webhook

An optional webhook can be provided which will be called if any records are committed as part of the workflow. A POST
request will be made to the configured URL, with a JSON payload containing:

- GitLab commit and merge request URLs
- new and/or updated record file identifiers
- statistics about the number of files created and/or updated

> [!TIP]
> See `/resources/scripts/non-interactive-publishing-workflow-schema.json` for the schema used with an example.
