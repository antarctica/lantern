#
# This file is used to define Azure Application Registrations for protecting and providing access to external resources

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Application Registrations
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# SCAR ADD Metadata Toolbox (server)
#
# This resource relies on the Azure Active Directory Terraform provider being previously configured
#
# Azure source: https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-how-applications-are-added
# Terraform source: https://www.terraform.io/docs/providers/azuread/r/application.html
resource "azuread_application" "add-repository" {
  name                       = "SCAR ADD Metadata Toolbox (Catalogue)"
  type                       = "webapp/api"
  owners                     = ["7aa5b9f2-25c1-4a88-8627-c0d7d1326b55"]
  public_client              = false
  available_to_other_tenants = false
  homepage                   = "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox"

  # set once the initial application registration has been made and Application ID has been assigned
  identifier_uris = ["api://8bfe65d3-9509-4b0a-acd2-8ce8cdc0c01e"]

  oauth2_allow_implicit_flow = false
  group_membership_claims    = "None"

  optional_claims {
    access_token {
      name = "email"
    }
    access_token {
      name = "family_name"
    }
    access_token {
      name = "given_name"
    }
  }

  app_role {
    allowed_member_types = [
      "User"
    ]
    description  = "Publish all SCAR ADD Data Catalogue metadata records."
    display_name = "BAS.MAGIC.ADD.Records.Publish.All"
    is_enabled   = true
    value        = "BAS.MAGIC.ADD.Records.Publish.All"
  }
  app_role {
    allowed_member_types = [
      "User"
    ]
    description  = "Change all SCAR ADD Data Catalogue metadata records."
    display_name = "BAS.MAGIC.ADD.Records.ReadWrite.All"
    is_enabled   = true
    value        = "BAS.MAGIC.ADD.Records.ReadWrite.All"
  }

  oauth2_permissions {
    admin_consent_description  = "Allow access to the SCAR ADD Data Catalogue."
    admin_consent_display_name = "SCAR ADD Data Catalogue Access"
    is_enabled                 = true
    type                       = "Admin"
    value                      = "BAS.MAGIC.ADD.Access"
  }
}

# SCAR ADD Metadata Toolbox (client)
#
# This resource implicitly depends on the 'azuread_application.add-repository' resource
# This resource relies on the Azure Active Directory Terraform provider being previously configured
#
# Azure source: https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-how-applications-are-added
# Terraform source: https://www.terraform.io/docs/providers/azuread/r/application.html
resource "azuread_application" "add-editor" {
  name                       = "SCAR ADD Metadata Toolbox (Editor)"
  type                       = "native"
  owners                     = ["7aa5b9f2-25c1-4a88-8627-c0d7d1326b55"]
  public_client              = true
  available_to_other_tenants = false
  homepage                   = "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox"

  reply_urls                 = ["https://login.microsoftonline.com/common/oauth2/nativeclient"]
  oauth2_allow_implicit_flow = false
  group_membership_claims    = "None"
  oauth2_permissions         = []

  required_resource_access {
    resource_app_id = azuread_application.add-repository.application_id

    resource_access {
      id   = "096645b9-0cdd-4f47-978d-ab46b8e60549"
      type = "Scope"
    }
  }
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Service Principles (Enterprise applications)
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# SCAR ADD Metadata Toolbox (server)
#
# This resource implicitly depends on the 'azuread_application.add-repository' resource
# This resource relies on the Azure Active Directory Terraform provider being previously configured
#
# Azure source: https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-how-applications-are-added
# Terraform source: https://www.terraform.io/docs/providers/azuread/r/service_principal.html
resource "azuread_service_principal" "add-repository" {
  application_id               = azuread_application.add-repository.application_id
  app_role_assignment_required = false
}
