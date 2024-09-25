#
# This file is used to define Terraform core resources

terraform {
  # Required Terraform version
  #
  # Ensures the Terraform version used is compatible with this configuration.
  #
  # Source: https://www.terraform.io/language/settings#specifying-a-required-terraform-version
  required_version = "~> 1.0"

  # Required Terraform provider versions
  #
  # Terraform providers are versioned and distributed independently from Terraform itself.
  #
  # A registry maintains an index of 1st and vetted 3rd party providers. The `terraform init` command the latest
  # version of each provider required here, subject to version constraints.
  #
  # Source: https://www.terraform.io/language/settings#specifying-provider-requirements
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.18"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.23"
    }

    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "3.20.0"
    }
  }

  # AWS S3 Remote state backend
  #
  # Implements a Terraform backend for storing state remotely so it can be used elsewhere.
  #
  # This backend is configured to use the common BAS Terraform Remote State project.
  #
  # This resource relies on the AWS Terraform provider being previously configured.
  #
  # Source: https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state
  # Terraform source: https://www.terraform.io/language/settings/backends/s3
  backend "s3" {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-ADD-DATA-CATALOGUE/terraform.tfstate"
    region = "eu-west-1"
  }
}
