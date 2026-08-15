# Lantern - Contrib

Modules intended for use by other applications or scripts.

## Non-interactive publishing workflow

`lantern.contrib.non_interactive_publishing_workflow`

Module implementing the [Non-Interactive Publishing Workflow](/docs/usage.md#non-interactive-publishing-workflow).

Call this module directly to run the workflow with an argparse CLI to collect required arguments.

Intended for creating publishing scripts managed by [Ansible](/docs/deployment.md#ansible-playbook), or for future
direct integration within other applications that manage records.

## Site checks

`lantern.contrib.site_checks`

Module implementing [Scheduled Site Checks](/docs/monitoring.md#scheduled-checks).

Call the `entrypoint()` method to run and publish site checks for all catalogue content in the live site.

E.g.

```shell
python -c "from lantern.contrib.site_checks import entrypoint; entrypoint()"
```

Intended for use in a cron/timer task managed by [Ansible](/docs/deployment.md#ansible-playbook) to run scheduled checks.

## Deployment updates

`lantern.contrib.deployment_updates`

Module implementing the [Site Updates Script](/docs/deployment.md#site-updates-script) run during
[Ansible](/docs/deployment.md#ansible-playbook) deployments.

Call this module directly to trigger exports with an argparse CLI to collect required arguments.
