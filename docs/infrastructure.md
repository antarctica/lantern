# Lantern - Infrastructure

## Overview

This diagram shows this project's infrastructure components:

![Infrastructure Diagram](/docs/img/infrastructure.png)

## Environments

Available environments:

- development:
  - for prototyping and making changes (see [Development](/docs/dev.md) documentation)
  - hosted locally
- integration:
  - for pre-release testing and experimentation
  - externally accessible
- production:
  - for real-world use
  - externally accessible

Development environments may be created and destroyed as needed. Staging and Production environments are long-lived.

## 1Password
## Infrastructure as Code

[OpenTofu](https://opentofu.org), an open-source fork of the [Terraform](https://www.terraform.io) infrastructure as
code tool, is used to manage some project infrastructure in `resources/envs/main.tf`.

Remote state is managed by the [BAS Terraform Remote State 🛡️](https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state)
project.

To apply this infrastructure:

- install tools (`brew install awscli 1password-cli`)
- configure credentials for the [BAS AWS 🛡️](https://gitlab.data.bas.ac.uk/WSF/bas-aws) account (`aws configure`)
- copy `resources/envs/terraform.tfvars.tpl` to `resources/envs/terraform.tfvars` and populate values

Then running:

```text
% cd resources/envs
% opentofu init
% opentofu apply
```

- [Service Account 🔒](https://magic.1password.eu/developer-tools/infrastructure-secrets/serviceaccount/4MR5NL7W45AA3GAFGRZMVN2H2I)
  - to allow access to secrets in [Continuous Integration](/docs/dev.md#continuous-integration)

## Sentry

- [Project 🔒](https://antarctica.sentry.io/issues/?project=5197036)
  - for [Error monitoring](/docs/monitoring.md#error-monitoring)

## GitLab

- [Project Repository 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp)
  - [Public Mirror](https://github.com/antarctica/lantern)
- [Project User 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=el4eljwuhbgpunh7pvu3m7pvfy&h=magic.1password.eu)
- [Records Repository 🛡️](https://gitlab.data.bas.ac.uk/felnne/lantern-records-exp)
  - for [Storing](/docs/stores.md#gitlab-store) records in GitLab

## Power Automate

- [Item Enquires 🔒](https://make.powerautomate.com/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/shared/5e01b213-38ad-4a54-8f7c-25d3bee36101/details)
  - for [Item Enquires](/docs/site.md#item-enquires)
  - uses Personal Access Token for GitLab Project User
- [SharePoint Proxy 🔒](...)
  - for verifying SharePoint hosted record distribution options

## Plausible

- [Dashboard 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=lesr4cnv35csmuptgqqcionbf4&h=magic.1password.eu)
  - for [Web Analytics](/docs/monitoring.md#plausible)

## Cloudflare

- [Turnstile 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=sdwj5bvfuyrhtinexxxizk7mw4&h=magic.1password.eu)
  - for [Bot protection](/docs/site.md#bot-protection)

## Font Awesome

- [Icon Kit 🔒](https://fontawesome.com/kits/032ef5c342)
  - for [Icons](/docs/supplemental/icon-audit.md)

## Exporters

- AWS S3 publishing buckets & CloudFront distributions:
  - [Integration 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=rnv7zb3jzviwsvziknpxicvqaq&h=magic.1password.eu):
  - [Production 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=hksogwx7zqx3ct2jr36cshoqpy&h=magic.1password.eu):
  - [IAM policy 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=6wawslwrjk42cbff7qanfswz6q&h=magic.1password.eu)
  - for [Exporters](/docs/exporters.md) to publish content

## Deployment

- BAS Workstations:
  - [Ansible Playbook 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/lantern.yml)

## Hosting

Endpoints:

- development: [localhost:9000](http://localhost:9000/)
- integration: [data-testing.data.bas.ac.uk](https://data-testing.data.bas.ac.uk/)
- production: [data.bas.ac.uk](https://data.bas.ac.uk/)

The integration and production environments share domains with the legacy Discovery Metadata System (DMS), coexisting
via reverse proxying using the BAS HAProxy load balancer.

See the `data_redirect.txt` file within the load balancer configuration (🔒) for proxied paths.
