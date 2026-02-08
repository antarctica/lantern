# Lantern - Configuration

Application configuration is managed by the `lantern.Config` class.

<!-- pyml disable md028 -->
> [!TIP]
> User configurable options can be defined using environment variables and/or an `.env` file, with environment
> variables taking precedence. Variables are prefixed with `LANTERN_` to avoid conflicts with other applications.
>
> E.g. use `LANTERN_FOO` to set a `FOO` option.

> [!NOTE]
> Config option values may be [Overridden](/docs/dev.md#pytest-env) in application tests.
<!-- pyml enable md028 -->

## Config options

<!-- pyml disable md013 -->
| Option                                  | Type         | Configurable | Required | Sensitive | Since Version | Summary                                                                            | Default                                   | Example                                         |
|-----------------------------------------|--------------|--------------|----------|-----------|---------------|------------------------------------------------------------------------------------|-------------------------------------------|-------------------------------------------------|
| `ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE` | JSON Web Key | Yes          | Yes      | Yes       | v0.4.x        | JSON Web Key (JWK) for accessing administrative metadata                           | *None*                                    | '{"kid": "magic_metadata_encryption_key", ...}' |
| `ADMIN_METADATA_SIGNING_KEY_PUBLIC`     | JSON Web Key | Yes          | Yes      | No        | v0.4.x        | JSON Web Key (JWK) for verifying administrative metadata                           | *None*                                    | '{"kid": "magic_metadata_signing_key", ...}'    |
| `AWS_ACCESS_ID`                         | String       | Yes          | Yes      | No        | v0.1.x        | AWS IAM user identifier for site exporter remote uploads                           | *None*                                    | 'x'                                             |
| `AWS_ACCESS_SECRET`                     | String       | Yes          | Yes      | Yes       | v0.1.x        | AWS IAM user secret for site exporter remote uploads                               | *None*                                    | 'x'                                             |
| `AWS_ACCESS_SECRET_SAFE`                | String       | No           | -        | No        | v0.1.x        | Redacted version of `STORE_GITLAB_TOKEN`                                           | *N/A*                                     | 'REDACTED'                                      |
| `AWS_S3_BUCKET`                         | String       | Yes          | Yes      | No        | v0.1.x        | AWS S3 bucket used for remote static site builds                                   | *None*                                    | 'example.com'                                   |
| `BASE_URL`                              | String       | No           | -        | No        | v0.2.x        | Root URL for the static site, used to generate fully qualified links               | `https://{AWS_S3_BUCKET}`                 | 'https://example.com'                           |
| `ENABLE_FEATURE_SENTRY`                 | Boolean      | Yes          | No       | No        | v0.1.x        | Enables Sentry monitoring if true                                                  | *True*                                    | *True*                                          |
| `EXPORT_PATH`                           | Path         | Yes          | Yes      | No        | v0.1.x        | Location for local static site exporter builds                                     | *None*                                    | '/data/exports/records'                         |
| `LOG_LEVEL`                             | Number       | Yes          | No       | No        | v0.1.x        | A logging level name or number to set the application logging level                | 30                                        | 20                                              |
| `LOG_LEVEL_NAME`                        | String       | No           | -        | No        | v0.1.x        | Logging level name for the configured application logging level                    | 'WARNING'                                 | 'INFO'                                          |
| `PARALLEL_JOBS`                         | Number       | Yes          | No       | No        | v0.3.x        | Number of parallel jobs to run for applicable tasks                                | 1                                         | 4                                               |
| `SENTRY_DSN`                            | String       | No           | -        | No        | v0.1.x        | Sentry connection string for backend error monitoring (not sensitive)              | *N/A*                                     | 'https://example.com'                           |
| `SENTRY_ENVIRONMENT`                    | String       | Yes          | No       | No        | v0.1.x        | Application runtime environment to include in Sentry errors                        | 'development'                             | 'production'                                    |
| `STORE_GITLAB_BRANCH`                   | String       | Yes          | Yes      | No        | v0.5.x        | GitLab store's remote branch name                                                  | *None*                                    | 'main'                                          |
| `STORE_GITLAB_CACHE_PATH`               | Path         | Yes          | Yes      | No        | v0.1.x        | Location for GitLab store's local records cache                                    | *None*                                    | '/tmp/gitlab_cache/'                            |
| `STORE_GITLAB_ENDPOINT`                 | String       | Yes          | Yes      | No        | v0.1.x        | base API endpoint for GitLab store's remote instance                               | *None*                                    | 'https://gitlab.com'                            |
| `STORE_GITLAB_PROJECT_ID`               | String       | Yes          | Yes      | No        | v0.1.x        | GitLab project ID for GitLab store's remote instance                               | *None*                                    | '123'                                           |
| `STORE_GITLAB_TOKEN`                    | String       | Yes          | Yes      | Yes       | v0.1.x        | API access token for GitLab store's remote instance                                | *None*                                    | 'REDACTED'                                      |
| `STORE_GITLAB_TOKEN_SAFE`               | String       | No           | -        | No        | v0.1.x        | Redacted version of `STORE_GITLAB_TOKEN`                                           | *N/A*                                     | 'REDACTED'                                      |
| `TEMPLATES_CACHE_BUST_VALUE`            | String       | No           | -        | No        | v0.1.x        | Query string value appended to site assets to avoid stale browser caches           | *N/A*                                     | '0.3.0'                                         |
| `TEMPLATES_ITEM_CONTACT_ENDPOINT`       | String       | Yes          | Yes      | No        | v0.1.x        | Microsoft Power Automate trigger endpoint for item contact form                    | *N/A*                                     | 'https://example.com'                           |
| `TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY`  | String       | Yes          | Yes      | No        | v0.4.x        | Cloudflare Turnstile site key for item contact form                                | *N/A*                                     | 'x'                                             |
| `TEMPLATES_ITEM_MAPS_ENDPOINT`          | String       | Yes          | No       | No        | v0.1.x        | Embedded Maps Service base endpoint                                                | `https://embedded-maps.data.bas.ac.uk/v1` | 'https://embedded-maps.data.bas.ac.uk/v1'       |
| `TEMPLATES_ITEM_VERSIONS_ENDPOINT`      | String       | Yes          | Yes      | No        | v0.2.x        | Base URL to a GitLab project for viewing item record revisions                     | *None*                                    | 'https://example.com'                           |
| `TEMPLATES_PLAUSIBLE_DOMAIN`            | String       | No           | -        | No        | v0.1.x        | Plausible site identifier for frontend analytics                                   | *None*                                    | 'example'                                       |
| `TRUSTED_UPLOAD_HOST`                   | String       | Yes          | No       | No        | v0.5.x        | SSH config alias for remote trusted content hosting server                         | *None*                                    | 'lantern-trusted-content'                       |
| `TRUSTED_UPLOAD_PATH`                   | String       | Yes          | Yes      | No        | v0.5.x        | Directory for trusted content, local or remote within trusted content server       | *None*                                    | '/data/lantern'                                 |
| `VERIFY_SAN_PROXY_ENDPOINT`             | String       | Yes          | Yes      | No        | v0.5.x        | Microsoft Power Automate trigger endpoint for checking SAN references              | *N/A*                                     | 'https://example.com'                           |
| `VERIFY_SHAREPOINT_PROXY_ENDPOINT`      | String       | Yes          | Yes      | No        | v0.3.x        | Microsoft Power Automate trigger endpoint for checking SharePoint hosted downloads | *N/A*                                     | 'https://example.com'                           |
| `VERSION`                               | String       | No           | -        | No        | v0.1.x        | Application package version                                                        | *N/A*                                     | '0.3.0'                                         |
<!-- pyml enable md013 -->

### Data model config options

- `ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE`
- `ADMIN_METADATA_SIGNING_KEY_PUBLIC`

### Performance config options

- `PARALLEL_JOBS`

Some tasks such as populating caches can run in parallel for better performance. The `PARALLEL_JOBS` option sets the
maximum number of parallel jobs to run. Where `1` disables parallelism and `-1` uses all available CPU cores.

### Monitoring config options

See the [Monitoring](/docs/monitoring.md#monitoring-configuration) docs for more information on how these
[Config Options](#config-options) are used to configure app monitoring (inc. Sentry):

- `ENABLE_FEATURE_SENTRY`
- `SENTRY_ENVIRONMENT`
- `SENTRY_DSN`
- `VERIFY_SHAREPOINT_PROXY_ENDPOINT`
- `VERIFY_SAN_PROXY_ENDPOINT`

### GitLab Store config options

See the [Stores](/docs/stores.md#stores-configuration) docs for more information on how these
[Config Options](#config-options) are used by stores:

- `STORE_GITLAB_BRANCH`
- `STORE_GITLAB_STORE_CACHE_PATH`
- `STORE_GITLAB_STORE_ENDPOINT`
- `STORE_GITLAB_STORE_PROJECT_ID`
- `STORE_GITLAB_TOKEN`
- `STORE_GITLAB_TOKEN_SAFE`

### Exporter config options

See the [Exporters](/docs/exporters.md#exporters-configuration) docs for more information on how these
[Config Options](#config-options) are used by exporters:

- `BASE_URL`
- `EXPORT_PATH`
- `AWS_ACCESS_ID`
- `AWS_ACCESS_SECRET`
- `AWS_ACCESS_SECRET_SAFE`
- `AWS_S3_BUCKET`
- `VERIFY_SHAREPOINT_PROXY_ENDPOINT`

### Site templates config options

See the [Templates](/docs/site.md#templates-configuration) docs for more information on how these
[Config Options](#config-options) are used by site and item templates:

- `TEMPLATES_CACHE_BUST_VALUE`
- `TEMPLATES_ITEM_CONTACT_ENDPOINT`
- `TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY`
- `TEMPLATES_ITEM_MAPS_ENDPOINT`
- `TEMPLATES_ITEM_VERSIONS_ENDPOINT`
- `TEMPLATES_PLAUSIBLE_DOMAIN`

### Development task options

See the [Development Tasks Configuration](/docs/dev.md#development-tasks-config) docs for information on additional
config options used by development tasks.

## Config option types

All [Config Options](#config-options) are read as string values. They will then be parsed and cast to the listed type
by the `Config` class. E.g. `'true'` and `'True'` will be parsed as Python's `True` constant for a boolean option.

## Config validation

The `Config.validate()` method performs limited validation of configurable [Config Options](#config-options), raising
an exception if invalid.

This checks whether required options are set and can be parsed, it does not check whether access credentials work with
a remote service for example. These sorts of errors SHOULD be caught elsewhere in the application.

> [!TIP]
> Run the `config-check` [Development Task](/docs/dev.md#development-tasks) to validate the current configuration.

## Config listing

The `Config.dumps_safe()` method returns a typed dict of [Config Options](#config-options). For sensitive options, only
'safe' (redacted) versions are returned.

> [!TIP]
> Run the `config-show` [Development Task](/docs/dev.md#development-tasks) to validate the current configuration.

## Generate an environment config file

Run the `config-init` [Development Task](/docs/dev.md#development-tasks) to generate a new `.env` file from the
`resources/dev/.env.tpl` template.

> [!IMPORTANT]
> This uses the [1Password CLI](https://developer.1password.com/docs/cli/) to inject relevant secrets. You must have
> access to the MAGIC 1Password vault to run this task.

## Adding configuration options

See the [Development](/docs/dev.md#adding-configuration-options) documentation.
