# Lantern - Infrastructure

## Environments

Available environments:

- development:
  - for prototyping and making changes (see [Development](/docs/dev.md) documentation)
  - hosted locally
- integration:
  - for pre-release testing and experimentation
  - externally accessible
- production:
  - for real-world use
  - externally accessible

Development environments may be created and destroyed as needed. Staging and Production environments are long-lived.

## 1Password

- [Service Account 🔒](https://magic.1password.eu/developer-tools/infrastructure-secrets/serviceaccount/4MR5NL7W45AA3GAFGRZMVN2H2I)
  - to allow access to secrets in [Continuous Integration](/docs/dev.md#continuous-integration)

## Sentry

- [Project 🔒](https://antarctica.sentry.io/issues/?project=5197036)
  - for [Error monitoring](/docs/monitoring.md#error-monitoring)

## GitLab

- [Records Repository 🛡️](https://gitlab.data.bas.ac.uk/felnne/lantern-records-exp)
  - for [Storing](/docs/stores.md#gitlab-store) records in GitLab

## Power Automate

- [Contact Form Submissions 🔒](https://make.powerautomate.com/environments/Default-b311db95-32ad-438f-a101-7ba061712a4e/flows/shared/5e01b213-38ad-4a54-8f7c-25d3bee36101/details)
  - For item [Contact Forms](/docs/site.md#contact-form)

## Plausible

- [Dashboard 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=lesr4cnv35csmuptgqqcionbf4&h=magic.1password.eu)
  - For [Web Analytics](/docs/monitoring.md#plausible)

## Exporters

- AWS S3 publishing bucket:
  - [Integration 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=rnv7zb3jzviwsvziknpxicvqaq&h=magic.1password.eu):
    - Console: [`arn:aws:s3:::add-catalogue-integration.data.bas.ac.uk`](https://eu-west-1.console.aws.amazon.com/s3/buckets/add-catalogue-integration.data.bas.ac.uk)
  - [Production 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=hksogwx7zqx3ct2jr36cshoqpy&h=magic.1password.eu):
    - Console: [`arn:aws:s3:::add-catalogue.data.bas.ac.uk`](https://eu-west-1.console.aws.amazon.com/s3/buckets/add-catalogue.data.bas.ac.uk)
  - For [Exporters](/docs/exporters.md) to publish content

> [!IMPORTANT]
> For auditing and to follow best practice, per-user IAM credentials, with
> [Suitable Permissions](/docs/setup.md#iam-policy-for-static-website-hosting) to manage items in one these buckets,
> SHOULD be used over common credentials.
