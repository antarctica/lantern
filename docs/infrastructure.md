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

- [Service Account 🔒](https://magic.1password.eu/developer-tools/infrastructure-secrets/serviceaccount/4MR5NL7W45AA3GAFGRZMVN2H2I)
  - to allow access to secrets in [Continuous Integration](/docs/dev.md#continuous-integration)

## Sentry

- [Project 🔒](https://antarctica.sentry.io/issues/?project=5197036)
  - for [Error monitoring](/docs/monitoring.md#error-monitoring)

## GitLab

- [Records Repository 🛡️](https://gitlab.data.bas.ac.uk/felnne/lantern-records-exp)
  - for [Storing](/docs/stores.md#gitlab-store) records in GitLab

## Power Automate

- [Item Enquires 🔒](https://make.powerautomate.com/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/shared/5e01b213-38ad-4a54-8f7c-25d3bee36101/details)
  - for [Item Enquires](/docs/site.md#item-enquires)
- [SharePoint Proxy 🔒](...)
  - for

## Plausible

- [Dashboard 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=lesr4cnv35csmuptgqqcionbf4&h=magic.1password.eu)
  - for [Web Analytics](/docs/monitoring.md#plausible)

## Cloudflare

- [Turnstile 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=sdwj5bvfuyrhtinexxxizk7mw4&h=magic.1password.eu)
    - for [Bot protection](/docs/site.md#bot-protection)

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

- development: http://localhost:9000/
- integration: https://data-testing.data.bas.ac.uk/
- production: https://data.bas.ac.uk/

The integration and production environments share domains with the legacy Discovery Metadata System (DMS), coexisting
via reverse proxying using the BAS HAProxy load balancer.

See the `data_redirect.txt` file within the load balancer configuration (🔒) for proxied paths.
