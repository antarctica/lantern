#
# This file is used to define Terraform provider resources

# AWS provider
#
# The BAS preferred public cloud provider.
#
# See https://www.terraform.io/docs/providers/aws/index.html#authentication for how to
# configure credentials to use this provider.
#
# AWS source: https://aws.amazon.com/
# Terraform source: https://www.terraform.io/docs/providers/aws/index.html
provider "aws" {
  version = "~> 2.65"

  region = "eu-west-1"
}

# AWS provider - alias
#
# This alias is used for resources or data-sources that require the 'us-east-1' region, which is used as a control
# region by AWS for some services
#
# See https://www.terraform.io/docs/providers/aws/index.html#authentication for how to
# configure credentials to use this provider.
#
# AWS source: https://aws.amazon.com/
# Terraform source: https://www.terraform.io/docs/providers/aws/index.html
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}
