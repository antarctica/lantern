#
# This file is used to define bot users in the BAS GitLab instance

## ADD Data Catalogue Records Tracking bot user - Password
##
## Password tracked in Terraform remote state (and so not exposed).
##
## Terraform source: https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password
resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

## ADD Data Catalogue Records Tracking bot user
##
## GitLab user resources require either a password or password_reset option so a random password is generated and used.
## This password is never used, instead Personal Access Tokens are created manually for use in applications.
##
# This resource implicitly depends on the 'random_password.password' resource.
## This resource relies on the GitLab Terraform provider being previously configured.
##
## GitLab source: https://docs.gitlab.com/ee/api/users.html#user-creation
## Terraform source: https://registry.terraform.io/providers/gitlabhq/gitlab/latest/docs/resources/user
resource "gitlab_user" "add-catalogue-records-tracking-bot" {
  name     = "SCAR ADD Metadata Toolbox - Records Tracking (Bot)"
  username = "bot-add-catalogue-records-tracking"
  email    = "magic+add-cat-rec-trac@bas.ac.uk"
  password = random_password.password.result

  state = "active"
  note  = "Bot user for the CSW records revision tracking feature in the SCAR ADD Metadata Toolbox. Managed using Terraform."

  can_create_group  = false
  is_admin          = false
  is_external       = false
  projects_limit    = 0
  skip_confirmation = true
}
