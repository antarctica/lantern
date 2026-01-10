# Lantern - Monitoring

## Monitoring configuration

These options from the app `lantern.Config` class are used to configure application logging:

- `ENABLE_FEATURE_SENTRY`: if true, enables backend [Error Monitoring](#error-monitoring) via Sentry
- `SENTRY_ENVIRONMENT`: the Sentry [Environment](https://docs.sentry.io/platforms/python/configuration/environments/) name
- `SENTRY_DSN`: Sentry backend Data Source Name (DSN) for error logging
- `TEMPLATES_SENTRY_SRC`: Sentry CDN URL for frontend error tracking and user feedback
- `VERIFY_SHAREPOINT_PROXY_ENDPOINT`: the [SharePoint Proxy](#verification-sharepoint-proxy) used for site checks
- `VERIFY_SAN_PROXY_ENDPOINT`: the [SAN Proxy](#verification-san-proxy) used for site checks

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

## Health monitoring

### Heartbeat

A static text file is available as part of the [Static Site](/docs/architecture.md#static-site) for use as a basic,
binary, health monitoring endpoint at: `/static/txt/heartbeat.txt`.

This endpoint MAY be used by monitoring tools and/or load balancers to determine if the static site is available.

A non-200 status code MUST be considered as the static site being unavailable.

## Sentry

### Error monitoring

Errors in the Python backend (where enabled) and frontend [Static Site](/docs/site.md) (always) are logged to
[Sentry](https://sentry.io) for aggregation and alerting.

- [Sentry Project 🔒](/docs/infrastructure.md#sentry)

Alerts are sent via email and to the `#dev` channel in the MAGIC Teams workspace.

### Uptime checks

A Sentry [Uptime Check](https://docs.sentry.io/product/uptime-monitoring/) checks the
[MAGIC Team](https://data.bas.ac.uk/collections/magic) collection page returns a 2xx response in the production
environment every 5 minutes, automatically following the [Item Alias](/docs/data-model.md#item-aliases) redirect.

### User feedback

Sentry's [User Feedback](https://docs.sentry.io/product/user-feedback/) feature is used to collect user feedback via
a widget shown in the [Static Site](/docs/site.md).

> [!WARNING]
> Sentry user feedback is only retained for 90 days. An anonymous version can be copied to GitLab if needed.

## Plausible

[Plausible](https://plausible.io) is used for recording web analytics in the frontend [Static Site](/docs/site.md).

- [Plausible Dashboard 🔒](/docs/infrastructure.md#plausible)

## Site verification

A series of checks can be run to verify the contents of a generated site against expected values.

[Verification checks](#verification-checks) are run and compiled into a [Verification report](#verification-report) by
the [Verification Exporter](/docs/exporters.md#verification-exporter).

### Verification checks

Checks are run for:

- site 404 handler (by requesting a page known not to exist)
- site pages (legal policy pages, formatting guide, etc.)
- [Record](/docs/data-model.md#records) pages (JSON, XML, HTML)
- [Item](/docs/data-model.md#items) pages (HTML)
- [Item Alias](/docs/data-model.md#item-aliases) redirects
- Item DOI redirects
- Item distribution options (as links on Item pages)
- File distribution options (with special support for SharePoint and NORA hosted files)
- ArcGIS layers and services (via the ArcGIS API)

Checks are skipped for:

- SAN reference distribution options (as there is no allowed access method)

For Record and Item checks, all records in the [Store](/docs/architecture.md) are checked.

For most checks, HEAD requests are used to check the HTTP status code is expected (typically `200`) without requesting
any content. In addition:

- for redirects, the `location` header is checked. Redirects are also followed to check they reach a `200` status
- for files, the `content-length` header is optionally checked if an expected value is known
- for NORA hosted files, a GET request with a byte range is used as NORA gives false negatives using HEAD requests
- for SharePoint hosted files, a [Proxy](#verification-sharepoint-proxy) is used to allow access to restricted content
- for SAN references, a [Proxy](#verification-san-proxy) is used to allow to validate target paths
- for ArcGIS layers and services, the response is checked for errors (as ArcGIS returns a `200` even for missing items)

Checks are not run for:

- static assets (CSS, fonts, images, etc.)

Some checks are skipped depending on the environment being checked:

- 404 and redirect checks are skipped when using a local Python server (as it does not support either feature)
- DOI redirect checks are skipped when not using the production environment (as they only work in production)

#### Verification SharePoint proxy

SharePoint files hosted in the NERC tenancy cannot be accessed anonymously. A Power Automate flow is used as a basic
proxy to return the file size (content-length) of a given path parsed from the Item distribution option URL.

See the [Setup](/docs/setup.md#power-automate-sharepoint-proxy) docs for more information on setting up this proxy.

> [!NOTE]
> The 'GetFileMetadataByPath' operation within this flow MUST be connected to an account that can access all files
> across all Items hosted in SharePoint.

#### Verification SAN proxy

> [!IMPORTANT]
> This proxy is not used for operational reasons.

SAN references cannot be accessed anonymously. A Power Automate flow can be used as a basic proxy to validate the
specified path exists on the SAN. This check does not verify the path contains expected data (as we don't know what to
expect).

See the [Setup](/docs/setup.md#power-automate-san-proxy) docs for more information on setting up this proxy.

> [!NOTE]
> The 'List files in folder' operation within this flow MUST be connected to an account that can access all files
> across all Items referenced from the SAN.

### Verification report

The results from [Verification Checks](#verification-checks) are compiled into a JSON and HTML report for manual review
and/or optional additional processing:

- JSON report: `/-/verification/data.json`
- HTML report: `/-/verification/index.html`

### Scheduled verification

The production environment is automatically verified via a cron job running on the BAS central workstations:

- scope: all items
- frequency: Wednesdays at 12:15 (local time)
- results: [data.bas.ac.uk/-/verification/](https://data.bas.ac.uk/-/verification/))
- logs: `/users/geoweb/cron_logs/lantern/lantern-verify-*.log`
- log retention: 90 days (enforced monthly)
