terraform {
  required_version = "~> 0.12"
}

variable "registry_image" {
  type = string
  description = "Application Docker image, e.g. https://registry.example.com/namespace/image:tag"
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

# Terraform source: https://www.terraform.io/docs/providers/local/r/file.html
resource "local_file" "container-wrapper" {
  content = templatefile("scar-add-metadata-toolbox.tmpl", {
    registry_image = var.registry_image
  })
  filename = "scar-add-metadata-toolbox"
}

# Terraform source: https://www.terraform.io/docs/providers/local/r/file.html
resource "local_file" "dot-env" {
  content = templatefile("dot.env.tmpl", {
    app_csw_connection_string_published = var.app_csw_connection_string_published
    app_csw_connection_string_unpublished = var.app_csw_connection_string_unpublished
    app_s3_static_site_bucket = var.app_s3_static_site_bucket
  })
  filename = "dot.env"
}
