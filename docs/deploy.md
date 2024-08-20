# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Deployment

## Python package

This project is distributed as a Python package, hosted in the
[BAS GitLab Python Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/packages).

Source and binary packages are built and published automatically using
[Poetry](https://python-poetry.org) in [Continuous Deployment](#continuous-deployment).

## Deployment process

Create a [deployment issue](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/new?issue[title]=x.x.x%20deploy&issuable_template=deploy)
and follow the instructions.

## BAS IT Ansible

The deployment [Python package](#python-package) is deployed as a WSGI application through the BAS IT
[Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/) setup.

- [Playbook 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/add-metadata-toolbox.yml)
- [Inventory 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/tree/master/inventory/magic)

This application is deployed to a development, staging and production environment. Development deployments are
automatic via [Continuous Deployment](#continuous-deployment). Deployments to the staging and production environments
can only be performed by BAS IT.

### Running CLI commands

To use the Flask CLI:

```
$ ssh [environment]
$ source /var/opt/wsgi/.virtualenvs/add-metadata-toolbox/bin/activate
$ FLASK_APP=scar_add_metadata_toolbox FLASK_ENV=production flask [command]
$ deactivate
$ exit
```

## API Service

The CSW Catalogues are deployed as a service within the BAS API Load Balancer, pointing to the
[BAS IT Ansible](#bas-it-ansible) production environment.

### API Documentation

Usage documentation for this API service is held in `docs/api/` and currently
[manually 🛡️](https://gitlab.data.bas.ac.uk/WSF/api-docs#adding-a-service-manually) published using these service paths:

* `s3://bas-api-docs-content-testing/services/data/metadata/add/csw/`
* `s3://bas-api-docs-content/services/data/metadata/add/csw/`

## Downloads proxy deployment

When [Source Code](/docs/dev.md#downloads-proxy-source) for the
[Downloads Proxy](/docs/implementation-downloads-proxy.md) is updated, it needs to be packaged into a zip archive for
deployment via [Terraform](/docs/setup.md#terraform).

**Note:** Terraform will automatically deploy either zip archive if its file hash changes. Therefore, only update the
archives of Download Proxy environments you wish to update. I.e. don't update the production archive if changes are
still being tested.

To package the source code into a deployment package for the staging environment:

```
$ cd support/downloads-proxy/
$ zip -u downloads-proxy-stage.zip index.js
```

To package the source code into a deployment package for the production environment:

```
$ cd support/downloads-proxy/
$ zip -u downloads-proxy-prod.zip index.js
```

To deploy changes, plan and apply the [Terraform](/docs/setup.md#terraform) configuration.

## Downloads proxy JSON Schema deployment

The JSON Schema used for the
[Downloads Proxy](/docs/implementation-downloads-proxy.md#downloads-proxy-artefacts-lookup-schema) is distributed
through the BAS Metadata Standards website, alongside schemas from other projects.

**Note:** These instructions assume the JSON Schema is version 1. Replace `v1` if this version is different (e.g. `v3`).

To deploy the latest Downloads Proxy JSON Schema for use within the *staging* environment of the BAS Metadata
Standards website:

```
# with the AWS CLI installed and configured with appropriate credentials
$ aws s3 cp ./support/downloads-proxy/artefact-lookups-v1.json s3://metadata-standards-testing.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json
```

To deploy the latest Downloads Proxy JSON Schema for use within the *production* environment of the BAS Metadata
Standards website:

```
# with the AWS CLI installed and configured with appropriate credentials
$ aws s3 cp ./support/downloads-proxy/artefact-lookups-v1.json s3://metadata-standards.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json
```

## Continuous Deployment

All commits will trigger a Continuous Deployment process using GitLab's CI/CD platform, configured in `.gitlab-ci.yml`.
