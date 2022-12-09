#
# This file is used to define Git repos managed through the BAS GitLab instance

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Projects
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

## ADD Data Catalogue CSW Records Repo (Integration)
##
## This resource relies on the GitLab Terraform provider being previously configured.
##
## GitLab source: https://docs.gitlab.com/ee/user/project/
## Terraform source: https://registry.terraform.io/providers/gitlabhq/gitlab/latest/docs/resources/project
resource "gitlab_project" "add-catalogue-records-integration" {
  namespace_id = 31 # MAGIC
  path         = "add-catalogue-records-integration"
  name         = "SCAR ADD Metadata Toolbox Metadata Records - Integration"
  description  = "Metadata records held in the ADD Data Catalogue Unpublished CSW (Integration Environment)"

  default_branch         = "main"
  visibility_level       = "private"
  initialize_with_readme = false

  analytics_access_level               = "disabled"
  builds_access_level                  = "disabled"
  container_registry_access_level      = "disabled"
  forking_access_level                 = "disabled"
  issues_access_level                  = "disabled"
  merge_requests_access_level          = "disabled"
  operations_access_level              = "disabled"
  pages_access_level                   = "disabled"
  repository_access_level              = "enabled"
  requirements_access_level            = "disabled"
  security_and_compliance_access_level = "disabled" # buggy - needs to be manually disabled
  snippets_access_level                = "disabled"
  wiki_access_level                    = "disabled"

  container_registry_enabled = false
  issues_enabled             = false
  lfs_enabled                = false
  merge_pipelines_enabled    = false
  merge_requests_enabled     = false
  packages_enabled           = false
  snippets_enabled           = false
  wiki_enabled               = false
}

## ADD Data Catalogue CSW Records Repo (Production)
##
## This resource relies on the GitLab Terraform provider being previously configured.
##
## GitLab source: https://docs.gitlab.com/ee/user/project/
## Terraform source: https://registry.terraform.io/providers/gitlabhq/gitlab/latest/docs/resources/project
resource "gitlab_project" "add-catalogue-records-production" {
  namespace_id = 31 # MAGIC
  path         = "add-catalogue-records-production"
  name         = "SCAR ADD Metadata Toolbox Metadata Records - Production"
  description  = "Metadata records held in the ADD Data Catalogue Unpublished CSW (Production Environment)"

  default_branch         = "main"
  visibility_level       = "private"
  initialize_with_readme = false

  analytics_access_level               = "disabled"
  builds_access_level                  = "disabled"
  container_registry_access_level      = "disabled"
  forking_access_level                 = "disabled"
  issues_access_level                  = "disabled"
  merge_requests_access_level          = "disabled"
  operations_access_level              = "disabled"
  pages_access_level                   = "disabled"
  repository_access_level              = "enabled"
  requirements_access_level            = "disabled"
  security_and_compliance_access_level = "disabled" # buggy - needs to be manually disabled
  snippets_access_level                = "disabled"
  wiki_access_level                    = "disabled"

  container_registry_enabled = false
  issues_enabled             = false
  lfs_enabled                = false
  merge_pipelines_enabled    = false
  merge_requests_enabled     = false
  packages_enabled           = false
  snippets_enabled           = false
  wiki_enabled               = false
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Project Memberships
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

## ADD Data Catalogue CSW Records Repo (Integration) - ADD Data Catalogue Records Tracking bot user
##
## This resource implicitly depends on the 'gitlab_user.add-catalogue-records-tracking-bot' resource.
## This resource implicitly depends on the 'gitlab_project.add-catalogue-records-integration' resource.
## This resource relies on the GitLab Terraform provider being previously configured.
##
## GitLab source: https://docs.gitlab.com/ee/user/permissions.html
## Terraform source: https://registry.terraform.io/providers/gitlabhq/gitlab/latest/docs/resources/project_membership
resource "gitlab_project_membership" "add_tracking_bot_add_tracking_integration" {
  project_id   = gitlab_project.add-catalogue-records-integration.id
  user_id      = gitlab_user.add-catalogue-records-tracking-bot.id
  access_level = "developer"
}

## ADD Data Catalogue CSW Records Repo (Production) - ADD Data Catalogue Records Tracking bot user
##
## This resource implicitly depends on the 'gitlab_user.add-catalogue-records-tracking-bot' resource.
## This resource implicitly depends on the 'gitlab_project.add-catalogue-records-production' resource.
## This resource relies on the GitLab Terraform provider being previously configured.
##
## GitLab source: https://docs.gitlab.com/ee/user/permissions.html
## Terraform source: https://registry.terraform.io/providers/gitlabhq/gitlab/latest/docs/resources/project_membership
resource "gitlab_project_membership" "add_tracking_bot_add_tracking_production" {
  project_id   = gitlab_project.add-catalogue-records-production.id
  user_id      = gitlab_user.add-catalogue-records-tracking-bot.id
  access_level = "developer"
}
