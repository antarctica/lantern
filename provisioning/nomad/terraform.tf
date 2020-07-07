terraform {
  required_version = "~> 0.12"
}

variable "registry_image" {
  type = string
  description = "Application Docker image, e.g. https://registry.example.com/namespace/image:tag"
}

variable "registry_token" {
  type = string
  description = "Authentication token for accessing the registry referred by var.registry_image"
}

variable "app_csw_connection_string_published" {
  type = string
  description = "Connection string for the published CSW server backing database"
}

variable "app_csw_connection_string_unpublished" {
  type = string
  description = "Connection string for the unpublished CSW server backing database"
}

variable "app_s3_static_site_bucket" {
  type = string
  description = "Name of S3 bucket used for static site"
}

# Terraform source: https://www.terraform.io/docs/providers/nomad/index.html
provider "nomad" {
  address = "http://bsl-nomad-magic-dev-s3.nerc-bas.ac.uk:4646"
  region  = "bas"
}

# Terraform source: https://www.terraform.io/docs/providers/nomad/r/job.html
resource "nomad_job" "app" {
  jobspec = templatefile("scar-add-metadata-toolbox.hcl.tmpl", {
    registry_image = var.registry_image
    registry_token = var.registry_token
    app_csw_connection_string_published = var.app_csw_connection_string_published
    app_csw_connection_string_unpublished = var.app_csw_connection_string_unpublished
    app_s3_static_site_bucket = var.app_s3_static_site_bucket
  })
}
