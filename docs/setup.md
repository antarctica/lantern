# Lantern - Setup

> [!CAUTION]
> This section is Work in Progress (WIP) and is not complete/accurate.

## 1Password

For managing secrets and common [Config](/docs/config.md) options.

1. create a new 1Password [service account](https://developer.1password.com/docs/service-accounts/) with access to the
  *infrastructure* vault

## GitLab

> [!NOTE]
> Resources for the [GitLab](/docs/architecture.md#gitlab) records store are managed by the
> [ADD Metadata Toolbox 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/setup.md) project.

### GitLab API token

For managing records. Create separate tokens for each [Deployment](/docs/deployment.md) or [Development](/docs/dev.md)
environment.

1. create a [Project Access Token](https://gitlab.data.bas.ac.uk/felnne/lantern-records-exp/-/settings/access_tokens):
   - role: *developer*
   - scopes: *api*
2. store the token in 1Password
3. set the relevant [Config](/docs/config.md) option in a local `.env` file or Ansible Vault for use in the
  [Environment Module](/docs/deployment.md#environment-module) template as appropriate

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

## Power Automate

### Power Automate SharePoint proxy

1. import `resources/flows/lantern-sharepoint-proxy.zip` into Power Automate as a new flow
2. configure the flow connections and generate a HTTP endpoint
3. set the relevant [Config](/docs/config.md) option in the `.env` template and Ansible Vault for use in the
   [Environment Module](/docs/deployment.md#environment-module) template
