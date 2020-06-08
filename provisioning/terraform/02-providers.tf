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


# Azure Active Directory provider
#
# The BAS preferred identity management provider
#
# See https://www.terraform.io/docs/providers/azuread/guides/azure_cli.html for how to configure credentials to use
# this provider using the Azure CLI.
#
# AWS source: https://azure.microsoft.com/en-us/services/active-directory/
# Terraform source: https://www.terraform.io/docs/providers/azuread/index.html
provider "azuread" {
  version = "=0.10.0"

  # NERC Production AD
  #
  # Tenancy used as subscription as per [1]
  # [1] https://github.com/terraform-providers/terraform-provider-azuread/issues/259#issuecomment-636387231
  subscription_id = "b311db95-32ad-438f-a101-7ba061712a4e"
  tenant_id       = "b311db95-32ad-438f-a101-7ba061712a4e"
}
