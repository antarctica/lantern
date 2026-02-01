terraform {
  required_version = "~> 1.0"

  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "18.6.1"
    }
  }
}

provider "gitlab" {
  base_url = "https://gitlab.dev.orb.local/api/v4"
}

resource "gitlab_group" "magic" {
  name             = "MAGIC"
  path             = "magic"
  description      = "Mapping and Geographic Information Centre."
  visibility_level = "internal"
}

resource "gitlab_user" "lantern_bot" {
  username              = "lantern_bot"
  name                  = "Lantern (Bot)"
  email                 = "magicdev@bas.ac.uk"
  note                  = "Bot user for Lantern data catalogue."
  force_random_password = true
  is_external           = true
}

resource "gitlab_project" "lantern_records" {
  name             = "Lantern Records Store"
  path             = "lantern-records"
  namespace_id     = gitlab_group.magic.id
  description      = "Lantern records store."
  visibility_level = "internal"

  # disable everything except repository
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
  merge_requests_access_level          = "disabled"
  model_experiments_access_level       = "disabled"
  model_registry_access_level          = "disabled"
  monitor_access_level                 = "disabled"
  pages_access_level                   = "disabled"
  releases_access_level                = "disabled"
  requirements_access_level            = "disabled"
  security_and_compliance_access_level = "disabled"
  snippets_access_level                = "disabled"
  wiki_access_level                    = "disabled"
}

resource "gitlab_project_membership" "lantern_records_lantern_bot" {
  project      = gitlab_project.lantern_records.id
  user_id      = gitlab_user.lantern_bot.id
  access_level = "maintainer"
}
