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
# Terraform source: https://registry.terraform.io/providers/hashicorp/azuread/latest/docs/resources/application
resource "azuread_application" "add-repository" {
  display_name = "SCAR ADD Metadata Toolbox (Catalogue)"
  identifier_uris = [
    # set once the initial application registration has been made and Application ID has been assigned
    "api://8bfe65d3-9509-4b0a-acd2-8ce8cdc0c01e"
  ]
  owners = [
    # Felix Fennell (Admin) [o365felnne@bas.ac.uk]
    "7aa5b9f2-25c1-4a88-8627-c0d7d1326b55"
  ]
  marketing_url                  = "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox"
  sign_in_audience               = "AzureADMyOrg"
  group_membership_claims        = ["None"]
  fallback_public_client_enabled = false
  prevent_duplicate_names        = true

  feature_tags {
    hide = false
  }

  api {
    requested_access_token_version = 2

    oauth2_permission_scope {
      admin_consent_description  = "Allow access to the SCAR ADD Data Catalogue."
      admin_consent_display_name = "SCAR ADD Data Catalogue Access"
      id                         = "096645b9-0cdd-4f47-978d-ab46b8e60549"
      enabled                    = true
      type                       = "Admin"
      value                      = "BAS.MAGIC.ADD.Access"
    }
  }

  app_role {
    allowed_member_types = [
      "User"
    ]
    description  = "Publish all SCAR ADD Data Catalogue metadata records."
    display_name = "BAS.MAGIC.ADD.Records.Publish.All"
    enabled      = true
    id           = "526ec886-e932-4578-9a87-90fa6f35e664"
    value        = "BAS.MAGIC.ADD.Records.Publish.All"
  }

  app_role {
    allowed_member_types = [
      "User"
    ]
    description  = "Change all SCAR ADD Data Catalogue metadata records."
    display_name = "BAS.MAGIC.ADD.Records.ReadWrite.All"
    enabled      = true
    id           = "7acdf1f0-20e4-43be-a489-09407959e888"
    value        = "BAS.MAGIC.ADD.Records.ReadWrite.All"
  }

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
}

# SCAR ADD Metadata Toolbox (client)
#
# This resource implicitly depends on the 'azuread_application.add-repository' resource
# This resource relies on the Azure Active Directory Terraform provider being previously configured
#
# Azure source: https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-how-applications-are-added
# Terraform source: https://www.terraform.io/docs/providers/azuread/r/application.html
resource "azuread_application" "add-editor" {
  display_name = "SCAR ADD Metadata Toolbox (Editor)"
  owners = [
    # Felix Fennell (Admin) [o365felnne@bas.ac.uk]
    "7aa5b9f2-25c1-4a88-8627-c0d7d1326b55"
  ]
  marketing_url                  = "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox"
  sign_in_audience               = "AzureADMyOrg"
  group_membership_claims        = ["None"]
  fallback_public_client_enabled = true
  prevent_duplicate_names        = true

  feature_tags {
    hide = false
  }

  api {
    requested_access_token_version = 2
  }

  public_client {
    redirect_uris = [
      "https://login.microsoftonline.com/common/oauth2/nativeclient"
    ]
  }

  required_resource_access {
    resource_app_id = azuread_application.add-repository.application_id

    resource_access {
      id   = "096645b9-0cdd-4f47-978d-ab46b8e60549" # BAS.MAGIC.ADD.Access
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
# Terraform source: https://registry.terraform.io/providers/hashicorp/azuread/latest/docs/resources/service_principal
resource "azuread_service_principal" "add-repository" {
  application_id               = azuread_application.add-repository.application_id
  app_role_assignment_required = false
  owners = [
    # Felix Fennell (Admin) [o365felnne@bas.ac.uk]
    "7aa5b9f2-25c1-4a88-8627-c0d7d1326b55",
    # Laura Gerrish [lauger@bas.ac.uk]
    "cdee342c-3935-41dd-967c-241547d61c9d",
    # Louise Ireland [louela@bas.ac.ul]
    "b1d03922-60d6-46e5-ba74-e79f41a54103"
  ]
}
