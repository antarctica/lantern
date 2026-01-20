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

- the [Interactive Publishing Workflow](/docs/usage.md#interactive-record-publishing-workflow)
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

## Sentry

1. register a new Sentry project
2. from *Project Settings* -> *Client Keys*:
   1. from the *Credentials* section, copy the *DSN* and store in 1Password
   2. from the *JavaScript Loader Script* section:
      1. set the SDK version to the highest/latest available
      2. enable the *Session Reply* option (needed for the user feedback widget to work)
      3. store the script value in 1Password
      4. and set as the `TEMPLATES_SENTRY_SRC` [Config](/docs/config.md) fixed value
3. set the relevant [Config](/docs/config.md) options for the DSN and CDN script in the `.env` template and Ansible
   Vault for use in the [Environment Module](/docs/deployment.md#environment-module) template

> [!NOTE]
> The Sentry DSN and JavaScript Loader Script are not considered secrets.

## Static website hosting

The majority of the [Static Site](/docs/architecture.md#static-site) hosting setup is managed using
[Infrastructure as Code (IaC)](/docs/infrastructure.md#infrastructure-as-code).

### Static website hosting IAM users

An IAM user for the [Workstation Module](/docs/usage.md#workstation-module) will be created via IaC for each
non-development environment, with permissions to manage content in
[AWS S3 publishing buckets](/docs/infrastructure.md#exporters).

Once created:

1. create an access key for each user and store in 1Password
2. set the relevant [Config](/docs/config.md) options in each Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template as appropriate

## Plausible Analytics

1. register a new Plausible Analytics site for the production [Hosting](/docs/infrastructure.md#hosting) endpoint
2. record the domain in 1Password
3. set the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template

## CloudFlare Turnstile

1. register a new Turnstile widget with hostnames for each [Hosting](/docs/infrastructure.md#hosting) endpoint
2. store site and secret keys in 1Password
3. set the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template

## Font Awesome

1. register a new Font Awesome kit with:
   - version *7.x*
   - *CSS only* embedding method (to support non-JavaScript clients)
   - automatic subsetting (*classic* -> *regular*)
   - hostnames for each [Hosting](/docs/infrastructure.md#hosting) endpoint
2. set the kit CDN URL in the `styles_font_awesome()` [Common Macro](/docs/site.md#common-macros)

## Power Automate

### Power Automate item enquires

1. import `resources/flows/lantern-item-enquires.zip` into Power Automate as a new flow
2. for MAGIC point of contact branch, set the [GitLab Personal Access Token](#item-enquires-gitlab-api-token) in the
   authentication value in the 'create-issue' action
3. set the flow endpoint as the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for
   use in the [Environment Module](/docs/deployment.md#environment-module) template

### Power Automate SharePoint proxy

1. import `resources/flows/lantern-sharepoint-proxy.zip` into Power Automate as a new flow
2. configure the flow connections and generate an HTTP endpoint
3. set the flow endpoint as the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for
   use in the [Environment Module](/docs/deployment.md#environment-module) template

### Power Automate SAN proxy

> [!IMPORTANT]
> This proxy is not used for operational reasons.

1. import `resources/flows/lantern-san-proxy.zip` into Power Automate as a new flow
2. configure the flow connections and generate an HTTP endpoint
3. set the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template

> [!TIP]
> See [this note](https://gitlab.data.bas.ac.uk/MAGIC/dev-docs/-/blob/32f4adf63fae42acab7b8fb749362432b68ad397/tool-power-automate.md#sftp-connector)
> on getting the SSH server fingerprint in Power Automate expected format.
