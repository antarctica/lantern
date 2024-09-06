#
# This file is used to define TLS Server Certificates used by various AWS resources

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Certificates
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# add-catalogue-integration.data.bas.ac.uk
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-integration' resource
# This resource relies on the AWS Terraform provider ('us-east-1' alias) being previously configured
#
# AWS source: http://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate
resource "aws_acm_certificate" "add-catalogue-integration" {
  provider = aws.us-east-1

  domain_name       = aws_s3_bucket.add-catalogue-integration.bucket
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name         = "add-catalogue-integration.data.bas.ac.uk"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

# add-catalogue.data.bas.ac.uk
#
# This resource implicitly depends on the 'aws_s3_bucket.add-catalogue-production' resource
# This resource relies on the AWS Terraform provider ('us-east-1' alias) being previously configured
#
# AWS source: http://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html
# Terraform source: https://www.terraform.io/docs/providers/aws/r/acm_certificate.html
resource "aws_acm_certificate" "add-catalogue-production" {
  provider = aws.us-east-1

  domain_name       = aws_s3_bucket.add-catalogue-production.bucket
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name         = "add-catalogue.data.bas.ac.uk"
    X-Project    = "ADD Data Catalogue"
    X-Managed-By = "Terraform"
  }
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Certificate validation records (Route53)
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# add-catalogue-integration.data.bas.ac.uk
#
# This resource implicitly depends on the 'aws_acm_certificate.add-catalogue-integration' resource
# This resource explicitly depends on outputs from the the 'terraform_remote_state.BAS-CORE-DOMAINS' data source
# This resource relies on the AWS Terraform provider being previously configured
#
# AWS source: http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/rrsets-working-with.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record
#
# Tags are not supported by this resource
//noinspection HILUnresolvedReference
resource "aws_route53_record" "add-catalogue-integration-cert" {
  for_each = {
    for dvo in aws_acm_certificate.add-catalogue-integration.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.terraform_remote_state.BAS-CORE-DOMAINS.outputs.DATA-BAS-AC-UK-ID
}

# add-catalogue.data.bas.ac.uk
#
# This resource implicitly depends on the 'aws_acm_certificate.add-catalogue-production' resource
# This resource explicitly depends on outputs from the the 'terraform_remote_state.BAS-CORE-DOMAINS' data source
# This resource relies on the AWS Terraform provider being previously configured
#
# AWS source: http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/rrsets-working-with.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record
#
# Tags are not supported by this resource
//noinspection HILUnresolvedReference
resource "aws_route53_record" "add-catalogue-production-cert" {
  for_each = {
    for dvo in aws_acm_certificate.add-catalogue-production.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.terraform_remote_state.BAS-CORE-DOMAINS.outputs.DATA-BAS-AC-UK-ID
}

#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *
#
# Certificate validations
#
#    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *    *

# add-catalogue-integration.data.bas.ac.uk
#
# This resource may take a significant time (~30m) to create whilst domain validation is completed
#
# This resource implicitly depends on the 'aws_acm_certificate.add-catalogue-integration' resource
# This resource implicitly depends on the 'aws_route53_record.add-catalogue-integration-cert' resource
# This resource relies on the AWS Terraform provider ('us-east-1' alias) being previously configured
#
# AWS source: https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-validate-dns.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation
#
# Tags are not supported by this resource
resource "aws_acm_certificate_validation" "add-catalogue-integration" {
  provider = aws.us-east-1

  certificate_arn         = aws_acm_certificate.add-catalogue-integration.arn
  validation_record_fqdns = [for record in aws_route53_record.add-catalogue-integration-cert : record.fqdn]
}

# add-catalogue.data.bas.ac.uk
#
# This resource may take a significant time (~30m) to create whilst domain validation is completed
#
# This resource implicitly depends on the 'aws_acm_certificate.add-catalogue-production' resource
# This resource implicitly depends on the 'aws_route53_record.add-catalogue-production-cert' resource
# This resource relies on the AWS Terraform provider ('us-east-1' alias) being previously configured
#
# AWS source: https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-validate-dns.html
# Terraform source: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation
#
# Tags are not supported by this resource
resource "aws_acm_certificate_validation" "add-catalogue-production" {
  provider = aws.us-east-1

  certificate_arn         = aws_acm_certificate.add-catalogue-production.arn
  validation_record_fqdns = [for record in aws_route53_record.add-catalogue-production-cert : record.fqdn]
}
