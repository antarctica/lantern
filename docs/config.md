# Lantern - Configuration

Application configuration is managed by the `lantern.Config` class.

> [!TIP]
> User configurable options can be defined using environment variables and/or an `.env` file, with environment
> variables taking precedence. Variables are prefixed with `LANTERN_` to avoid conflicts with other applications.
>
> E.g. use `LANTERN_FOO` to set a `FOO` option.

> [!NOTE]
> Config option values may be [Overridden](/docs/dev.md#pytest-env) in application tests.

## Config options

| Option                            | Type    | Configurable | Required | Sensitive | Since Version | Summary                                                                  | Default                                   | Example                                   |
|-----------------------------------|---------|--------------|----------|-----------|---------------|--------------------------------------------------------------------------|-------------------------------------------|-------------------------------------------|
| `AWS_ACCESS_ID`                   | String  | Yes          | Yes      | No        | v0.1.x        | AWS IAM user identifier for site exporter remote uploads                 | *None*                                    | 'x'                                       |
| `AWS_ACCESS_SECRET`               | String  | Yes          | Yes      | Yes       | v0.1.x        | AWS IAM user secret for site exporter remote uploads                     | *None*                                    | 'x'                                       |
| `AWS_ACCESS_SECRET_SAFE`          | String  | No           | -        | -         | v0.1.x        | Redacted version of `STORE_GITLAB_TOKEN`                                 | *N/A*                                     | 'REDACTED'                                |
| `AWS_S3_BUCKET`                   | String  | Yes          | Yes      | No        | v0.1.x        | Location for remote static site exporter builds                          | *None*                                    | './exports/'                              |
| `ENABLE_FEATURE_SENTRY`           | Boolean | Yes          | No       | No        | v0.1.x        | Enables Sentry monitoring if true                                        | *True*                                    | *True*                                    |
| `EXPORT_PATH`                     | Path    | Yes          | Yes      | No        | v0.1.x        | Location for local static site exporter builds                           | *None*                                    | '/data/exports/records'                   |
| `LOG_LEVEL`                       | Number  | Yes          | No       | No        | v0.1.x        | A logging level name or number to set the application logging level      | 30                                        | 20                                        |
| `LOG_LEVEL_NAME`                  | String  | No           | -        | -         | v0.1.x        | Logging level name for the configured application logging level          | 'WARNING'                                 | 'INFO'                                    |
| `SENTRY_DSN`                      | String  | No           | -        | -         | v0.4.x        | Sentry connection string for backend error monitoring (not sensitive)    | *N/A*                                     | 'https://123@example.com/123'             |
| `SENTRY_ENVIRONMENT`              | String  | Yes          | No       | No        | v0.1.x        | Application runtime environment to include in Sentry errors              | 'development'                             | 'production'                              |
| `STORE_GITLAB_STORE_CACHE_PATH`   | Path    | Yes          | Yes      | No        | v0.1.x        | Location for GitLab store's local records cache                          | *None*                                    | '/tmp/gitlab_cache/'                      |
| `STORE_GITLAB_STORE_ENDPOINT`     | String  | Yes          | Yes      | No        | v0.1.x        | base API endpoint for GitLab store's remote instance                     | *None*                                    | 'https://gitlab.com'                      |
| `STORE_GITLAB_STORE_PROJECT_ID`   | String  | Yes          | Yes      | No        | v0.1.x        | GitLab project ID for GitLab store's remote instance                     | *None*                                    | '123'                                     |
| `STORE_GITLAB_TOKEN`              | String  | Yes          | Yes      | Yes       | v0.1.x        | API access token for GitLab store's remote instance                      | *None*                                    | 'REDACTED'                                |
| `STORE_GITLAB_TOKEN_SAFE`         | String  | No           | -        | -         | v0.1.x        | Redacted version of `STORE_GITLAB_TOKEN`                                 | *N/A*                                     | 'REDACTED'                                |
| `TEMPLATES_CACHE_BUST_VALUE`      | String  | No           | -        | -         | v0.1.x        | Query string value appended to site assets to avoid stale browser caches | *N/A*                                     | '0.3.0'                                   |
| `TEMPLATES_ITEM_CONTACT_ENDPOINT` | String  | Yes          | Yes      | No        | v0.1.x        | Microsoft Power Automate trigger endpoint for item contact form          | *N/A*                                     | 'https://example.com/...'                 |
| `TEMPLATES_ITEM_MAPS_ENDPOINT`    | String  | Yes          | No       | No        | v0.1.x        | Embedded Maps Service base endpoint                                      | `https://embedded-maps.data.bas.ac.uk/v1` | 'https://embedded-maps.data.bas.ac.uk/v1' |
| `TEMPLATES_PLAUSIBLE_DOMAIN`      | String  | No           | -        | -         | v0.1.x        | Plausible site identifier for frontend analytics                         | *None*                                    | 'example'                                 |
| `TEMPLATES_SENTRY_SRC`            | String  | No           | -        | No        | v0.1.x        | Sentry CDN project URL for frontend error tracking and user feedback     | *N/A*                                     | 'https://example.com'                     |
| `VERSION`                         | String  | No           | -        | -         | v0.1.x        | Application package version                                              | *N/A*                                     | '0.3.0'                                   |

### Monitoring config options

See the [Monitoring](/docs/monitoring.md#monitoring-configuration) docs for more information on how these
[Config Options](#config-options) are used to configure app monitoring (inc. Sentry):

- `ENABLE_FEATURE_SENTRY`
- `SENTRY_ENVIRONMENT`
- `SENTRY_DSN`
- `TEMPLATES_SENTRY_SRC`

### GitLab Store config options

See the [Stores](/docs/stores.md#stores-configuration) docs for more information on how these
[Config Options](#config-options) are used by stores:

- `STORE_GITLAB_STORE_CACHE_PATH`
- `STORE_GITLAB_STORE_ENDPOINT`
- `STORE_GITLAB_STORE_PROJECT_ID`
- `STORE_GITLAB_TOKEN`
- `STORE_GITLAB_TOKEN_SAFE`

### Site exporter config options

See the [Exporters](/docs/exporters.md#exporters-configuration) docs for more information on how these
[Config Options](#config-options) are used by exporters:

- `EXPORT_PATH`
- `AWS_ACCESS_ID`
- `AWS_ACCESS_SECRET`
- `AWS_ACCESS_SECRET_SAFE`
- `AWS_S3_BUCKET`

### Site templates config options

See the [Templates](/docs/site.md#templates-configuration) docs for more information on how these
[Config Options](#config-options) are used by site and item templates:

- `TEMPLATES_CACHE_BUST_VALUE`
- `TEMPLATES_ITEM_CONTACT_ENDPOINT`
- `TEMPLATES_ITEM_MAPS_ENDPOINT`
- `TEMPLATES_PLAUSIBLE_DOMAIN`

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

> [!TIP]
> Run the `config-init` [Development Task](/docs/dev.md#development-tasks) to generate a new `.env` file from the
> `.env.tpl` template.

> [!IMPORTANT]
> This uses the [1Password CLI](https://developer.1password.com/docs/cli/) to inject relevant secrets. You must have
> access to the MAGIC 1Password vault to run this task.

## Adding configuration options

See the [Developing](/docs/dev.md#adding-configuration-options) documentation.
