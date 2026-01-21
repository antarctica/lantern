# Lantern - Infrastructure

## Overview

This diagram shows this project's infrastructure components:

![Infrastructure Diagram](/docs/img/infrastructure.png)

## Environments

Available environments:

- development:
  - for prototyping and making changes (see [Development](/docs/dev.md) documentation)
  - hosted locally
- staging:
  - for pre-release testing and experimentation
  - externally accessible
- production:
  - for real-world use
  - externally accessible

Development environments may be created and destroyed as needed. Staging and Production environments are long-lived.

## Deployment

- [Environment Module](/docs/deployment.md#environment-module)
  - to BAS Workstations to run [Publishing Workflows](/docs/usage.md#workstation-module)
  - managed via [Ansible Playbook 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/lantern.yml)

## Hosting

Endpoints:

- development: [localhost:9000](http://localhost:9000/)
- staging:
  - [lantern-testing.data.bas.ac.uk](https://lantern-testing.data.bas.ac.uk)
  - reverse proxied as [data-testing.data.bas.ac.uk](https://data-testing.data.bas.ac.uk/)
- production:
  - [lantern.data.bas.ac.uk](https://lantern.data.bas.ac.uk)
  - reverse proxied as [data.bas.ac.uk](https://data.bas.ac.uk/)

The staging and production environments share their endpoints with the legacy Discovery Metadata System (DMS), via
reverse proxying. The BAS HAProxy load balancer proxies applicable requests to a relevant AWS Cloudfront Distribution.

See the `data_redirect.txt` file within the load balancer configuration (🔒) for proxied paths.

## Infrastructure as Code

[OpenTofu](https://opentofu.org), an open-source fork of the [Terraform](https://www.terraform.io) infrastructure as
code tool, is used to manage some project infrastructure in `resources/envs/main.tf`.

Remote state is managed by the [BAS Terraform Remote State 🛡️](https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state)
project.

To apply this infrastructure:

- install tools (`brew install awscli 1password-cli`)
- configure credentials for the [BAS AWS 🛡️](https://gitlab.data.bas.ac.uk/WSF/bas-aws) account (`aws configure`)
- copy `resources/envs/terraform.tfvars.tpl` to `resources/envs/terraform.tfvars` and populate credentials/values

Then run:

```text
% cd resources/envs
% opentofu init
% opentofu apply
```

## Components

### 1Password

- [Service Account 🔒](https://magic.1password.eu/developer-tools/infrastructure-secrets/serviceaccount/4MR5NL7W45AA3GAFGRZMVN2H2I)
  - to allow access to secrets in [Continuous Integration](/docs/dev.md#continuous-integration)
  - managed manually as per [Setup](/docs/setup.md#1Password) documentation

### Sentry

- [Project 🔒](https://antarctica.sentry.io/issues/?project=4507147658919936)
  - for [Error monitoring](/docs/monitoring.md#error-monitoring)
  - managed via [Infrastructure as Code](#infrastructure-as-code) and manually as per
    [Setup](/docs/setup.md#sentry) documentation

### GitLab

- [Project Repository 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp)
  - [Public Mirror](https://github.com/antarctica/lantern)
  - managed manually
- [Project User 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=el4eljwuhbgpunh7pvu3m7pvfy&h=magic.1password.eu)
  - for committing records and interacting with issues
  - managed via [Infrastructure as Code](#infrastructure-as-code)
- [Records Repository 🛡️](https://gitlab.data.bas.ac.uk/felnne/lantern-records-exp)
  - [GitLab bot user PAT 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=geijspsmchmg6j2ojhc6fkh7ge&h=magic.1password.eu).
  - for [Storing](/docs/stores.md#gitlab-store) records in GitLab
  - managed via [Infrastructure as Code](#infrastructure-as-code) and manually as per
    [Setup](/docs/setup.md#gitLab-publishing-workflows) documentation

### Power Automate

- [Item Enquires 🔒](https://make.powerautomate.com/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/shared/5e01b213-38ad-4a54-8f7c-25d3bee36101/details)
  - [GitLab bot user PAT 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=uyhvmbnsfuk5oxb2snanmpolj4&h=magic.1password.eu)
  - for [Item Enquires](/docs/site.md#item-enquires)
  - managed via [Infrastructure as Code](#infrastructure-as-code) and manually as per
    [Setup](/docs/setup.md#power-automate-item-enquires) documentation
- [SharePoint Proxy 🔒](...)
  - for verifying SharePoint hosted record distribution options
  - managed manually as per [Setup](/docs/setup.md#power-automate-sharepoint-proxy) documentation

### Plausible

- [Dashboard 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=lesr4cnv35csmuptgqqcionbf4&h=magic.1password.eu)
  - for [Web Analytics](/docs/monitoring.md#plausible)
  - managed manually as per [Setup](/docs/setup.md#plausible-analytics) documentation

### Cloudflare

- [Turnstile 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=sdwj5bvfuyrhtinexxxizk7mw4&h=magic.1password.eu)
  - [Site and Secret Keys 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=s7zzm3hqsq4qs5aidqyqbce2qq&h=magic.1password.eu)
  - for [Bot protection](/docs/site.md#bot-protection)
  - managed via [Infrastructure as Code](#infrastructure-as-code) and manually as per
    [Setup](/docs/setup.md#gitLab-publishing-workflows) documentation

### Font Awesome

- [Icon Kit 🔒](https://fontawesome.com/kits/032ef5c342)
  - for [Icons](/docs/supplemental/icon-audit.md)
  - managed manually as per [Setup](/docs/setup.md#font-awesome) documentation

### Exporters

- AWS S3 publishing buckets & CloudFront distributions:
  - [Staging 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=rnv7zb3jzviwsvziknpxicvqaq&h=magic.1password.eu):
    - [IAM user for workstation module 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=b3xyp2epz6qycjrbootkf3oaha&h=magic.1password.eu)
  - [Production 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=hksogwx7zqx3ct2jr36cshoqpy&h=magic.1password.eu):
    - [IAM user for workstation module 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=hgjc2sxfvctejscocydzmg2tge&h=magic.1password.eu)
  - for [Exporters](/docs/exporters.md) to publish content
  - managed via [Infrastructure as Code](#infrastructure-as-code)
