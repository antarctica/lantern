#
# This file is used to define resources for storage resources managed through S3

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Buckets
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *


# ADD Data Catalogue (Integration)
#
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://aws.amazon.com/s3/
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket
resource "aws_s3_bucket" "add-catalogue-integration" {
  bucket = "add-catalogue-integration.data.bas.ac.uk"

  tags = {
    Name         = "add-catalogue-integration.data.bas.ac.uk"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

# ADD Data Catalogue (Production)
#
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://aws.amazon.com/s3/
# Terraform source: https://www.terraform.io/docs/providers/aws/r/s3_bucket.html
resource "aws_s3_bucket" "add-catalogue-production" {
  bucket = "add-catalogue.data.bas.ac.uk"

  tags = {
    Name         = "add-catalogue.data.bas.ac.uk"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Static website hosting
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# ADD Data Catalogue (Integration)
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_website_configuration
resource "aws_s3_bucket_website_configuration" "add-catalogue-integration" {
  bucket = aws_s3_bucket.add-catalogue-integration.bucket

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# ADD Data Catalogue (Integration)
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_website_configuration
resource "aws_s3_bucket_website_configuration" "add-catalogue-production" {
  bucket = aws_s3_bucket.add-catalogue-production.bucket

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Permissions
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# ADD Data Catalogue (Integration)
#
# This canned ACL allows objects to be read by anyone, but only changed by the owner
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_acl
resource "aws_s3_bucket_acl" "add-catalogue-integration" {
  bucket = aws_s3_bucket.add-catalogue-integration.id
  acl    = "public-read"
}

# ADD Data Catalogue (Production)
#
# This canned ACL allows objects to be read by anyone, but only changed by the owner
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_acl
resource "aws_s3_bucket_acl" "add-catalogue-production" {
  bucket = aws_s3_bucket.add-catalogue-production.id
  acl    = "public-read"
}
