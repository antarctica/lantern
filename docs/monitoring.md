# Lantern - Monitoring

## Monitoring configuration

These options from the app `lantern.Config` class are used to configure application logging:

- `ENABLE_FEATURE_SENTRY`: if true, enables backend [Error Monitoring](#error-monitoring) via Sentry
- `SENTRY_ENVIRONMENT`: the Sentry [Environment](https://docs.sentry.io/platforms/python/configuration/environments/) name
- `SENTRY_DSN`: Sentry backend Data Source Name (DSN) for error logging
- `TEMPLATES_SENTRY_SRC`: Sentry CDN URL for frontend error tracking and user feedback

See the [Config](/docs/config.md#config-options) docs for how to set these config options.

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
