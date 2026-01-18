terraform {
  required_version = "~> 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.27"
    }
  }

  # Source: https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state
  backend "s3" {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-LANTERN/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = "eu-west-1"
}

# Alias for resources that require the 'us-east-1' region, which is used as a control region by AWS for some services.
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}

# Source: https://gitlab.data.bas.ac.uk/WSF/bas-core-domains
data "terraform_remote_state" "BAS-CORE-DOMAINS" {
  backend = "s3"

  config = {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-CORE-DOMAINS/terraform.tfstate"
    region = "eu-west-1"
  }
}

variable "static_site_ref" {
  type        = string
  default     = "v0.4.0"
  description = "Static site module version."
}

module "site_testing" {
  source = "git::https://github.com/felnne/tf-aws-static-site.git?ref=${var.static_site_ref}"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  site_name                         = "lantern-testing.data.bas.ac.uk"
  route53_zone_id                   = data.terraform_remote_state.BAS-CORE-DOMAINS.outputs.DATA-BAS-AC-UK-ID
  cloudfront_comment                = "Lantern Exp Site (Testing)"
  cloudfront_csp                    = "default-src * data: 'unsafe-inline'"
  cloudfront_enable_default_caching = false

  tags = {
    Name         = "lantern-testing"
    X-Project    = "BAS Lanern Experiment"
    X-Managed-By = "Terraform"
  }
}

module "site_prod" {
  source = "git::https://github.com/felnne/tf-aws-static-site.git?ref=${var.static_site_ref}"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  site_name                         = "lantern.data.bas.ac.uk"
  route53_zone_id                   = data.terraform_remote_state.BAS-CORE-DOMAINS.outputs.DATA-BAS-AC-UK-ID
  cloudfront_comment                = "Lantern Exp Site (Production)"
  cloudfront_csp                    = "default-src * data: 'unsafe-inline'"
  cloudfront_enable_default_caching = true

  tags = {
    Name         = "lantern-prod"
    X-Project    = "BAS Lanern Experiment"
    X-Managed-By = "Terraform"
  }
}
