terraform {
  required_version = "~> 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.27"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "5.15.0"
    }
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "18.5.0"
    }
    onepassword = {
      source = "1Password/onepassword"
    }
    sentry = {
      source  = "jianyuan/sentry"
      version = "0.14.8"
    }
  }

  # Source: https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state
  backend "s3" {
    bucket  = "bas-terraform-remote-state-prod"
    key     = "v2/BAS-LANTERN/terraform.tfstate"
    region  = "eu-west-1"
    encrypt = true
  }
}

variable "pvd_gitlab_pat" {
  type        = string
  description = "GitLab provider personal access token, for an admin user 'api' and 'sudo' scopes."
}

variable "pvd_cloudflare_api_token" {
  type        = string
  description = "Cloudflare provider API token, with edit permissions for Turnstile."
}

variable "pvd_op_account_id" {
  type        = string
  description = "1Password provider account ID to store secrets in."
}

variable "pvd_op_vault_id" {
  type        = string
  description = "1Password provider vault ID to store secrets in."
}

variable "pvd_sentry_api_token" {
  type        = string
  description = "Sentry API token."
}

provider "aws" {
  region = "eu-west-1"
  # credentials set by awscli profile
}

provider "aws" {
  # alias for resources requiring the 'us-east-1' region, which is used as a control region by AWS for some services.
  alias  = "us-east-1"
  region = "us-east-1"
  # credentials set by awscli profile
}

provider "cloudflare" {
  api_token = var.pvd_cloudflare_api_token
}

provider "gitlab" {
  base_url = "https://gitlab.data.bas.ac.uk/api/v4/"
  token    = var.pvd_gitlab_pat
}

provider "onepassword" {
  account = var.pvd_op_account_id
}

provider "sentry" {
  token = var.pvd_sentry_api_token
}

### Static site hosting

data "terraform_remote_state" "BAS-CORE-DOMAINS" {
  # https://gitlab.data.bas.ac.uk/WSF/bas-core-domains
  backend = "s3"

  config = {
    bucket = "bas-terraform-remote-state-prod"
    key    = "v2/BAS-CORE-DOMAINS/terraform.tfstate"
    region = "eu-west-1"
  }
}

variable "static_site_ref" {
  type        = string
  default     = "v0.5.1"
  description = "Static site module version."
}

variable "static_site_tls_version" {
  type = string
  default = "TLSv1.2_2025"
  description = "CloudFront viewer certificate minimum protocol version"
}

variable "static_site_csp" {
  type = string
  default = "default-src * data: 'unsafe-inline'"
  description = "CloudFront content security policy header (CSP)"
}

module "site_stage" {
  source = "git::https://github.com/felnne/tf-aws-static-site.git?ref=${var.static_site_ref}"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  site_name                         = "lantern-testing.data.bas.ac.uk"
  route53_zone_id                   = data.terraform_remote_state.BAS-CORE-DOMAINS.outputs.DATA-BAS-AC-UK-ID
  cloudfront_min_proto_version      = var.static_site_tls_version
  cloudfront_comment                = "Lantern Exp Site (Testing)"
  cloudfront_csp                    = var.static_site_csp
  cloudfront_enable_default_caching = false

