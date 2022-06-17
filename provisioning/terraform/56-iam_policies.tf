#
# This file is used to define and assign IAM policies definining sets of permissions or restrictions to resources
# Policies can be applied to combinations of users, roles and groups as required

# ADD Data Catalogue - Downloads Proxy [Write] (Staging)
#
# Customer Managed Policy
#
# Allows principles to execute the specified Lambda function
#
# This resource implicitly depends on the 'aws_lambda_function.add-catalogue-downloads-proxy-write-staging' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html#urls-auth-iam
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy
#
# Tags are not supported by this resource
resource "aws_iam_policy" "add-catalogue-downloads-proxy-write-staging" {
  name        = "BAS-ADD-Catalogue-Downloads-Proxy-Function-Write-Staging"
  description = "Allows access to call ADD Downloads Proxy staging function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["lambda:InvokeFunctionUrl"]
        Resource = [aws_lambda_function.add-catalogue-downloads-proxy-write-staging.arn]
        Effect   = "Allow"
        Sid      = "Lambda"
      }
    ]
  })

  tags = {
    Name         = "add-catalogue-downloads-proxy-write-stage"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

# ADD Data Catalogue - Downloads Proxy [Write] (Production)
#
# Customer Managed Policy
#
# Allows principles to execute the specified Lambda function
#
# This resource implicitly depends on the 'aws_lambda_function.add-catalogue-downloads-proxy-write-production' resource
# This resource relies on the AWS Terraform provider being previously configured.
#
# AWS source: https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html#urls-auth-iam
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy
#
# Tags are not supported by this resource
resource "aws_iam_policy" "add-catalogue-downloads-proxy-write-production" {
  name        = "BAS-ADD-Catalogue-Downloads-Proxy-Function-Write-Production"
  description = "Allows access to call ADD Downloads Proxy production function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["lambda:InvokeFunctionUrl"]
        Resource = [aws_lambda_function.add-catalogue-downloads-proxy-write-production.arn]
        Effect   = "Allow"
        Sid      = "Lambda"
      }
    ]
  })

  tags = {
    Name         = "add-catalogue-downloads-proxy-write-prod"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}
