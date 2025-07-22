# Lantern - Setup

Resources for managing:

* the [GitLab](/docs/architecture.md#gitlab) project for storing and versioning records
  * is initially manually provisioned until the multiple repositories that have been used for records tracking are
    rationalised into a single history
* the [AWS S3](/docs/architecture.md#amazon-s3) based static website hosting
  * are reused from and managed by the
    [ADD Metadata Toolbox](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/setup.md) project

## IAM policy for static website hosting

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
