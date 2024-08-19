# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Configuration

Application configuration options are set in per-environment classes extending a base `Config` class in
`scar_add_metadata_toolbox/config.py`. The active environment is set using the `FLASK_ENV` environment variable.

Configuration options are defined, and documented, using class properties. Some configuration options may optionally be
set at runtime using environment variables. If not set, default values will be used.

| Configuration Option                                  | Description                                                                  | Allowed Values                             | Example Value                                                              |
|-------------------------------------------------------|------------------------------------------------------------------------------|--------------------------------------------|----------------------------------------------------------------------------|
| `APP_ENABLE_SENTRY`                                   | Feature flag to enable/disable Sentry error tracking                         | True/False                                 | `true`                                                                     |
| `APP_LOGGING_LEVEL`                                   | Minimum logging level to include in application logs                         | debug/info/warning/error/critical          | `warning`                                                                  |
| `APP_AUTH_CACHE`                                      | Path to file used for client auth cache                                      | Valid file path (file will be overwritten) | `/home/user/.config/scar_add_metadata_toolbox/auth_cache.bin`              |
| `APP_SITE_PATH`                                       | Path to directory used for rendered static site content                      | Valid directory path                       | `/home/user/.config/scar_add_metadata_toolbox/_site/`                      |
| `CSW_ENDPOINT_UNPUBLISHED`                            | CSW endpoint for accessing unpublished catalogue                             | Valid URL                                  | `http://example.com/csw/unpublished`                                       |
| `CSW_ENDPOINT_PUBLISHED`                              | CSW endpoint for accessing published catalogue                               | Valid URL                                  | `http://example.com/csw/published`                                         |
| `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`              | Endpoint at which to run unpublished CSW catalogue                           | Valid URL                                  | `http://example.com/csw/unpublished`                                       |
| `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`                | Endpoint at which to run published CSW catalogue                             | Valid URL                                  | `http://example.com/csw/published`                                         |
| `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION`   | Connection string for unpublished CSW catalogue backing database             | Valid SQLAlchemy connection string         | `postgresql://postgres:password@db.example.com/postgres`                   |
| `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`     | Connection string for published CSW catalogue backing database               | Valid SQLAlchemy connection string         | `postgresql://postgres:password@db.example.com/postgres`                   |
| `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_WORKING_DIR`  | Path to directory used for CSW revision tracking local working copy          | Valid directory path                       | `/opt/var/scar_add_metadata_toolbox/revision_tracking/`                    |
| `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL`   | Connection string/URL for CSW revision tracking Git remote                   | Valid Git remote URL                       | `https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-production.git` |
| `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_GITLAB_TOKEN` | GitLab Personal Access Token used to access CSW revision tracking Git remote | Valid GitLab PAT                           | `glpat-xx...xx`                                                            |
| `APP_S3_BUCKET`                                       | AWS S3 bucket name used for hosting static website content                   | Valid AWS S3 bucket name                   | `add-catalogue.data.bas.ac.uk`                                             |

## Typical client config options

These options are typically set when running this application as a client (CLI):

* `APP_LOGGING_LEVEL`
* `APP_COLLECTIONS_PATH`
* `APP_SITE_PATH`
* `CSW_ENDPOINT_UNPUBLISHED`
* `CSW_ENDPOINT_PUBLISHED`
* `APP_S3_BUCKET`

## Typical server config options

These options are typically set when running this application as a server (CSW catalogues):

* `APP_LOGGING_LEVEL`
* `CSW_SERVER_CONFIG_UNPUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_PUBLISHED_ENDPOINT`
* `CSW_SERVER_CONFIG_UNPUBLISHED_DATABASE_CONNECTION`
* `CSW_SERVER_CONFIG_PUBLISHED_DATABASE_CONNECTION`
* `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_WORKING_DIR`
* `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL`
* `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_GITLAB_TOKEN`
