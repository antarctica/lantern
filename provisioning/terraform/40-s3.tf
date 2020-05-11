#
# This file is used to define resources for storage resources managed through S3

# ADD Data Catalogue (Integration)
#
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://aws.amazon.com/s3/
# Terraform source: https://www.terraform.io/docs/providers/aws/r/s3_bucket.html
resource "aws_s3_bucket" "add-catalogue-integration" {
  bucket = "add-catalogue-integration.data.bas.ac.uk"

  # Canned ACL - All objects can be read by anyone, but only the owner can change them
  #
  # Source: https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl
  acl = "public-read"

  # Bucket policy - All objects can be read by anyone, but only the owner can change them
  #
  # Source: http://docs.aws.amazon.com/AmazonS3/latest/dev/example-bucket-policies.html#example-bucket-policies-use-case-2
  policy = "${file("70-resources/s3/bucket-policies/integration-public-read.json")}"

  website {
    index_document = "index.html"
    error_document = "error.html"
  }

  tags {
    Name         = "add-catalogue-integration.data.bas.ac.uk"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

# ADD Data Catalogue index (Integration)
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider being previously configured
#
# AWS source: https://aws.amazon.com/s3/
# Terraform source: https://www.terraform.io/docs/providers/aws/r/s3_bucket_object.html
resource "aws_s3_bucket_object" "add-catalogue-integration-index" {
  bucket           = "${aws_s3_bucket.add-catalogue-integration.bucket}"
  key              = "index.html"
  content          = "ADD Data Catalogue"
  website_redirect = "/master"
}

# ADD Data Catalogue (Production)
#
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://aws.amazon.com/s3/
# Terraform source: https://www.terraform.io/docs/providers/aws/r/s3_bucket.html
resource "aws_s3_bucket" "add-catalogue-production" {
  bucket = "add-catalogue.data.bas.ac.uk"

  # Canned ACL - All objects can be read by anyone, but only the owner can change them
  #
  # Source: https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl
  acl = "public-read"

  # Bucket policy - All objects can be read by anyone, but only the owner can change them
  #
  # Source: http://docs.aws.amazon.com/AmazonS3/latest/dev/example-bucket-policies.html#example-bucket-policies-use-case-2
  policy = "${file("70-resources/s3/bucket-policies/production-public-read.json")}"

  website {
    index_document = "index.html"
    error_document = "error.html"
  }

  tags {
    Name         = "add-catalogue.data.bas.ac.uk"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}