  tags = {
    Name         = "lantern-testing"
    X-Project    = "BAS Lantern Experiment"
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
  cloudfront_min_proto_version      = var.static_site_tls_version
  cloudfront_comment                = "Lantern Exp Site (Production)"
  cloudfront_csp                    = var.static_site_csp
  cloudfront_enable_default_caching = true

  tags = {
    Name         = "lantern-prod"
    X-Project    = "BAS Lantern Experiment"
    X-Managed-By = "Terraform"
  }
}
resource "aws_s3_bucket_versioning" "versioning_example" {
  bucket = module.site_prod.s3_bucket_name
  versioning_configuration {
    status = "Enabled"
  }
}

### Workstation module access to static site content

resource "aws_iam_user" "workstation_stage" {
  name = "lantern-workstation-stage"

  tags = {
    X-Project     = "BAS Lantern Experiment"
    X-Managed-By  = "Terraform"
    X-Managed-For = "Ansible"
  }
}
resource "aws_iam_access_key" "workstation_stage" {
  # would ideally be ephemeral https://github.com/hashicorp/terraform-provider-aws/issues/42182
  user = aws_iam_user.workstation_stage.name
}
resource "onepassword_item" "workstation_stage_access_key" {
  vault      = var.pvd_op_vault_id
  category   = "login"
  title      = "SCAR ADD Metadata Toolbox - Workstation AWS IAM S3 access key [Staging]"
  username   = aws_iam_access_key.workstation_stage.id
  password   = aws_iam_access_key.workstation_stage.secret
  note_value = "Used in Ansible to set environment module config for Lantern workstation workflows.\n\nManaged by Terraform in Lantern."
  tags       = ["SCAR ADD Metadata Toolbox"]
}
resource "aws_iam_user_policy" "workstation_stage" {
  name = "staging-bucket"
  user = aws_iam_user.workstation_stage.name

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
          module.site_stage.s3_bucket_arn,
          "${module.site_stage.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user" "workstation_prod" {
  name = "lantern-workstation-prod"

  tags = {
    X-Project     = "BAS Lantern Experiment"
    X-Managed-By  = "Terraform"
    X-Managed-For = "Ansible"
  }
}
resource "aws_iam_access_key" "workstation_prod" {
  # would ideally be ephemeral https://github.com/hashicorp/terraform-provider-aws/issues/42182
  user = aws_iam_user.workstation_prod.name
}
resource "onepassword_item" "workstation_prod_access_key" {
  vault      = var.pvd_op_vault_id
  category   = "login"
  title      = "SCAR ADD Metadata Toolbox - Workstation AWS IAM S3 access key [Production]"
  username   = aws_iam_access_key.workstation_prod.id
  password   = aws_iam_access_key.workstation_prod.secret
  note_value = "Used in Ansible to set environment module config for Lantern workstation workflows.\n\nManaged by Terraform in Lantern."
  tags       = ["SCAR ADD Metadata Toolbox"]
}
resource "aws_iam_user_policy" "workstation_prod" {
  name = "production-bucket"
  user = aws_iam_user.workstation_prod.name

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

resource "gitlab_personal_access_token" "lantern_bot_pa_item_enquires" {
  # To enable item enquires via Power Automate (see /docs/site.md#item-enquiries)
  user_id    = gitlab_user.lantern_bot.id
  name       = "pa-item-enquires"
  expires_at = "2026-07-09"
  scopes     = ["api"]
}
resource "onepassword_item" "lantern_bot_pa_item_enquires_token" {
  vault      = var.pvd_op_vault_id
  category   = "password"
  title      = "SCAR ADD Metadata Toolbox - Item enquires GitLab bot PAT"
  password   = gitlab_personal_access_token.lantern_bot_pa_item_enquires.token
  note_value = "Used in Power Automate flow to create issues in the Helpdesk GitLab project for item enquires.\n\nManaged by Terraform in Lantern."
  tags       = ["SCAR ADD Metadata Toolbox"]
}

resource "gitlab_personal_access_token" "lantern_bot_ansible_workstation_module" {
  # To enable publishing workflows via Ansible managed workstation module (see /docs/usage.md)
  user_id    = gitlab_user.lantern_bot.id
  name       = "ansible-workstation-module"
  expires_at = "2026-07-09"
  scopes     = ["api"]
}
resource "onepassword_item" "lantern_bot_ansible_workstation_module_token" {
  vault      = var.pvd_op_vault_id
  category   = "password"
  title      = "SCAR ADD Metadata Toolbox - Ansible workstation module GitLab bot PAT"
  password   = gitlab_personal_access_token.lantern_bot_ansible_workstation_module.token
  note_value = "Used in Ansible vaults to include in environment module deployed to workstations for record workflows.\n\nManaged by Terraform in Lantern."
  tags       = ["SCAR ADD Metadata Toolbox"]
}

resource "gitlab_project" "records_store" {
  name             = "Lantern experiment - records" # "Lantern Records Store"
  path             = "lantern-records-exp"
  namespace_id     = 22 # felnne
  description      = "Records store for Lantern experimental catalogue. This project is managed using Infrastructure as Code."
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
  # and interactive publishing workflow (see /docs/usage.md#interactive-record-publishing-workflow)
  project      = 462 # MAGIC Helpdesk
  user_id      = gitlab_user.lantern_bot.id
  access_level = "reporter"
}

resource "gitlab_project_membership" "magic_data_management_lantern_bot" {
  # To enable interactive publishing workflow (see /docs/usage.md#interactive-record-publishing-workflow)
  project      = 667 # MAGIC data management
  user_id      = gitlab_user.lantern_bot.id
  access_level = "reporter"
}

resource "gitlab_project_membership" "magic_mapping_coordination_lantern_bot" {
  # To enable interactive publishing workflow (see /docs/usage.md#interactive-record-publishing-workflow)
  project      = 1254 # MAGIC mapping coordination
  user_id      = gitlab_user.lantern_bot.id
  access_level = "reporter"
}

# Turnstile bot protection

variable "cloudflare_account_id" {
  type        = string
  description = "Cloudflare account identifier."
}

resource "cloudflare_turnstile_widget" "site" {
  # To enable bot protection on item enquires (see /docs/site.md#bot-protection)
  account_id = var.cloudflare_account_id
  domains = sort([
    module.site_stage.s3_bucket_name,
    module.site_prod.s3_bucket_name,
    "data-testing.data.bas.ac.uk",
    "data.bas.ac.uk"
  ])
  mode            = "managed"
  name            = "Lantern Item Enquires"
  bot_fight_mode  = false
  ephemeral_id    = false
  offlabel        = false
  clearance_level = "no_clearance"
  region          = "world"
}
resource "onepassword_item" "turnstile_site_secret_key" {
  vault      = var.pvd_op_vault_id
  category   = "login"
  title      = "SCAR ADD Metadata Toolbox - Cloudflare Turnstile Captcha"
  username   = cloudflare_turnstile_widget.site.sitekey
  password   = cloudflare_turnstile_widget.site.secret
  note_value = "Used in Ansible and local env to set config option.\n\nManaged by Terraform in Lantern."
  tags       = ["SCAR ADD Metadata Toolbox"]
}

# Sentry monitoring

variable "sentry_org" {
  type        = string
  description = "Sentry organisation slug."
  default     = "antarctica"
}

resource "sentry_project" "lantern" {
  organization = var.sentry_org
  teams        = ["magic"]
  name         = "Lantern (Data Catalogue)"
  slug         = "lantern"
  platform     = "python"
}

data "sentry_key" "lantern_dsn" {
  organization = var.sentry_org
  project      = sentry_project.lantern.slug
  first        = true # to select default key
}
output "sentry_dsn" {
  # (public) DSNs are not sensitive in newer Sentry versions
  value       = nonsensitive(data.sentry_key.lantern_dsn.dsn.public)
  description = "Sentry DSN."
}
