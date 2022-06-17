#
# This file is used to define IAM roles to which permissions can be assigned to other AWS services

# ADD Data Catalogue - Downloads Proxy (Staging)
#
# Allows AWS Lambda functions to log to AWS CloudWatch and access relevant S3 resources.
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-downloads-proxy-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
resource "aws_iam_role" "add-catalogue-downloads-proxy-staging" {
  name        = "BAS-ADD-Catalogue-Downloads-Proxy-Function-Staging"
  description = "Allows Lambda to log to AWS CloudWatch and read from S3"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  inline_policy {
    name = "ADD_Data_Catalogue_Downloads_Proxy_Stage"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "s3:GetObject",
            "s3:PutObject"
          ]
          Resource = ["${aws_s3_bucket.add-catalogue-downloads-proxy-staging.arn}/*"]
          Effect   = "Allow"
          Sid      = "S3"
        },
        {
          Action = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
          Resource = ["arn:aws:logs:*:178449599525:*"]
          Effect   = "Allow"
          Sid      = "CloudWatch"
        }
      ]
    })
  }

  tags = {
    Name         = "add-catalogue-downloads-proxy-stage"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

# ADD Data Catalogue - Downloads Proxy (Production)
#
# Allows AWS Lambda functions to log to AWS CloudWatch and access relevant S3 resources.
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-downloads-proxy-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
resource "aws_iam_role" "add-catalogue-downloads-proxy-production" {
  name        = "BAS-ADD-Catalogue-Downloads-Proxy-Function-Production"
  description = "Allows Lambda to log to AWS CloudWatch and read from S3"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  inline_policy {
    name = "ADD_Data_Catalogue_Downloads_Proxy_Prod"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "s3:GetObject",
            "s3:PutObject"
          ]
          Resource = ["${aws_s3_bucket.add-catalogue-downloads-proxy-production.arn}/*"]
          Effect   = "Allow"
          Sid      = "S3"
        },
        {
          Action = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
          Resource = ["arn:aws:logs:*:178449599525:*"]
          Effect   = "Allow"
          Sid      = "CloudWatch"
        }
      ]
    })
  }

  tags = {
    Name         = "add-catalogue-downloads-proxy-prod"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}
