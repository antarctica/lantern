# Lantern - Setup

> [!CAUTION]
> This section is Work in Progress (WIP) and is not complete/accurate.

Resources for managing:

* the [GitLab](/docs/architecture.md#gitlab) project for storing and versioning records is initially manually
  provisioned until the multiple repositories that have been used for records tracking can be rationalised into a
  single history
* the [AWS S3](/docs/architecture.md#amazon-s3) based static website hosting is reused from and managed by the
  [ADD Metadata Toolbox](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/setup.md) project

## Sentry

1. register a new Sentry project
2. from *Project Settings* > *Client Keys*:
   1. from the *Credentials* section, copy the *DSN* and set as the `SENTRY_DSN` [Config](/docs/config.md) fixed value
   2. from the *JavaScript Loader Script* section:
      1. set the SDK version to the highest/latest available
      2. enable the *Session Reply* option (needed for the user feedback widget to work)
      3. copy the script and set as the `TEMPLATES_SENTRY_SRC` [Config](/docs/config.md) fixed value

> ![NOTE]
> The Sentry DSN and JavaScript Loader Script are not considered secrets.

## Static website hosting

### IAM policy for static website hosting

The following IAM policy can be attached to users for managing content in the
[Static Website Hosting](/docs/architecture.md#static-site) S3 bucket.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "MinimalRuntimePermissions",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::add-catalogue-integration.data.bas.ac.uk",
                "arn:aws:s3:::add-catalogue-integration.data.bas.ac.uk/*",
                "arn:aws:s3:::add-catalogue.data.bas.ac.uk",
                "arn:aws:s3:::add-catalogue.data.bas.ac.uk/*"
            ]
        }
    ]
}
```

## Public Website Search

To configure a WordPress site to work with the
[Public Website Search Exporter](/docs/exporters.md#public-website-search-exporter):

1. create a WordPress site
2. as an administrator, install and activate the prototype plugin from `/support/public-website-search/wp-plugin.zip`
3. as an administrator, install and activate the prototype theme from `/support/public-website-search/wp-theme.zip`
4. create a new user with the *author* role to represent this integration, recording the password in 1Password
5. update the [Infrastructure](/docs/infrastructure.md) documentation
6. set the relevant [Config](/docs/config.md) values for the integration
