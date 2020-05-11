#
# This file is used to define Terraform remote state resources

# These resources import the remote state of another project, typically for using their outputs

# The BAS-AWS remote state 
#
# Includes outputs such as VPC subnet identifiers.
#
# Source: https://gitlab.data.bas.ac.uk/WSF/bas-aws
# Terraform source: https://www.terraform.io/docs/providers/terraform/r/remote_state.html
data "terraform_remote_state" "BAS-AWS" {
  backend = "s3"

  config {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-AWS/terraform.tfstate"
    region = "eu-west-1"
  }
}

# The BAS-CORE-DOMAINS remote state 
#
# Includes outputs such as DNS zone identifiers.
#
# Source: https://gitlab.data.bas.ac.uk/WSF/bas-core-domains
# Terraform source: https://www.terraform.io/docs/providers/terraform/r/remote_state.html
data "terraform_remote_state" "BAS-CORE-DOMAINS" {
  backend = "s3"

  config {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-CORE-DOMAINS/terraform.tfstate"
    region = "eu-west-1"
  }
}
