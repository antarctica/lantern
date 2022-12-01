#
# This file is used to define Terraform provider resources

# AWS provider
#
# The BAS preferred public cloud provider.
#
# See https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration for how to
# configure credentials to use this provider.
#
# AWS source: https://aws.amazon.com/
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws
provider "aws" {
  region = "eu-west-1"
}

# AWS provider - alias
#
# This alias is used for resources or data-sources that require the 'us-east-1' region, which is used as a control
# region by AWS for some services.
#
# See 'AWS' provider section for provider links.
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}


# Azure Active Directory provider
#
# The BAS preferred identity management provider
#
# See https://registry.terraform.io/providers/hashicorp/azuread/latest/docs#authenticating-to-azure-active-directory
# for how to configure credentials to use this provider using the Azure CLI.
#
# AWS source: https://azure.microsoft.com/en-us/services/active-directory/
# Terraform source: https://registry.terraform.io/providers/hashicorp/azuread/latest/docs
provider "azuread" {
  # NERC Production AD
  tenant_id = "b311db95-32ad-438f-a101-7ba061712a4e"
}
