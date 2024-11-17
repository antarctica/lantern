# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Infrastructure

## Environments

Available environments:

- *local development* - for prototyping and making changes (see [Development](/docs/dev.md) documentation)
- *development* - for shared experimentation and validating releases on BAS IT infrastructure
- *staging* - for pre-release testing
- *production* - for real-world use

Local Development environments may be created and destroyed as needed. The hosted Development (integration) and
Production environments are long-lived and run on central BAS IT infrastructure.

## Application servers

- managed by [BAS IT Ansible](/docs/deploy.md#bas-it-ansible) project

## Databases

- [Development 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=vb3uv7xz35iqosx5poznvbgycq&h=magic.1password.eu)
  - hosted using BAS IT
  - for storing ad-hoc data needed for development and prototyping
  - see [MAGIC/add-metadata-toolbox#391 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/391) for initial setup
- [Staging 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=63626cseqf3mrd32h33drhgzim&h=magic.1password.eu)
  - hosted using BAS IT
  - for storing non-production but real data
  - not currently used
  - see [MAGIC/add-metadata-toolbox#391 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/391) for initial setup
- [Production 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=nj7d6aoz5b6vrts23urb2unnbu&h=magic.1password.eu)
  - hosted using BAS IT
  - for storing real, definitive, data
  - see [MAGIC/add-metadata-toolbox#391 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/391) for initial setup
  - a [read-only](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=xe23mjl5zrchfbvfm7tdj7xzsi&h=magic.1password.eu) user is also available

## 1Password

- [Service Account 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=hialzwumkpxfor6oyqto4legpm&h=magic.1password.eu)
  - to allow access to secrets in [Continuous Deployment](/docs/deploy.md#continuous-deployment)

## Sentry

- [Project 🔒](https://antarctica.sentry.io/issues/?project=5197036)
  - for error monitoring

## Entra app registrations

- [Editor (Client) 🔒](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/91c284e7-6522-4eb4-9943-f4ec08e98cb9/isMSAApp~/false)
- [Catalogue (Server) 🔒](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/8b45581e-1b2e-4b8c-b667-e5a1360b6906/isMSAApp~/false)

## S3 buckets

- [Static site - integration (AWS Console 🔒)]()
  - for previewing upcoming static site builds
  - managed using [Terraform](/support/terraform/40-s3.tf)
- [Static site - production (AWS Console 🔒)]()
  - for production static site builds
  - managed using [Terraform](/support/terraform/40-s3.tf)

## GitLab projects

- [Revision tracking - integration 🔒](https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-integration)
  - for non-production use cases
  - managed using [Terraform](/support/terraform/42-gitlab_projects.tf)
- [Revision tracking - production 🔒](https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-production)
  - for production use cases
  - managed using [Terraform](/support/terraform/42-gitlab_projects.tf)

## GitLab Access Tokens

- [Revision tracking 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=jjsf3ts3qgp22a7cnaoui4jv4a&h=magic.1password.eu)
  - for integration and production [GitLab Projects](#gitlab-projects)
  - see [Setup](/docs/setup.md#manual-setup-gitlab-projects) documentation for provisioning instructions

## Downloads proxy

* Staging instance:
  * S3 bucket (AWS Console 🔒): `https://s3.console.aws.amazon.com/s3/buckets/add-catalogue-downloads-proxy-stage?region=eu-west-1&tab=objects`
  * Lambda function (Read, AWS Console 🔒): `https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/add-catalogue-downloads-proxy-stage`
  * Lambda function (Read, HTTP Endpoint): `https://vp3wuemex36unyzbzx76g4pnce0henks.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Write, AWS Console 🔒): `https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/add-catalogue-downloads-proxy-write-stage`
  * Lambda function (Write, HTTP Endpoint 🔒): `https://zrpqdlufnfqcmqmzppwzegosvu0rvbca.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Read, Reverse Proxied HTTP Endpoint, Staging Catalogue): `https://data-testing.data.bas.ac.uk/download-testing/`
  * Lambda endpoint (Read, Reverse Proxied HTTP Endpoint, Production Catalogue): `https://data.bas.ac.uk/download-testing/`
  * Artefact lookups file 🔒: `s3://add-catalogue-downloads-proxy-stage/lookups.json`
  * Lambda function (Write, IAM Customer Managed policy): `BAS-ADD-Catalogue-Downloads-Proxy-Function-Write-Staging`
* Production instance:
  * S3 bucket (AWS Console 🔒): `https://s3.console.aws.amazon.com/s3/buckets/add-catalogue-downloads-proxy-prod?region=eu-west-1&tab=objects`
  * Lambda function (Read, AWS Console 🔒): `https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/add-catalogue-downloads-proxy-prod`
  * Lambda endpoint (Read, HTTP Endpoint): `https://v7lyval5auv7hnqd75rsdhfi640wvpet.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Write, AWS Console 🔒): `https://eu-west-1.console.aws.amazon.com/lambda/home?
    region=eu-west-1#/functions/add-catalogue-downloads-proxy-write-prod`
  * Lambda function (Write, HTTP Endpoint 🔒): `https://dvej4gdfa333uci4chyhkxj3wq0fkxrs.lambda-url.eu-west-1.on.aws/`
  * Lambda function (Read, Reverse Proxied HTTP Endpoint, Staging Catalogue): `https://data-testing.data.bas.ac.uk/download/`
  * Lambda function (Read, Reverse Proxied HTTP Endpoint, Production Catalogue): `https://data.bas.ac.uk/download/`
  * Artefact lookups file 🔒: `s3://add-catalogue-downloads-proxy-prod/lookups.json`
  * Lambda function (Write, IAM Customer Managed policy): `BAS-ADD-Catalogue-Downloads-Proxy-Function-Write-Production`
