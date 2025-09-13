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

## Power Automate

### Power Automate SharePoint proxy

1. import `src/lantern/resources/flows/lantern-sharepoint-proxy.zip` into Power Automate as a new flow
2. configure the flow connections and generate a HTTP endpoint
3. set the `VERIFY_SHAREPOINT_PROXY_ENDPOINT` [Config](/docs/config.md) option
