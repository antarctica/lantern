# Lantern - Deployment

## Python package

This application is distributed as a Python (Pip) package.

[Continuous Deployment](#continuous-deployment) will build the package and publish it to the project
[Package Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp/-/packages) automatically.

> [!TIP]
> The package can be built manually by running the `build` [Development Task](/docs/dev.md#development-tasks).

## Environment module

This application is deployed as a custom [Environment Module](https://modules.readthedocs.io) on the BAS central
workstations to enable supported [Tasks and Workflows](/docs/usage.md#workstation-module).

The module:

- adds the `bin/` directory of a Python virtual environment containing the [Python Package](#python-package) to the PATH
- sets [Configuration Options](/docs/config.md)

Separate modules (and corresponding virtual environments) are created for each project [Release](/README.md#releases)
automatically by the [Ansible Playbook](#ansible-playbook).

## Non-interactive record publishing script

A [shell script 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/roles/magic/lantern/templates/pub-cat.sh.j2)
managed by [Ansible](#ansible-playbook) is deployed to the BAS Central workstations to implement the
[Non-Interactive Publishing Workflow](/docs/usage.md#non-interactive-publishing-workflow) using the
[Contrib Module](/docs/contrib.md#non-interactive-publishing-workflow).

## Site checks script

A [Cron shell script 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/roles/magic/lantern/templates/site-checks-cron.sh.j2)
managed by [Ansible](#ansible-playbook), is deployed to the BAS Central workstations for
[Scheduled Checks](/docs/monitoring.md#scheduled-checks) using the [Contrib Module](/docs/contrib.md#site-checks).

## Ansible playbook

This application is deployed using an
[Ansible Playbook 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/lantern.yml)
as part of the BAS IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/) project.

The playbook:

- creates a Python virtual environment containing the [Python Package](#python-package) for the app version
- generates an [Environment Module](#environment-module) for the app version
- configures a cron job for [Scheduled Checks](/docs/monitoring.md#scheduled-checks)
- runs post-deployment checks including:
  - checking the expected version is loaded by the [Environment Module](#environment-module)
  - checking the configuration set by the [Environment Module](#environment-module) is
    [Valid](/docs/config.md#config-validation)
  - running the [Non-Interactive Publishing Workflow](#non-interactive-record-publishing-script) for a fixed test
    record and branch
  - checking the [Heartbeat](/docs/monitoring.md#heartbeat)
  - checking the [Health Check Endpoint](/docs/monitoring.md#health-check-endpoint)

## Continuous Deployment

Tagged commits created for [Releases](/README.md#releases) will trigger a continuous deployment workflow for the
release to the production environment using GitLab's CI/CD configured in [`.gitlab-ci.yml`](/.gitlab-ci.yml).

Pre-releases can optionally be deployed to the staging environment by triggering the relevant CI job manually.

## Rotating access tokens

See [Infrastructure](/docs/infrastructure.md#rotating-tokens) documentation.
