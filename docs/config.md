# Lantern - Configuration

> [!NOTE]
> Parts of this page are specific to the [BAS Catalogue](/docs/architecture.md#bas-catalogue).

Application configuration is managed by the `lantern.Config` class using environment variables.

All variables are prefixed with `LANTERN_` to avoid conflicts with other applications. E.g. use `LANTERN_FOO` to set a
`FOO` option.

<!-- pyml disable md028 -->
> [!TIP]
> Configurable options can be defined using environment variables and/or an `.env` file, with environment variables
> taking precedence.

> [!NOTE]
> Config option values may be [Overridden](/docs/dev.md#pytest-env) in application tests.
<!-- pyml enable md028 -->

## Config options

<!-- pyml disable md013 -->
| Option                                  | Type         | Configurable | Required | Sensitive | Since Version | Summary                                                                  | Default                                   | Example                                         |
|-----------------------------------------|--------------|--------------|----------|-----------|---------------|--------------------------------------------------------------------------|-------------------------------------------|-------------------------------------------------|
| `ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE` | JSON Web Key | Yes          | Yes      | Yes       | v0.4.x        | JSON Web Key (JWK) for accessing administrative metadata                 | *None*                                    | '{"kid": "magic_metadata_encryption_key", ...}' |
| `ADMIN_METADATA_SIGNING_KEY_PUBLIC`     | JSON Web Key | Yes          | Yes      | No        | v0.4.x        | JSON Web Key (JWK) for verifying administrative metadata                 | *None*                                    | '{"kid": "magic_metadata_signing_key", ...}'    |
| `BASE_URL_LIVE`                         | String       | Yes          | Yes      | No        | v0.6.x        | Base URL for production/live catalogue (typically reverse proxied)       | *None*                                    | 'https://example.com'                           |
| `BASE_URL_TESTING`                      | String       | Yes          | Yes      | No        | v0.6.x        | Base URL for staging/testing catalogue (typically reverse proxied)       | *None*                                    | 'https://example.com'                           |
| `ENABLE_FEATURE_SENTRY`                 | Boolean      | Yes          | No       | No        | v0.1.x        | Enables Sentry monitoring if true                                        | *True*                                    | 'true'                                          |
| `LOG_LEVEL`                             | Number       | Yes          | No       | No        | v0.1.x        | A logging level name or number to set the application logging level      | 30                                        | '20'                                            |
| `LOG_LEVEL_NAME`                        | String       | No           | -        | No        | v0.1.x        | Logging level name for the configured application logging level          | 'WARNING'                                 | 'INFO'                                          |
| `PARALLEL_JOBS`                         | Number       | Yes          | No       | No        | v0.3.x        | Number of parallel jobs to run for applicable tasks                      | 1                                         | '4'                                             |
| `SENTRY_DSN`                            | String       | No           | -        | No        | v0.1.x        | Sentry connection string for backend error monitoring (not sensitive)    | *N/A*                                     | 'https://example.com'                           |
| `SENTRY_ENVIRONMENT`                    | String       | Yes          | No       | No        | v0.1.x        | Application runtime environment to include in Sentry errors              | 'development'                             | 'production'                                    |
| `SITE_TRUSTED_RSYNC_BASE_PATH_LIVE`     | String       | Yes          | Yes      | No        | v0.6.x        | Path for trusted site content within upload server (live environment)    | *None*                                    | '/data/content/live'                            |
| `SITE_TRUSTED_RSYNC_BASE_PATH_TESTING`  | String       | Yes          | Yes      | No        | v0.6.x        | Path for trusted site content within upload server (testing environment) | *None*                                    | '/data/content/testing'                         |
| `SITE_TRUSTED_RSYNC_HOST`               | String       | Yes          | Yes      | No        | v0.6.x        | SSH config alias for trusted site uploads                                | *None*                                    | "lantern-trusted-content"                       |
| `SITE_UNTRUSTED_S3_ACCESS_ID`           | String       | Yes          | Yes      | No        | v0.6.x        | AWS IAM user identifier for untrusted site uploads                       | *None*                                    | 'xxx'                                           |
| `SITE_UNTRUSTED_S3_ACCESS_SECRET`       | String       | Yes          | Yes      | Yes       | v0.6.x        | AWS IAM user secret for untrusted site uploads                           | *None*                                    | 'xxx'                                           |
| `SITE_UNTRUSTED_S3_ACCESS_SECRET_SAFE`  | String       | Yes          | Yes      | Yes       | v0.6.x        | Redacted version of `SITE_UNTRUSTED_S3_ACCESS_SECRET`                    | *N/A*                                     | 'REDACTED'                                      |
| `SITE_UNTRUSTED_S3_BUCKET_LIVE`         | String       | Yes          | Yes      | No        | v0.6.x        | AWS S3 bucket used for untrusted site uploads (live environment)         | *None*                                    | 'example.com'                                   |
| `SITE_UNTRUSTED_S3_BUCKET_TESTING`      | String       | Yes          | Yes      | No        | v0.6.x        | AWS S3 bucket used for untrusted site uploads (testing environment)      | *None*                                    | 'testing.example.com'                           |
| `STORE_GITLAB_CACHE_PATH`               | Path         | Yes          | Yes      | No        | v0.1.x        | Location for GitLab store's local records cache                          | *None*                                    | '/tmp/gitlab_cache/'                            |
| `STORE_GITLAB_DEFAULT_BRANCH`           | String       | Yes          | Yes      | No        | v0.6.x        | GitLab store's default remote branch name                                | *None*                                    | 'main'                                          |
| `STORE_GITLAB_ENDPOINT`                 | String       | Yes          | Yes      | No        | v0.1.x        | Base API endpoint for GitLab store's remote instance                     | *None*                                    | 'https://gitlab.com'                            |
| `STORE_GITLAB_PROJECT_ID`               | String       | Yes          | Yes      | No        | v0.1.x        | GitLab project ID for GitLab store's remote instance                     | *None*                                    | '123'                                           |
| `STORE_GITLAB_TOKEN`                    | String       | Yes          | Yes      | Yes       | v0.1.x        | API access token for GitLab store's remote instance                      | *None*                                    | 'REDACTED'                                      |
| `STORE_GITLAB_TOKEN_SAFE`               | String       | No           | -        | No        | v0.1.x        | Redacted version of `STORE_GITLAB_TOKEN`                                 | *N/A*                                     | 'REDACTED'                                      |
| `TEMPLATES_CACHE_BUST_VALUE`            | String       | No           | -        | No        | v0.1.x        | Query string value appended to site assets to avoid stale browser caches | *N/A*                                     | '0.3.0'                                         |
| `TEMPLATES_ITEM_CONTACT_ENDPOINT`       | String       | Yes          | Yes      | No        | v0.1.x        | Microsoft Power Automate trigger endpoint for item contact form          | *N/A*                                     | 'https://example.com'                           |
| `TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY`  | String       | Yes          | Yes      | No        | v0.4.x        | Cloudflare Turnstile site key for item contact form                      | *N/A*                                     | 'x'                                             |
| `TEMPLATES_ITEM_MAPS_ENDPOINT`          | String       | Yes          | No       | No        | v0.1.x        | Embedded Maps Service base endpoint                                      | `https://embedded-maps.data.bas.ac.uk/v1` | 'https://embedded-maps.data.bas.ac.uk/v1'       |
| `TEMPLATES_ITEM_VERSIONS_ENDPOINT`      | String       | Yes          | Yes      | No        | v0.2.x        | Base URL to a GitLab project for viewing item record revisions           | *None*                                    | 'https://example.com'                           |
| `TEMPLATES_PLAUSIBLE_ID`                | String       | No           | -        | No        | v0.5.x        | Plausible site identifier for frontend analytics                         | *None*                                    | 'pa-xxx'                                        |
| `VERSION`                               | String       | No           | -        | No        | v0.1.x        | Application package version                                              | *N/A*                                     | '0.3.0'                                         |
<!-- pyml enable md013 -->

### Data model config options

- `ADMIN_METADATA_ENCRYPTION_KEY_PRIVATE`
- `ADMIN_METADATA_SIGNING_KEY_PUBLIC`

### Performance config options

- `PARALLEL_JOBS`

Some tasks such as populating caches, generating and uploading content, etc. can run in parallel for better performance.

The `PARALLEL_JOBS` option sets the maximum number of parallel jobs to run.

Where `1` disables parallelism and `-1` uses all available CPU cores. Non-positive integers (except `-1`) will give a
validator error. Defaults to `1` (no parallelism).

### Monitoring config options

See the [Monitoring](/docs/monitoring.md#monitoring-configuration) docs for more information on how these
[Config Options](#config-options) are used to configure app monitoring (inc. Sentry):

- `ENABLE_FEATURE_SENTRY`
- `SENTRY_ENVIRONMENT`
- `SENTRY_DSN`

### GitLab Store config options

See the [Stores](/docs/stores.md#stores-configuration) docs for more information on how these
[Config Options](#config-options) are used by stores:

- `STORE_GITLAB_CACHE_PATH`
- `STORE_GITLAB_DEFAULT_BRANCH`
- `STORE_GITLAB_ENDPOINT`
- `STORE_GITLAB_PROJECT_ID`
- `STORE_GITLAB_TOKEN`
- `STORE_GITLAB_TOKEN_SAFE`

### Exporter config options

See the [Exporters](/docs/exporters.md#exporters-configuration) docs for more information on how these
[Config Options](#config-options) are used by exporters:

- `SITE_TRUSTED_RSYNC_HOST`
- `SITE_TRUSTED_RSYNC_BASE_PATH_LIVE`
- `SITE_TRUSTED_RSYNC_BASE_PATH_TESTING`
- `SITE_UNTRUSTED_S3_ACCESS_ID`
- `SITE_UNTRUSTED_S3_ACCESS_SECRET`
- `SITE_UNTRUSTED_S3_ACCESS_SECRET_SAFE`
- `SITE_UNTRUSTED_S3_BUCKET_LIVE`
- `SITE_UNTRUSTED_S3_BUCKET_TESTING`

### Site templates config options

See the [Templates](/docs/site.md#templates-configuration) docs for more information on how these
[Config Options](#config-options) are used by site and item templates:

- `TEMPLATES_CACHE_BUST_VALUE`
- `TEMPLATES_ITEM_CONTACT_ENDPOINT`
- `TEMPLATES_ITEM_CONTACT_TURNSTILE_KEY`
- `TEMPLATES_ITEM_MAPS_ENDPOINT`
- `TEMPLATES_ITEM_VERSIONS_ENDPOINT`
- `TEMPLATES_PLAUSIBLE_ID`

### Development task options

See the [Development Tasks Configuration](/docs/dev.md#development-tasks-config) docs for information on additional
config options used by development tasks.

## Config option types

All [Config Options](#config-options) are read as string values. They will then be parsed and cast to the listed type
by the `Config` class. E.g. `'true'` and `'True'` will be parsed as Python's `True` constant for a boolean option.

## Config validation

Missing, required, config options will raise a `environs.exceptions.EnvError` on property access via the
environs package.

[Marshmallow](https://marshmallow.readthedocs.io/en/stable/marshmallow.validate.html and custom validation methods MAY
additionally validate some config options, raising `environs.exceptions.EnvValidationError` (a `EnvError` subclass) if
invalid.

> [!WARNING]
> This validation is basic/limited, checking a value is a URL for example, not that it points to a particular type of
> service. Additional validation and error handling SHOULD be caught elsewhere in the application.

The `Config.validate()` method can be used to force validation of all properties.

> [!TIP]
> Run the `config-check` [Development Task](/docs/dev.md#development-tasks) to call this method and return the current
> configuration if valid.

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
