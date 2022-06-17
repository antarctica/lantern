#
# This file is used to define compute resources managed through Lambda

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Function source code
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# ADD Data Catalogue - Downloads Proxy (Staging)
#
# Represents the source code for the 'add-catalogue-downloads-proxy-stage' Lambda function.
# The contents `downloads-proxy-stage.zip` is a zip file containing `./support/downloads-proxy/index.js`.
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-downloads-proxy-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_object
resource "aws_s3_object" "add-catalogue-downloads-proxy-package-staging" {
  bucket = aws_s3_bucket.add-catalogue-downloads-proxy-staging.bucket
  key    = "downloads-proxy-stage.zip"
  source = "/data/support/downloads-proxy/downloads-proxy-stage.zip"
  etag   = filemd5("/data/support/downloads-proxy/downloads-proxy-stage.zip")

  tags = {
    X-Name       = "add-catalogue-downloads-proxy-stage"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

# ADD Data Catalogue - Downloads Proxy (Production)
#
# Represents the source code for the 'add-catalogue-downloads-proxy-prod' Lambda function.
# The contents `downloads-proxy-prod.zip` is a zip file containing `./support/downloads-proxy/index.js`.
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-downloads-proxy-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_object
resource "aws_s3_object" "add-catalogue-downloads-proxy-package-production" {
  bucket = aws_s3_bucket.add-catalogue-downloads-proxy-production.bucket
  key    = "downloads-proxy-prod.zip"
  source = "/data/support/downloads-proxy/downloads-proxy-prod.zip"
  etag   = filemd5("/data/support/downloads-proxy/downloads-proxy-prod.zip")

  tags = {
    X-Name       = "add-catalogue-downloads-proxy-prod"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Functions
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# ADD Data Catalogue - Downloads Proxy [Read] (Staging)
#
# This resource explicitly depends on the 'aws_iam_role.add-catalogue-downloads-proxy-staging' resource
# This resource implicitly depends on the 'aws_s3_object.add-catalogue-downloads-proxy-package-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/index.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
//noinspection HILUnresolvedReference
resource "aws_lambda_function" "add-catalogue-downloads-proxy-staging" {
  function_name     = "add-catalogue-downloads-proxy-stage"
  role              = aws_iam_role.add-catalogue-downloads-proxy-staging.arn
  runtime           = "nodejs16.x"
  s3_bucket         = aws_s3_object.add-catalogue-downloads-proxy-package-staging.bucket
  s3_key            = aws_s3_object.add-catalogue-downloads-proxy-package-staging.key
  s3_object_version = aws_s3_object.add-catalogue-downloads-proxy-package-staging.version_id
  handler           = "index.handler_read"

  environment {
    variables = {
      ENVIRONMENT_NAME = "staging"
      S3_BUCKET        = aws_s3_object.add-catalogue-downloads-proxy-package-staging.bucket
    }
  }

  tags = {
    Name          = "add-catalogue-downloads-proxy-stage"
    X-Project     = "ADD Data Catalogue"
    X-Managed-By  = "Terraform"
    X-Environment = "Staging"
  }
}

# ADD Data Catalogue - Downloads Proxy [Read] (Production)
#
# This resource explicitly depends on the 'aws_iam_role.add-catalogue-downloads-proxy-production' resource
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-downloads-proxy-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/index.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
//noinspection HILUnresolvedReference
resource "aws_lambda_function" "add-catalogue-downloads-proxy-production" {
  function_name     = "add-catalogue-downloads-proxy-prod"
  role              = aws_iam_role.add-catalogue-downloads-proxy-production.arn
  runtime           = "nodejs16.x"
  s3_bucket         = aws_s3_object.add-catalogue-downloads-proxy-package-production.bucket
  s3_key            = aws_s3_object.add-catalogue-downloads-proxy-package-production.key
  s3_object_version = aws_s3_object.add-catalogue-downloads-proxy-package-production.version_id
  handler           = "index.handler_read"

  environment {
    variables = {
      ENVIRONMENT_NAME = "production"
      S3_BUCKET        = aws_s3_object.add-catalogue-downloads-proxy-package-production.bucket
    }
  }

  tags = {
    Name          = "add-catalogue-downloads-proxy-prod"
    X-Project     = "ADD Data Catalogue"
    X-Managed-By  = "Terraform"
    X-Environment = "Production"
  }
}

# ADD Data Catalogue - Downloads Proxy [Write] (Staging)
#
# This resource explicitly depends on the 'aws_iam_role.add-catalogue-downloads-proxy-staging' resource
# This resource implicitly depends on the 'aws_s3_object.add-catalogue-downloads-proxy-package-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/index.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
//noinspection HILUnresolvedReference
resource "aws_lambda_function" "add-catalogue-downloads-proxy-write-staging" {
  function_name     = "add-catalogue-downloads-proxy-write-stage"
  role              = aws_iam_role.add-catalogue-downloads-proxy-staging.arn
  runtime           = "nodejs16.x"
  s3_bucket         = aws_s3_object.add-catalogue-downloads-proxy-package-staging.bucket
  s3_key            = aws_s3_object.add-catalogue-downloads-proxy-package-staging.key
  s3_object_version = aws_s3_object.add-catalogue-downloads-proxy-package-staging.version_id
  handler           = "index.handler_write"

  environment {
    variables = {
      ENVIRONMENT_NAME = "staging"
      S3_BUCKET        = aws_s3_object.add-catalogue-downloads-proxy-package-staging.bucket
    }
  }

  tags = {
    Name          = "add-catalogue-downloads-proxy-write-stage"
    X-Project     = "ADD Data Catalogue"
    X-Managed-By  = "Terraform"
    X-Environment = "Staging"
  }
}

# ADD Data Catalogue - Downloads Proxy [Write] (Production)
#
# This resource explicitly depends on the 'aws_iam_role.add-catalogue-downloads-proxy-production' resource
# This resource implicitly depends on the 'aws_s3_object.add-catalogue-downloads-proxy-package-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/index.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
//noinspection HILUnresolvedReference
resource "aws_lambda_function" "add-catalogue-downloads-proxy-write-production" {
  function_name     = "add-catalogue-downloads-proxy-write-prod"
  role              = aws_iam_role.add-catalogue-downloads-proxy-production.arn
  runtime           = "nodejs16.x"
  s3_bucket         = aws_s3_object.add-catalogue-downloads-proxy-package-production.bucket
  s3_key            = aws_s3_object.add-catalogue-downloads-proxy-package-production.key
  s3_object_version = aws_s3_object.add-catalogue-downloads-proxy-package-production.version_id
  handler           = "index.handler_write"

  environment {
    variables = {
      ENVIRONMENT_NAME = "production"
      S3_BUCKET        = aws_s3_object.add-catalogue-downloads-proxy-package-production.bucket
    }
  }

  tags = {
    Name          = "add-catalogue-downloads-proxy-write-prod"
    X-Project     = "ADD Data Catalogue"
    X-Managed-By  = "Terraform"
    X-Environment = "Production"
  }
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Function URLs
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# ADD Data Catalogue - Downloads Proxy [Read] (Staging)
#
# This resource implicitly depends on the 'aws_lambda_function.add-catalogue-downloads-proxy-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url
resource "aws_lambda_function_url" "add-catalogue-downloads-proxy-staging-latest" {
  function_name      = aws_lambda_function.add-catalogue-downloads-proxy-staging.function_name
  authorization_type = "NONE"
}

# ADD Data Catalogue - Downloads Proxy [Read] (Production)
#
# This resource implicitly depends on the 'aws_lambda_function.add-catalogue-downloads-proxy-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url
resource "aws_lambda_function_url" "add-catalogue-downloads-proxy-production-latest" {
  function_name      = aws_lambda_function.add-catalogue-downloads-proxy-production.function_name
  authorization_type = "NONE"
}

# ADD Data Catalogue - Downloads Proxy [Write] (Staging)
#
# This resource implicitly depends on the 'aws_lambda_function.add-catalogue-downloads-proxy-write-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url
resource "aws_lambda_function_url" "add-catalogue-downloads-proxy-write-staging-latest" {
  function_name      = aws_lambda_function.add-catalogue-downloads-proxy-write-staging.function_name
  authorization_type = "AWS_IAM"
}

# ADD Data Catalogue - Downloads Proxy [Write] (Production)
#
# This resource implicitly depends on the 'aws_lambda_function.add-catalogue-downloads-proxy-write-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url
resource "aws_lambda_function_url" "add-catalogue-downloads-proxy-write-production-latest" {
  function_name      = aws_lambda_function.add-catalogue-downloads-proxy-write-production.function_name
  authorization_type = "AWS_IAM"
}
