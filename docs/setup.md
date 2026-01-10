# Lantern - Setup

> [!WARNING]
> This section is Work in Progress (WIP) and is not complete/accurate.

## 1Password

For managing secrets and common [Config](/docs/config.md) options.

1. create a new 1Password [service account](https://developer.1password.com/docs/service-accounts/) with access to the
  *infrastructure* vault

## GitLab

> [!NOTE]
> Resources for the [GitLab](/docs/architecture.md#gitlab) records store are managed by the
> [ADD Metadata Toolbox 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/setup.md) project.

### GitLab User Access

Invite the GitLab bot user with the *developer* role to:

- the [lantern-records-exp 🛡️](https://gitlab.data.bas.ac.uk/felnne/lantern-records-exp) GitLab Store project
- projects used in the [Interactive record publishing workflow](/docs/usage.md#interactive-record-publishing-workflow)

Invite the GitLab bot user with the *reporter* role to:

- the [MAGIC Helpdesk 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/helpdesk) project for creating issues from item enquires

### GitLab API token

#### Workflows GitLab API token

To manage records in the [GitLab Store](/docs/stores.md#gitlab-store) and comment on issues as part of the
[Interactive Publishing Workflow](/docs/usage.md#interactive-record-publishing-workflow).

As a GitLab administrator impersonating the GitLab bot user, for each deployment and local development environment:

1. create a [Personal Access Token](https://gitlab.data.bas.ac.uk/-/profile/personal_access_tokens):
   - token name: (e.g. 'ansible-prod', 'conwat-local-dev', etc.)
   - scopes: *api*
2. store the token in 1Password:
   - in the *infrastructure* vault, for deployment environments
   - in your *employee* vault, for local development environments
3. set the relevant [Config](/docs/config.md) option in:
   - a local `.env` file, for local development environments
   - per-environment Ansible Vault, for deployment environments

#### Item enquires GitLab API token

For Power Automate to create issues for [Item Enquires](#power-automate-item-enquires).

As a GitLab administrator impersonating the GitLab bot user for the production environment:

1. create a [Personal Access Token](https://gitlab.data.bas.ac.uk/-/profile/personal_access_tokens):
   - token name: 'pa-item-enquires'
   - scopes: *api*
2. store the token in [1Password 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=dnsmipeiqjxbzd2qutbrhn3itu&h=magic.1password.eu)
3. set the token as the authorisation header for the GitLab issue action in the Power Automate flow

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

> [!NOTE]
> Resources for the [AWS](/docs/architecture.md#amazon-s3) static website hosting are managed by the
> [ADD Metadata Toolbox 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/setup.md) project.
>
> This section is limited to granting this project access to these resources.

### Static website hosting IAM user

For managing content. Create separate users for each [Deployment](/docs/deployment.md) or [Development](/docs/dev.md)
environment.

1. create a IAM user using the [AWS Console](http://console.aws.amazon.com) with an
   [Inline Policy 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=6wawslwrjk42cbff7qanfswz6q&h=magic.1password.eu)
2. create an access key for this user and store in 1Password
3. set the relevant [Config](/docs/config.md) option in a local `.env` file or Ansible Vault for use in the
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
