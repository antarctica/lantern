# Lantern - Setup

> [!WARNING]
> This section is Work in Progress (WIP) and is not complete/accurate.

## 1Password

For managing secrets and common [Config](/docs/config.md) options.

1. create a new 1Password [service account](https://developer.1password.com/docs/service-accounts/) with access to the
  *infrastructure* vault

## GitLab

Resources for the [GitLab Store](/docs/stores.md#gitlab-store) are managed using
[Infrastructure as Code (IaC)](/docs/infrastructure.md#infrastructure-as-code).

This includes a GitLab bot user to enable:

- the [Publishing Workflows](#gitlab-publishing-workflows)
- [Item Enquires](#gitlab-item-enquires)

### GitLab publishing workflows

IaC will:

- create and store in 1Password a personal access token to enable the
  [Workstation Module](/docs/usage.md#workstation-module) to:
  - access and manage records in the [GitLab Store](/docs/stores.md#gitlab-store)
  - comment on issues for the [Interactive Publishing Workflow](/docs/usage.md#interactive-record-publishing-workflow)
- add the bot user as a member of the GitLab projects containing these issues, with at least the *reporter* role

Manually:

- reference this token in relevant Ansible Vault templates to set [Config](/docs/config.md) options

### GitLab item enquires

IaC will:

- create a personal access token to enable the [Power Automate](#power-automate-item-enquires) flow for
  [Item Enquires](/docs/site.md#item-enquires)
- store this token in 1Password

Manually:

- set this token in the authorisation header for the 'create-issue' action in the Power Automate flow

## Static website hosting

The majority of the [Static Site](/docs/architecture.md#static-site) hosting setup is managed using
[Infrastructure as Code (IaC)](/docs/infrastructure.md#infrastructure-as-code).

### Static website hosting reverse proxying

Configuring the BAS HAProxy load balancer for [Reverse Proxying](/docs/infrastructure.md#hosting) requires a request
to BAS IT. This should request:

- frontend ACLs matching any of the static site endpoints [1] for each non-development environment
- backends for each of these environments with:
  - a single server pointing to the relevant AWS CloudFront Distribution
  - a health check using the [Health Check Endpoint](/docs/monitoring.md#health-check-endpoint)

[1] Static site endpoints:

```text
/-/
/collections
/features
/items
/legal
/maps
/records
/series
/static
/teams
/waf
/.well-known/api-catalog
```

### Static website hosting IAM users

IaC will:

- create an IAM user to enable the [Workstation Module](/docs/usage.md#workstation-module) with a suitable inline
  policy to:
  - manage content in the [Static Site](/docs/architecture.md#static-site) for the
    [Interactive](/docs/usage.md#interactive-record-publishing-workflow) and
    [Non-Interactive](/docs/usage.md#non-interactive-record-publishing-workflow) Publishing Workflows
- create and store an access key in 1Password for each non-development environment

Manually:

- reference the relevant access key in the corresponding Ansible Vault templates to set [Config](/docs/config.md) options

## Sentry

A Sentry project for [Error Monitoring Protection](/docs/monitoring.md#error-monitoring) is managed using
[Infrastructure as Code (IaC)](/docs/infrastructure.md#infrastructure-as-code).

IaC will:

- register a new Sentry project and create a `sentry_dsn` output for the default DSN

> [!NOTE]
> DSNs are not considered secret in newer Sentry versions.

Manually:

- set the relevant [Config](/docs/config.md) option for the DSN as a hard-coded value
- create an [Uptime Check](https://docs.sentry.io/product/uptime-monitoring/) for the production environment:
  - url: `https://data.bas.ac.uk/collections/bas-maps`
  - interval: 5 minutes
  - timeout: 3 seconds

> [!TIP]
> Uptime monitors [cannot be managed](https://github.com/jianyuan/terraform-provider-sentry/issues/643) via IaC.

## Cloudflare Turnstile

A Cloudflare Turnstile widget for [Bot Protection](/docs/site.md#bot-protection) in the static site is managed using
[Infrastructure as Code (IaC)](/docs/infrastructure.md#infrastructure-as-code).

IaC will:

- create a Turnstile widget, including [Hosting Endpoints](/docs/infrastructure.md#hosting)
- store the site and secret keys in 1Password

Manually:

- reference the site key as the relevant [Config](/docs/config.md) option in:
  - the `/resources/dev/.env.tpl` template
  - the relevant Ansible Vault template
- set the secret key token as the 'secret' property value in the body of the 'turnstile-verify' action in the item
  enquiries [Power Automate Flow](#power-automate-item-enquires)

## Plausible Analytics

Manually:

1. register a new Plausible Analytics site for the production [Hosting](/docs/infrastructure.md#hosting) endpoint
2. record the domain in 1Password
3. set the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template

## Font Awesome

Manually:

1. register a new Font Awesome kit with:
   - version *7.x*
   - *CSS only* embedding method (to support non-JavaScript clients)
   - automatic subsetting (*classic* -> *regular*)
   - hostnames for each [Hosting](/docs/infrastructure.md#hosting) endpoint
2. set the kit CDN URL in the `styles_font_awesome()` [Common Macro](/docs/site.md#common-macros)

## Power Automate

### Power Automate item enquires

Manually:

1. import `resources/flows/lantern-item-enquires.zip` into Power Automate as a new flow
2. set the 'secret' property value in the body of the 'turnstile-verify' action to the
   [Cloudflare Turnstile](#cloudflare-turnstile) secret key from 1Password
3. for MAGIC point of contact branch, set the [GitLab Personal Access Token](#gitlab-item-enquires) in the
   authentication header in the 'create-issue' action
4. set the flow endpoint as the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for
   use in the [Environment Module](/docs/deployment.md#environment-module) template

### Power Automate SharePoint proxy

Manually:

1. import `resources/flows/lantern-sharepoint-proxy.zip` into Power Automate as a new flow
2. configure the flow connections and generate an HTTP endpoint
3. set the flow endpoint as the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for
   use in the [Environment Module](/docs/deployment.md#environment-module) template

### Power Automate SAN proxy

> [!IMPORTANT]
> This proxy is not used for operational reasons.

Manually:

1. import `resources/flows/lantern-san-proxy.zip` into Power Automate as a new flow
2. configure the flow connections and generate an HTTP endpoint
3. set the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template

> [!TIP]
> See [this note](https://gitlab.data.bas.ac.uk/MAGIC/dev-docs/-/blob/32f4adf63fae42acab7b8fb749362432b68ad397/tool-power-automate.md#sftp-connector)
> on getting the SSH server fingerprint in the format Power Automate expects.
