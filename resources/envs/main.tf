terraform {
  required_version = "~> 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.27"
    }
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "18.5.0"
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

provider "gitlab" {
  base_url = "https://gitlab.data.bas.ac.uk/api/v4/"
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

### Static site hosting

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

### Workstation module access to static site content

resource "aws_iam_user" "workstation-stage" {
  name = "lantern-workstation-stage"
}
resource "aws_iam_user_policy" "workstation-stage" {
  name = "staging-bucket"
  user = aws_iam_user.workstation-stage.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "MinimalContinuousDeploymentPermissions"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectAcl",
          "s3:PutObjectAcl"
        ]
        Resource = [
          module.site_testing.s3_bucket_arn,
          "${module.site_testing.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user" "workstation-prod" {
  name = "lantern-workstation-prod"
}
resource "aws_iam_user_policy" "workstation-prod" {
  name = "production-bucket"
  user = aws_iam_user.workstation-prod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "MinimalContinuousDeploymentPermissions"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectAcl",
          "s3:PutObjectAcl"
        ]
        Resource = [
          module.site_prod.s3_bucket_arn,
          "${module.site_prod.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

### GitLab store

resource "gitlab_user" "lantern_bot" {
  username          = "bot_magic_lantern"
  name              = "MAGIC Lantern Exp (Bot)"
  email             = "magicdev@bas.ac.uk"
  note              = "Bot user for Lantern data catalogue. Mangaged by IaC via the Lantern project."
  skip_confirmation = true
  is_external       = true
}

resource "gitlab_project" "records_store" {
  name             = "Lantern experiment - records" # "Lantern Records Store"
  path             = "lantern-records-exp"
  namespace_id     = 22 # felnne
  description      = "Records store for Lantern experimental catalogue. Managed by IaC."
  visibility_level = "internal"

  # disable everything except repository and merge-requests
  auto_devops_enabled                  = false
  emails_enabled                       = false
  lfs_enabled                          = false
  packages_enabled                     = false
  initialize_with_readme               = false
  analytics_access_level               = "disabled"
  builds_access_level                  = "disabled"
  container_registry_access_level      = "disabled"
  environments_access_level            = "disabled"
  feature_flags_access_level           = "disabled"
  forking_access_level                 = "disabled"
  infrastructure_access_level          = "disabled"
  issues_access_level                  = "disabled"
  monitor_access_level                 = "disabled"
  pages_access_level                   = "disabled"
  releases_access_level                = "disabled"
  security_and_compliance_access_level = "disabled"
  snippets_access_level                = "disabled"
  wiki_access_level                    = "disabled"
  # model_experiments_access_level     = "disabled"  # not supported in GitLab 15.7
  # model_registry_access_level        = "disabled"  # not supported in GitLab 15.7
  # requirements_access_level          = "disabled"  # not supported in GitLab 15.7
}

resource "gitlab_project_membership" "lantern_records_lantern_bot" {
  # To enable GitLab Store (see /docs/stores.md#gitlab-store)
  project      = gitlab_project.records_store.id
  user_id      = gitlab_user.lantern_bot.id
  access_level = "maintainer"
}

resource "gitlab_project_membership" "magic_helpdesk_lantern_bot" {
  # To enable item enquires via Power Automate (see /docs/site.md#item-enquiries)
  project      = 462 # MAGIC Helpdesk
  user_id      = gitlab_user.lantern_bot.id
  access_level = "reporter"
}
